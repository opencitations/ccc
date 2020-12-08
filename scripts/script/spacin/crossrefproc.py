#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2016, Silvio Peroni <essepuntato@gmail.com>
#
# Permission to use, copy, modify, and/or distribute this software for any purpose
# with or without fee is hereby granted, provided that the above copyright notice
# and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT,
# OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE,
# DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS
# SOFTWARE.

__author__ = 'essepuntato, Gabriele Pisciotta'

from rdflib.term import Node, URIRef, Genid
from script.support.queryinterface import LocalQuery, RemoteQuery
from script.support.support import dict_get as dg
from script.support.support import encode_url
from script.spacin.formatproc import FormatProcessor
from script.ocdm.crossrefdatahandler import CrossrefDataHandler
from script.ocdm.graphlib import GraphEntity
from script.ccc.jats2oc import Jats2OC as jt
import threading, queue
from script.spacin.bibentry import Bibentry
import time


def run_in_thread(fn):
    def run(*k, **kw):
        t = threading.Thread(target=fn, args=k, kwargs=kw)
        t.start()
        return t
    return run


bibentries = queue.Queue()


@run_in_thread
def create_bibentry(full_entry, bibentries, repok, reperr, query_interface, rf, get_bib_entry_doi, message, process_existing_by_id):
    bibentries.put(Bibentry(full_entry, repok, reperr, query_interface, rf, get_bib_entry_doi, message, process_existing_by_id))


class CrossrefProcessor(FormatProcessor):
    def __init__(self,
                 base_iri,
                 context_base,
                 info_dir,
                 entries,
                 res_finder,
                 of_finder,
                 n_file_item,
                 supplier_prefix,
                 headers={"User-Agent": "SPACIN / CrossrefProcessor (via OpenCitations - "
                                        "http://opencitations.net; mailto:contact@opencitations.net)"},
                 sec_to_wait=10,
                 max_iteration=6,
                 timeout=30,
                 use_doi_in_bibentry_as_id=True,
                 use_url_in_bibentry_as_id=True,
                 crossref_min_similarity_score=95.0,
                 intext_refs=False,
                 query_interface='remote'):

        self.crossref_api_works = "https://api.crossref.org/works/"
        self.crossref_api_search = "https://api.crossref.org/works?rows=3&query.bibliographic="  # return 3 results
        self.lengths = []
        self.rf = res_finder
        self.of = of_finder
        self.get_bib_entry_url = use_url_in_bibentry_as_id
        self.get_bib_entry_doi = use_doi_in_bibentry_as_id
        self.crossref_min_similarity_score = crossref_min_similarity_score
        self.intext_refs = intext_refs
        self.process_existing_by_id_time = 0

        super(CrossrefProcessor, self).__init__(
            base_iri, context_base, info_dir, entries, n_file_item, supplier_prefix, "Crossref")

        # Manage the query_interface, in order to select if we want to query our local
        # indexed version of Crossref/ORCID or their remote API
        if query_interface == 'local':
            self.query_interface = LocalQuery(reperr=self.reperr,
                                              repok=self.repok)
        elif query_interface == 'remote':
            self.query_interface = RemoteQuery(self.crossref_min_similarity_score,
                                               max_iteration,
                                               sec_to_wait,
                                               headers,
                                               timeout,
                                               reperr=self.reperr,
                                               repok=self.repok,
                                               is_json=True)
        else:
            raise ValueError("query_interface param must be `local` or `remote`")

    def process_citing_entity(self):
        # This method let us process the citing entity: this is the first step of the process, if the citing resource
        # hasn't been found in blazegraph.
        citing_entity = None

        if self.occ is not None:
            citing_resource = self.rf.retrieve_entity(self.occ, GraphEntity.expression, typ='only_blazegraph')
            citing_entity = self.g_set.add_br(self.name, self.id, self.source_provider, citing_resource)

        if citing_entity is None and self.doi is not None:
            citing_entity = self.process_doi_query(self.doi, self.curator, self.source_provider, typ='only_blazegraph')

        if citing_entity is None:
            # If the citing entity hasn't been found, then create one and update the graph
            citing_entity = self.g_set.add_br(self.name)
            self.__add_doi(citing_entity, self.doi, self.curator)

            # self.rf.update_graph_set(self.g_set)
            self.repok.add_sentence(
                self.message("The citing entity has been created even if no results have "
                             "been returned by the API.",
                             "doi", self.doi))

        # Add other ids if they exist
        self.__add_pmid(citing_entity, self.pmid)
        self.__add_pmcid(citing_entity, self.pmcid)

        # Process all the references contained and return related entities
        cited_entities = self.process_references()

        if cited_entities is not None:
            cited_entities_xmlid_be = []
            for idx, cited_entity in enumerate(cited_entities):
                citing_entity.has_citation(cited_entity)
                cur_bibentry = dg(self.entries[idx], ["bibentry"])
                cur_be_xmlid = dg(self.entries[idx], ["xmlid"])
                if cur_bibentry is not None and cur_bibentry.strip():
                    cur_be = self.g_set.add_be(self.curator, self.source_provider, self.source)
                    citing_entity.contains_in_reference_list(cur_be)

                    cited_entity.has_reference(cur_be)
                    self.__add_xmlid(cur_be, cur_be_xmlid)  # new
                    cur_be.create_content(cur_bibentry.strip())
                    cited_entities_xmlid_be.append((cited_entity, cur_be_xmlid, cur_be))

            # create rp, pl, de, ci, an
            if self.intext_refs:
                rp_entities = jt.process_reference_pointers(citing_entity, \
                                                            cited_entities_xmlid_be, self.reference_pointers,
                                                            self.g_set, \
                                                            self.curator, self.source_provider, self.source)
                # self.rf.update_graph_set(self.g_set)

            return self.g_set

    def process(self):
        """This methods returns a GraphSet populated with the citation data form the input
        source, or None if any issue has been encountered."""

        # The process can start if a DOI is specified
        if self.doi is not None:
            citing_resource = self.rf.retrieve_citing_from_doi(self.doi, typ='only_blazegraph')

            if citing_resource is None and self.pmid is not None:
                citing_resource = self.rf.retrieve_citing_from_pmid(self.pmid, typ='only_blazegraph')
            if citing_resource is None and self.pmcid is not None:
                citing_resource = self.rf.retrieve_citing_from_pmcid(self.pmcid, typ='only_blazegraph')
            if citing_resource is None and self.url is not None:
                citing_resource = self.rf.retrieve_citing_from_url(self.url, typ='only_blazegraph')

            if citing_resource is None:
                return self.process_citing_entity()
            else:
                self.repok.add_sentence(
                    "The citing entity with DOI '%s' has been already "
                    "processed in the past." % self.doi)

        # Otherwise if no DOI has been specified for the citing resource, nothing has been done
        else:
            self.reperr.add_sentence("No DOI has been specified for the citing resource.")

        self.query_interface.close()

    def process_references(self, do_process_entry=True):
        # Queue for results
        results_queue = queue.Queue()

        # Clear previously created bibentries objects
        # bibentries = queue.Queue()

        # Queue for done
        done = queue.Queue()

        # Insert new bibentries in the queue (in parallel)
        tasks = [create_bibentry(full_entry=full_entry, bibentries=bibentries, repok=self.repok, reperr=self.reperr,
                                 query_interface=self.query_interface, rf=self.rf,
                                 get_bib_entry_doi=self.get_bib_entry_doi, message=self.message,
                                 process_existing_by_id=self.process_existing_by_id) for full_entry in
                 self.entries]
        [t.join() for t in tasks]

        tot = 0

        for bibentry_entity in list(bibentries.queue):
            # for full_entry in self.entries:

            #    bibentry_entity = Bibentry(full_entry, self.repok, self.reperr, self.query_interface, self.rf, self.get_bib_entry_doi, self.message)

            self.repok.new_article()
            self.reperr.new_article()

            # Start time counter
            s = time.time()

            # If no resource has been found on blazegraph, then do a local search
            # and, if possible, create the resource according to returned data
            cur_res = bibentry_entity.cur_res

            if cur_res is None:

                # In the parallel part we've already taken the json result from Crossref. So, if there's any,
                # process it
                if bibentry_entity.provided_doi is not None and bibentry_entity.process_doi_result is not None:
                        cur_res = self.process_doi(bibentry_entity.provided_doi, self.curator, self.source_provider,
                                                   typ='only_local', result=bibentry_entity.process_doi_result)

                        if cur_res is not None:
                                self.repok.add_sentence(
                                    self.message("The entity has been found by means of the "
                                                 "DOI provided as input by %s." % self.source_provider,
                                                 "DOI", bibentry_entity.provided_doi))

                if cur_res is None and bibentry_entity.extracted_doi is not None and bibentry_entity.process_doi_result is not None and bibentry_entity.extracted_doi_used:
                    cur_res = self.process_doi(bibentry_entity.extracted_doi, self.name, self.source_provider,
                                               typ='only_local', result=bibentry_entity.process_doi_result)
                    if cur_res is not None:
                        self.repok.add_sentence(
                            self.message("The entity for '%s' has been found by means of the "
                                         "DOI extracted from it." % bibentry_entity.entry,
                                         "DOI", bibentry_entity.extracted_doi))

                if cur_res is None and bibentry_entity.provided_pmid is not None:
                    cur_res = self.process_pmid(bibentry_entity.provided_pmid)
                    if cur_res is not None:
                        self.repok.add_sentence(
                            self.message("The entity has been found by means of the "
                                         "PMID provided as input by %s." % self.source_provider,
                                         "PMID", bibentry_entity.provided_doi))

                if cur_res is None and bibentry_entity.provided_pmcid is not None:
                    cur_res = self.process_pmcid(bibentry_entity.provided_pmcid)
                    if cur_res is not None:
                        self.repok.add_sentence(
                            self.message("The entity has been found by means of the "
                                         "PMCID provided as input by %s." % self.source_provider,
                                         "PMCID", bibentry_entity.provided_pmcid))

                if cur_res is None and bibentry_entity.entry is not None:  # crossref API string search
                    if do_process_entry == True:
                        cur_res = self.process_entry(entry=bibentry_entity.entry,
                                                     cur_json=bibentry_entity.existing_bibref_entry,
                                                     research=False)
                        if cur_res is not None:
                            self.repok.add_sentence(
                                self.message(
                                    "The entity has been retrieved by using the search API.",
                                    "entry", bibentry_entity.entry))

            # If no errors were generated, proceed
            if self.reperr.is_empty():

                # If there's no cur_res neither in local, create the resource
                if cur_res is None:
                    # Add it on the graph
                    cur_res = self.g_set.add_br(self.name)
                    self.repok.add_sentence(
                        self.message("The entity has been created even if no results have "
                                     "been returned by the API.",
                                     "entry", bibentry_entity.entry))

                    # self.rf.update_graph_set(self.g_set)

                # Add the DOI, the PMID and the PMCID if they have been provided by the curator
                # (if they are not already associated to the resource)
                self.__add_doi(cur_res, bibentry_entity.provided_doi, self.curator)
                self.__add_pmid(cur_res, bibentry_entity.provided_pmid)
                self.__add_pmcid(cur_res, bibentry_entity.provided_pmcid)
                self.__add_url(cur_res, bibentry_entity.provided_url)

                # Add any DOI extracted from the entry if it is not already included (and only if
                # a resource has not been retrieved by a DOI specified in the entry explicitly, or
                # by a Crossref search.
                if self.get_bib_entry_doi and bibentry_entity.extracted_doi_used:
                    self.__add_doi(cur_res, bibentry_entity.extracted_doi, self.name)

                # Add any URL extracted from the entry if it is not already included
                if self.get_bib_entry_url == True and bibentry_entity.extracted_url is not None:
                    self.__add_url(cur_res, bibentry_entity.extracted_url)

                results_queue.put(cur_res)
                done.put(bibentry_entity)

                # self.rf.update_graph_set(self.g_set)
                e = time.time()
                tot += e - s


            else:  # If errors have been raised, stop the process for this entry (by returning None)
                done.put(bibentry_entity)
                return None

        results = list(results_queue.queue)
        #print(f"Tot time for processing references: {(tot)}")

        bibentries.queue.clear()

        # If the process comes here, then everything worked correctly
        return results

    def process_existing_by_id(self, existing_res, source_provider):
        if existing_res is not None:
            self.process_existing_by_id_time += 1
            result = self.g_set.add_br(self.name, source_provider, self.source, existing_res)
            # self.rf.update_graph_set(self.g_set)
            return result

    def process_crossref_json(self, crossref_json: dict, crossref_source: str, doi_curator=None, doi_source_provider=None,
                              doi_source=None, typ='only_local'):
        """
        This is to process a json result from Crossref and get a fill the graph with the data
        :param crossref_json: the json document retrieved from Crossref
        :return: the reference on the graph for the processed json
        """
        #self.rf.update_graph_set(self.g_set)

        if not isinstance(crossref_json, dict):
            print(f"Error: crossref_json is not a dict, it's {type(crossref_json)} ")
            return

        # Check if the found bibliographic resource already exist locally.
        retrieved_resource = self.rf.retrieve(CrossrefDataHandler.get_ids_for_type(crossref_json), typ=typ)

        # If has been found, add the reference to it to the graph
        if retrieved_resource is not None:
            cur_br = self.g_set.add_br(self.name, self.id, crossref_source, retrieved_resource)
        else:
            # Otherwise, process the json and extract all the needed data from it
            cdh = CrossrefDataHandler(graph_set=self.g_set, orcid_finder=self.of, resource_finder=self.rf)
            cur_br = cdh.process_json(crossref_json, crossref_source, doi_curator, doi_source_provider, doi_source)
        return cur_br

    def message(self, mess, entity_type, entity, url="not provided"):
        return super(CrossrefProcessor, self).message(mess) + \
               "\n\t%s: %s\n\tURL: %s" % (entity_type, entity, url)


    def process_entry(self, entry: str, cur_json=None, check: bool = False, research=True):
        """
        This method let you process a bibliographic entry. It's possible both to
        :param entry: the bibliographic reference
        :param cur_json: the json already retrieved from Crossref (if given)
        :param check: Set it to True only in the tests in order to return the json
        :return: reference of the entity processed
        """

        if cur_json is None and research:
            cur_json = self.query_interface.get_data_crossref_bibref(entry)

        if cur_json is not None:
            return self.process_crossref_json(cur_json,
                                              self.crossref_api_search + FormatProcessor.clean_entry(entry),
                                              self.name,
                                              self.id,
                                              self.source)

    def process_doi(self, doi: str, doi_curator: str, doi_source_provider: str, check=False, result=None, typ='both'):
        """
        Process a DOI searching for it on Crossref (local/remote).

        Parameters
        ----------
        :param doi: The DOI to be searched.
        :param doi_curator : The curator(URL), e.g.: https://api.crossref.org/works/
        :param doi_source_provider: The source provider, e.g.: Europe PubMed Central
        :param check: Set it to True only in the tests in order to return the json
        :param result: A result retrieved with the query_interface during the Bibentry creation process
        :param typ: A string that can be 'both', 'only_local', or 'only_blazegraph'. Useful when you want to query
                    only on a specific kind of store.

        """

        # Check if we already have this resource
        existing_res = self.rf.retrieve_from_doi(doi, typ=typ)

        # Otherwise query for it
        if existing_res is None:
            if result is None:
                cur_json = self.query_interface.get_data_crossref_doi(doi)
            else:
                cur_json = result

            if cur_json is not None:
                if check:
                    return cur_json
                else:
                    return self.process_crossref_json(cur_json,
                                                    self.crossref_api_works + encode_url(doi),
                                                    doi_curator,
                                                    doi_source_provider,
                                                    self.source)

        else:
            return self.process_existing_by_id(existing_res, self.id)

    def process_doi_query(self, doi: str, doi_curator: str, doi_source_provider: str, check=False,
                    typ='both'):
        """
        Process a DOI searching for it on Crossref (local/remote). If no result is found with blazegraph/local,
        then query for it.

        Parameters
        ----------
        :param doi: The DOI to be searched.
        :param doi_curator : The curator(URL), e.g.: https://api.crossref.org/works/
        :param doi_source_provider: The source provider, e.g.: Europe PubMed Central
        :param check: Set it to True only in the tests in order to return the json
        :param result: A result retrieved with the query_interface during the Bibentry creation process
        :param typ: A string that can be 'both', 'only_local', or 'only_blazegraph'. Useful when you want to query
                    only on a specific kind of store.

        """

        # Check if we already have this resource
        existing_res = self.rf.retrieve_from_doi(doi, typ=typ)

        # Otherwise query for it
        if existing_res is None:
            cur_json = self.query_interface.get_data_crossref_doi(doi)

            if cur_json is not None:
                if check:
                    return cur_json
                else:
                    return self.process_crossref_json(cur_json,
                                                      self.crossref_api_works + encode_url(doi),
                                                      doi_curator,
                                                      doi_source_provider,
                                                      self.source,
                                                      typ)

        else:
            return self.process_existing_by_id(existing_res, self.id)

    def __add_url(self, cur_res, extracted_url):
        # self.rf.update_graph_set(self.g_set)
        if extracted_url is not None:
            cur_id = self.rf.retrieve_br_url(cur_res.res, extracted_url, typ='only_local')

            if cur_id is None:
                cur_id = self.g_set.add_id(self.name, self.source_provider, self.source)
                cur_id.create_url(extracted_url)
                cur_res.has_id(cur_id)

            # Update ResourceFinder's dict in order to enable a local search for it
            self.rf.url_store_type_id[f"{cur_res}_{extracted_url}"] = cur_id
            self.rf.url_store_type[f"{cur_res}"] = extracted_url
            self.rf.url_store[f"{extracted_url}"] = cur_res

    def __add_pmid(self, cur_res, pmid_string):
        # self.rf.update_graph_set(self.g_set)
        if pmid_string is not None:
            cur_id = self.rf.retrieve_br_pmid(cur_res.res, pmid_string, typ='only_local')

            if cur_id is None:
                cur_id = self.g_set.add_id(self.curator, self.source_provider, self.source)
                cur_id.create_pmid(pmid_string)
                cur_res.has_id(cur_id)

            # Update ResourceFinder's dict in order to enable a local search for it
            self.rf.pmid_store_type_id[f"{cur_res}_{pmid_string}"] = cur_id
            self.rf.pmid_store_type[f"{cur_res}"] = pmid_string
            self.rf.pmid_store[f"{pmid_string}"] = cur_res

    def __add_pmcid(self, cur_res, pmcid_string):
        # self.rf.update_graph_set(self.g_set)
        if pmcid_string is not None:
            cur_id = self.rf.retrieve_br_pmcid(cur_res.res, pmcid_string, typ='only_local')

            if cur_id is None:
                cur_id = self.g_set.add_id(self.curator, self.source_provider, self.source)
                cur_id.create_pmcid(pmcid_string)
                cur_res.has_id(cur_id)

            # Update ResourceFinder's dict in order to enable a local search for it
            self.rf.pmcid_store_type_id[f"{cur_res}_{pmcid_string}"] = cur_id
            self.rf.pmcid_store_type[f"{cur_res}"] = pmcid_string
            self.rf.pmcid_store[f"{pmcid_string}"] = cur_res

    def __add_doi(self, cur_res, extracted_doi, curator):
        # self.rf.update_graph_set(self.g_set)
        if extracted_doi is not None:
            if hasattr(cur_res, 'res'):
                cur_id = self.rf.retrieve_br_doi(cur_res.res, extracted_doi, typ='only_local')
            else:
                cur_id = self.rf.retrieve_br_doi(cur_res, extracted_doi, typ='only_local')

            if cur_id is None:
                cur_id = self.g_set.add_id(curator, self.source_provider, self.source)
                cur_id.create_doi(extracted_doi)
                cur_res.has_id(cur_id)

            # Update ResourceFinder's dict in order to enable a local search for it
            self.rf.add_doi_to_store(cur_res, cur_id, extracted_doi)


    def __add_xmlid(self, cur_res, xmlid_string):  #  new
        # self.rf.update_graph_set(self.g_set)
        if xmlid_string is not None:
            cur_id = self.g_set.add_id(self.curator, self.source_provider, self.source)
            cur_id.create_xmlid(xmlid_string)
            cur_res.has_id(cur_id)

    # Local version
    def process_pmid(self, pmid):
        existing_res = self.rf.retrieve_from_pmid(pmid, typ='only_local')
        return self.process_existing_by_id(existing_res, self.id)

    # Local version
    def process_pmcid(self, pmcid):
        existing_res = self.rf.retrieve_from_pmcid(pmcid, typ='only_local')
        return self.process_existing_by_id(existing_res, self.id)

    # Local version
    def process_url(self, url):
        existing_res = self.rf.retrieve_from_url(url, typ='only_local')
        return self.process_existing_by_id(existing_res, self.id)

    # Add the number of triples in the graph in a local array in order to do troubleshooting
    def update_length(self):
        # TODO Remove
        ss = set()
        for g in self.g_set.g:
            for (s, o, p) in g:
                ss.add(f"{s}{o}{p}")
        self.lengths.append(len(ss))

    # Print all the triples in the graphset
    def print_graph(self):
        # TODO Remove
        ss = set()
        for g in self.g_set.g:
            for (s, o, p) in g:
                print(f"{s} {o} {p}")
