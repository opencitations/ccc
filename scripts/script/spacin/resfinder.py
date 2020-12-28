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

from rdflib import Graph, ConjunctiveGraph
from script.ocdm.graphlib import GraphEntity, ProvEntity
from script.ocdm.storer import Storer
import os
from script.support.support import find_paths

import re


class ResourceFinder(object):

    def __init__(self, g_set=None, ts_url=None, base_dir=None, base_iri=None, default_dir="_",
                 tmp_dir=None, context_map={}, dir_split=0, n_file_item=1):
        self.g = Graph()
        self.base_dir = base_dir
        self.base_iri = base_iri
        self.storer = Storer(context_map=context_map)
        self.tmp_dir = tmp_dir
        self.dir_split = dir_split
        self.n_file_item = n_file_item
        self.name = "SPACIN " + self.__class__.__name__
        self.loaded = set()
        self.default_dir = default_dir
        self.index_for_graph_set = 0
        #self.check = False

        if g_set is not None:
            self.update_graph_set(g_set)
        if ts_url is None:
            self.ts = None
        else:
            self.ts = ConjunctiveGraph('SPARQLUpdateStore')
            self.ts.open((ts_url, ts_url))
            self.ts.namespace_manager.store.nsBindings = {}

        # This is to search eg.: for doi and get the res
        self.doi_store = {}
        self.orcid_store = {}
        self.pmid_store = {}
        self.pmcid_store = {}
        self.url_store = {}
        self.issn_store = {}
        self.isbn_store = {}
        self.crossref_store = {}

        # Used in __retrieve_res_id_string() when you query for the {res} and want to get ids literal values
        self.doi_store_type = {}
        self.orcid_store_type = {}
        self.pmid_store_type = {}
        self.pmcid_store_type = {}
        self.url_store_type = {}
        self.issn_store_type = {}
        self.isbn_store_type = {}
        self.crossref_store_type = {}

        # Used in __retrieve_res_id_by_type() when you query for the {res}_{id_literal} and
        # want to get id's URI,
        #
        # eg: calling
        #               cur_id = self.rf.retrieve_br_url(cur_res.res, extracted_url)
        # in crossrefproc.py
        self.doi_store_type_id = {}
        self.orcid_store_type_id = {}
        self.pmid_store_type_id = {}
        self.pmcid_store_type_id = {}
        self.url_store_type_id = {}
        self.issn_store_type_id = {}
        self.isbn_store_type_id = {}
        self.crossref_store_type_id = {}

        # Used in __retrieve_from_journal() where you query for
        # {id_type}_{id_string}_{part_seq_id} and get the res
        # e.g. http://purl.org/spar/datacite/issn_1388-0209_58
        # ISSN_1388-0209_volume_58
        self.from_journal = {}
        self.from_journal_volume = {}
        self.from_journal_issue = {}
        self.from_issue_partof_journal = {}

        # Caching blazegraph queries
        self.cache = {}
        self.cache_local = {}

    def add_prov_triples_in_filesystem(self, res_iri, prov_entity_type=None):
        if self.base_dir is not None and self.base_iri is not None:
            cur_file_path = find_paths(res_iri, self.base_dir, self.base_iri, self.default_dir,
                                       self.dir_split, self.n_file_item)[1]
            if cur_file_path.endswith("index.json"):
                cur_path = cur_file_path.replace("index.json", "") + "prov"
            else:
                cur_path = cur_file_path[:-5] + os.sep + "prov"

            file_list = []
            if os.path.isdir(cur_path):
                for cur_dir, cur_subdir, cur_files in os.walk(cur_path):
                    for cur_file in cur_files:
                        if (cur_file.endswith(".json") or cur_file.endswith(".ttl")) and \
                                (prov_entity_type is None or cur_file.startswith(prov_entity_type)):
                            file_list += [cur_dir + os.sep + cur_file]

            for file_path in file_list:
                if file_path not in self.loaded:
                    self.loaded.add(file_path)
                    cur_g = self.storer.load(file_path, tmp_dir=self.tmp_dir)
                    #self.add_triples_in_graph(cur_g)

    def add_triples_in_graph(self, g):
        return
        # This is deprecated
        if g is not None:
            for s, p, o in g.triples((None, None, None)):
                self.g.add((s, p, o))

    def update_graph_set(self, g_set):
        return
        # This is deprecated
        for g in g_set.graphs()[self.index_for_graph_set:]:
            self.add_triples_in_graph(g)
            self.index_for_graph_set += 1

    def retrieve(self, id_dict, typ='both'):
        for id_type in id_dict:
            for id_string in id_dict[id_type]:
                res = self.__id_with_type(str(id_string), str(id_type), typ=typ)
                if res is not None:
                    return res

    '''
    def retrieve_provenance_agent_from_name(self, string):
        query = f"""
            SELECT DISTINCT ?pa WHERE {{
              ?pa a <{ProvEntity.prov_agent}> ;
                <{GraphEntity.name}> "{string}"
            }} LIMIT 1
            """
        return self.__query(query)

    def retrieve_reference(self, citing_res, cited_res):
        query = f"""
            SELECT DISTINCT ?res WHERE {{
                <{citing_res}> <{GraphEntity.contains_reference}> ?res .
                ?res <{GraphEntity.references}> <{cited_res}>
            }}"""
        return self.__query(query)

    def retrieve_reference_text(self, ref_res):
        query = f"""
            SELECT DISTINCT ?res WHERE {{
                <{ref_res}> <{GraphEntity.has_content}> ?res
            }}"""
        return self.__query(query)

    def retrieve_modification_date(self, res_iri):
        query = f"""
                SELECT DISTINCT ?res WHERE {{
                    <{res_iri}> ^<{ProvEntity.specialization_of}> ?snapshot .
                    FILTER NOT EXISTS {{ ?snapshop <{ProvEntity.invalidated_at_time}> ?inv_date }}
                    ?snapshop <{ProvEntity.generated_at_time}> ?res
                }}"""
        return self.__query(query)
    '''

    def retrieve_from_orcid(self, string, typ='both'):
        return self.__id_with_type(string, GraphEntity.orcid, typ=typ)

    def retrieve_entity(self, string, typ='both'):
        query = """
                SELECT DISTINCT ?res WHERE {{
                    BIND(iri("{}") as ?res) .
                    ?res a <{}>
                }}""".format(string, str(type))
        return self.__query(query, typ=typ)

    def retrieve_citing_from_doi(self, string, typ='only_blazegraph'):
        return self.__id_with_type(
            string.lower(), GraphEntity.doi, "?res <%s> ?cited" % GraphEntity.cites, typ)

    def retrieve_citing_from_pmid(self, string, typ='only_blazegraph'):
        return self.__id_with_type(
            string, GraphEntity.pmid, "?res <%s> ?cited" % GraphEntity.cites, typ)

    def retrieve_citing_from_pmcid(self, string, typ='only_blazegraph'):
        return self.__id_with_type(
            string, GraphEntity.pmcid, "?res <%s> ?cited" % GraphEntity.cites, typ)

    def retrieve_citing_from_url(self, string, typ='only_blazegraph'):
        return self.__id_with_type(
            string.lower(), GraphEntity.url, "?res <%s> ?cited" % GraphEntity.cites, typ)

    def retrieve_from_doi(self, string, typ='both'):
        return self.__id_with_type(string.lower(), GraphEntity.doi, typ=typ)

    def retrieve_from_pmid(self, string, typ='both'):
        return self.__id_with_type(string, GraphEntity.pmid, typ=typ)

    def retrieve_from_pmcid(self, string, typ='both'):
        return self.__id_with_type(string, GraphEntity.pmcid, typ=typ)

    def retrieve_from_url(self, string, typ='both'):
        return self.__id_with_type(string.lower(), GraphEntity.url, typ=typ)

    def retrieve_from_issn(self, string, typ='both'):
        return self.__id_with_type(string, GraphEntity.issn, typ=typ)

    def retrieve_from_isbn(self, string, typ='both'):
        return self.__id_with_type(string, GraphEntity.isbn, typ=typ)

    def retrieve_issue_from_journal(self, id_dict, issue_id, volume_id):

        # If volume_id is None, the return from then retrieve this the issue
        if volume_id is None:
            return self.__retrieve_from_journal(id_dict, GraphEntity.journal_issue, issue_id)

        else:

            retrieved_volume = self.retrieve_volume_from_journal(id_dict, volume_id)

            if retrieved_volume is not None:
                if self.from_issue_partof_journal.__contains__("{}_{}".format(str(retrieved_volume), issue_id)):
                    return self.from_issue_partof_journal["{}_{}".format(str(retrieved_volume), issue_id)]
                else:
                    query = """
                        SELECT DISTINCT ?br WHERE {{
                            ?br a <{}> ;
                                <{}> <{}> ;
                                <{}> "{}"
                        }} LIMIT 1
                    """.format(GraphEntity.journal_issue, GraphEntity.part_of, str(retrieved_volume), GraphEntity.has_sequence_identifier, issue_id)
                    return self.__query(query)

    def retrieve_volume_from_journal(self, id_dict, volume_id):
        return self.__retrieve_from_journal(id_dict, GraphEntity.journal_volume, volume_id)

    def retrieve_url_string(self, res, typ):
        return self.__retrieve_res_id_string(res, GraphEntity.url, typ)

    def retrieve_doi_string(self, res, typ):
        return self.__retrieve_res_id_string(res, GraphEntity.doi, typ)

    def retrieve_pmid_string(self, res, typ):
        return self.__retrieve_res_id_string(res, GraphEntity.pmid, typ)

    def retrieve_pmcid_string(self, res, typ):
        return self.__retrieve_res_id_string(res, GraphEntity.pmcid, typ)

    def retrieve_br_url(self, res, string, typ):
        return self.__retrieve_res_id_by_type(res, string.lower(), GraphEntity.url, typ)

    def retrieve_br_doi(self, res, string, typ):
        return self.__retrieve_res_id_by_type(res, string.lower(), GraphEntity.doi, typ)

    def retrieve_br_pmid(self, res, string, typ):
        return self.__retrieve_res_id_by_type(res, string, GraphEntity.pmid, typ)

    def retrieve_br_pmcid(self, res, string, typ):
        return self.__retrieve_res_id_by_type(res, string, GraphEntity.pmcid, typ)

    def retrieve_last_snapshot(self, prov_subj):
        query = '''
            SELECT DISTINCT ?se WHERE {{
                ?se <{}> <{}> .
                FILTER NOT EXISTS {{?se <{}> ?ca }}
            }} LIMIT 1
        '''.format(ProvEntity.specialization_of, str(prov_subj), ProvEntity.was_invalidated_by)
        return self.__query(query)

    def __retrieve_res_id_string(self, res, id_type, typ):

        # First check if locally there's something
        if id_type is not None and id is not None:
            if str(id_type) == 'http://purl.org/spar/datacite/url':
                store = self.url_store_type
            elif str(id_type) == 'http://purl.org/spar/datacite/doi':
                store = self.doi_store_type
            elif str(id_type) == 'http://purl.org/spar/datacite/orcid':
                store = self.orcid_store_type
            elif str(id_type) == 'http://purl.org/spar/datacite/pmid':
                store = self.pmid_store_type
            elif str(id_type) == 'http://purl.org/spar/datacite/pmcid':
                store = self.pmcid_store_type
            elif str(id_type) == 'http://purl.org/spar/datacite/issn':
                store = self.issn_store_type
            elif str(id_type) == 'http://purl.org/spar/datacite/isbn':
                store = self.isbn_store_type

            if str(id_type) == 'http://purl.org/spar/datacite/orcid' or\
                    str(id_type) == 'http://purl.org/spar/datacite/issn' or \
                    str(id_type) == 'http://purl.org/spar/datacite/isbn':
                if store.__contains__('{}'.format(res)):
                    return store['{}'.format(res)][0]

            elif store.__contains__('{}'.format(res)):
                return store['{}'.format(res)]

        if typ != 'only_local':
            query = '''
            SELECT DISTINCT ?id WHERE {{
                <{}> <{}> [
                    <{}> <{}> ;
                    <{}> ?id
                ]
            }}'''.format(res, GraphEntity.has_identifier, GraphEntity.uses_identifier_scheme, id_type, GraphEntity.has_literal_value)
            return self.__query_blazegraph(query, typ)

    def __retrieve_res_id_by_type(self, res, id_string, id_type, typ):

        # First check if locally there's something
        if id_type is not None and id is not None:
            if str(id_type) == 'http://purl.org/spar/datacite/url':
                store = self.url_store_type_id
            elif str(id_type) == 'http://purl.org/spar/datacite/doi':
                store = self.doi_store_type_id
            elif str(id_type) == 'http://purl.org/spar/datacite/orcid':
                store = self.orcid_store_type_id
            elif str(id_type) == 'http://purl.org/spar/datacite/pmid':
                store = self.pmid_store_type_id
            elif str(id_type) == 'http://purl.org/spar/datacite/pmcid':
                store = self.pmcid_store_type_id
            elif str(id_type) == 'http://purl.org/spar/datacite/issn':
                store = self.issn_store_type_id
            elif str(id_type) == 'http://purl.org/spar/datacite/isbn':
                store = self.isbn_store_type_id

            if str(id_type) == 'http://purl.org/spar/datacite/orcid' or\
                    str(id_type) == 'http://purl.org/spar/datacite/issn' or \
                    str(id_type) == 'http://purl.org/spar/datacite/isbn':
                if store.__contains__('{}_{}'.format(res, id_string)):
                    return store['{}_{}'.format(res, id_string)][0]

            elif store.__contains__('{}_{}'.format(res, id_string)):
                return store['{}_{}'.format(res, id_string)]

        if id_string is not None and typ != 'only_local':
            query = '''
            SELECT DISTINCT ?id WHERE {{
                <{}> <{}> ?id .
                ?id <{}> <{}> ;
                    <{}> "{}"
            }}'''.format(res, GraphEntity.has_identifier, GraphEntity.uses_identifier_scheme, id_type, GraphEntity.has_literal_value,id_string )

            return self.__query_blazegraph(query)

    def add_doi_to_store(self, cur_res, cur_id, extracted_doi):
        if cur_res is not None and cur_id is not None and extracted_doi is not None:

            # Check if local store doesn't contains already the elements
            if self.doi_store_type_id.__contains__("{}_{}".format(cur_res, extracted_doi)) == False \
            and self.doi_store_type.__contains__("{}".format(cur_res)) == False \
            and self.doi_store.__contains__("{}".format(extracted_doi)) == False:

                # Add it
                self.doi_store_type_id["{}_{}".format(cur_res, extracted_doi)] = cur_id
                self.doi_store_type["{}".format(cur_res)] = extracted_doi
                self.doi_store["{}".format(extracted_doi)] = cur_res

    def add_url_to_store(self, cur_res, cur_id, extracted_url):
        if cur_res is not None and cur_id is not None and extracted_url is not None:

            # Check if local store doesn't contains already the elements
            if self.url_store_type_id.__contains__("{}_{}".format(cur_res, extracted_url)) == False \
            and self.url_store_type.__contains__("{}".format(cur_res)) == False \
            and self.url_store.__contains__("{}".format(extracted_url)) == False:

                # Add it
                self.url_store_type_id["{}_{}".format(cur_res, extracted_url)] = cur_id
                self.url_store_type["{}".format(cur_res)] = extracted_url
                self.url_store["{}".format(extracted_url)] = cur_res

    def add_issn_to_store(self, cur_res, cur_id, isbns):
        for isbn in isbns:
            if cur_res is not None and cur_id is not None and isbn is not None:
                # If empty create array
                if not self.isbn_store_type_id.__contains__("{}_{}".format(cur_res, isbn)):
                    self.isbn_store_type_id["{}_{}".format(cur_res, isbn)] = [cur_id]

                if not self.isbn_store_type.__contains__("{}".format(cur_res)):
                    self.isbn_store_type["{}".format(cur_res)] = [cur_id]
                else:
                    self.isbn_store_type["{}".format(cur_res)] += [cur_id]

                if not self.isbn_store.__contains__("{}".format(isbn)):
                    self.isbn_store["{}".format(isbn)] = [cur_res]
                else:
                    self.isbn_store["{}".format(isbn)] += [cur_res]
                    
    def add_issn_to_store(self, cur_res, cur_id, issns):
        for issn in issns:
            if cur_res is not None and cur_id is not None and issn is not None:
                # If empty create array
                if not self.issn_store_type_id.__contains__("{}_{}".format(cur_res, issn)):
                    self.issn_store_type_id["{}_{}".format(cur_res, issn)] = [cur_id]

                if not self.issn_store_type.__contains__("{}".format(cur_res)):
                    self.issn_store_type["{}".format(cur_res)] = [cur_id]
                else:
                    self.issn_store_type["{}".format(cur_res)] += [cur_id]

                if not self.issn_store.__contains__("{}".format(issn)):
                    self.issn_store["{}".format(issn)] = [cur_res]
                else:
                    self.issn_store["{}".format(issn)] += [cur_res]
 
    def add_orcid_to_store(self, cur_res, cur_id, orcid):

        if cur_res is not None and cur_id is not None and orcid is not None:

            # If empty create array
            if not self.orcid_store_type_id.__contains__("{}_{}".format(cur_res, orcid)):
                self.orcid_store_type_id["{}_{}".format(cur_res, orcid)] = []

            if not self.orcid_store_type.__contains__("{}".format(cur_res)):
                self.orcid_store_type["{}".format(cur_res)] = []

            if not self.orcid_store.__contains__("{}".format(orcid)):
                self.orcid_store["{}".format(orcid)] = []

            # Add it
            self.orcid_store_type_id["{}_{}".format(cur_res, orcid)] += [cur_id.res]
            self.orcid_store_type["{}".format(cur_res)] += [orcid]
            self.orcid_store["{}".format(orcid)] += [cur_res.res]

    def add_issue_to_store(self, cur_res, cur_id, issue):
        if cur_res is not None and cur_id is not None and issue is not None:
            # Check if local store doesn't contains already the elements
            if self.from_journal_issue.__contains__("{}_{}".format(cur_res, issue)) == False:
                # Add it
                self.from_journal_issue["{}_{}".format(cur_res, issue)] = cur_id.res

    def add_volume_to_store(self, cur_res, cur_id, volume):
        if cur_res is not None and cur_id is not None and volume is not None:
            # Check if local store doesn't contains already the elements
            if self.from_journal_volume.__contains__("{}_{}".format(cur_res, volume)) == False:
                # Add it
                self.from_journal_volume["{}_{}".format(cur_res, volume)] = cur_id.res

    def add_journal_to_store(self, id_string, part_type, part_seq_id, res):
        if id_string is not None and part_type is not None and part_seq_id is not None:
            self.from_journal["{}_{}_{}".format(id_string, part_type,part_seq_id)] = res.res

    def __retrieve_from_journal(self, id_dict, part_type, part_seq_id):
        # Check locally
        for id_type in id_dict:
            for id_string in id_dict[id_type]:

                if self.from_journal.__contains__("{}_{}_{}".format(id_string, part_type, part_seq_id)):
                    # The id_string belongs to the journal, while the part_seq_id is the
                    # string related to the part type of the journal
                    return self.from_journal["{}_{}_{}".format(id_string, part_type, part_seq_id)]

        # If not present, check in blazegraph
        # a journal that has a specific ID, which <journal literal id> is given, and at which is attached, then there's a resource
        # that is part of this journal that has a <sequence_identifier>(journal/issue> with a specific <part_seq_id>(literal)
        # we want that resource
        for id_type in id_dict:
            for id_string in id_dict[id_type]:

                query = '''
                SELECT DISTINCT ?res WHERE {{
                    ?j <{}> ?id .
                    ?id
                        <{}> <{}> ;
                        <{}> "{}" .
                    ?res a <{}> ;
                        <{}>+ ?j ;
                        <{}> "{}"
                }}'''.format(GraphEntity.has_identifier, GraphEntity.uses_identifier_scheme, id_type,
                             GraphEntity.has_literal_value, id_string,part_type, GraphEntity.part_of, GraphEntity.has_sequence_identifier,
                             part_seq_id)
                ret = self.__query(query, 'both')
                if ret is not None:
                    return ret

    def __id_with_type(self, id_string, id_type, extras="", typ='both'):
        """This method is called when we need to get the resource having a certain identifier. It first check locally
        if something has already been stored and then check on the blazegraph instance"""

        # First check if locally there's something

        if typ != 'only_blazegraph' and id_type is not None and id_string is not None:
            if str(id_type) == 'http://purl.org/spar/datacite/url':
                store = self.url_store
            elif str(id_type) == 'http://purl.org/spar/datacite/doi':
                store = self.doi_store
            elif str(id_type) == 'http://purl.org/spar/datacite/orcid':
                store = self.orcid_store
            elif str(id_type) == 'http://purl.org/spar/datacite/pmid':
                store = self.pmid_store
            elif str(id_type) == 'http://purl.org/spar/datacite/pmcid':
                store = self.pmcid_store
            elif str(id_type) == 'http://purl.org/spar/datacite/issn':
                store = self.issn_store
            elif str(id_type) == 'http://purl.org/spar/datacite/isbn':
                store = self.isbn_store

            if str(id_type) == 'http://purl.org/spar/datacite/orcid' or\
                    str(id_type) == 'http://purl.org/spar/datacite/issn' or \
                    str(id_type) == 'http://purl.org/spar/datacite/isbn':
                if store.__contains__(id_string):
                    return store["{}".format(id_string)][0]

            elif store.__contains__(id_string):
                return store["{}".format(id_string)]

        # If nothing found, query blazegraph
        if typ != 'only_local':
            query = '''SELECT DISTINCT ?res WHERE {{ ?res <{}> ?id .
                ?id <{}> <{}> ;
                    <{}> "{}" .
                {}
            }}'''.format(GraphEntity.has_identifier, GraphEntity.uses_identifier_scheme, id_type,
                         GraphEntity.has_literal_value, id_string, extras)

            return self.__query_blazegraph(query, typ=typ)

    def __query(self, query, typ='only_blazegraph'):

        if self.ts is not None and (typ == 'both' or typ == 'only_blazegraph'):
            res = self.__query_blazegraph(query)
            if res is not None:
                return res

    def __query_blazegraph(self, query, typ=None):
        if self.ts is not None:

            if self.cache.__contains__(query):
                result = self.cache[query]
            else:
                result = self.ts.query(query)
                for res, in result:
                    self.cache[query] = res
                    return res

    def __query_local(self, query):
        # Deprecated
        if self.cache_local.__contains__(query):
            result = self.cache_local[query]
        else:
            result = self.g.query(query)
            if result is not None and len(result):
                self.cache_local[query] = result
        for res, in result:
            return res
