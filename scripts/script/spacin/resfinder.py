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

from rdflib import Graph, ConjunctiveGraph, URIRef
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
        self.from_journal_volume = {}
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
                res = self.__id_with_type(id_string, id_type, typ=typ)
                if res is not None:
                    return res

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

    def retrieve_from_crossref(self, string, typ='both'):
        return self.__id_with_type(string, GraphEntity.crossref, typ=typ)

    def retrieve_from_issn(self, string, typ='both'):
        return self.__id_with_type(string, GraphEntity.issn, typ=typ)

    def retrieve_from_isbn(self, string, typ='both'):
        return self.__id_with_type(string, GraphEntity.isbn, typ=typ)

    def retrieve_issue_from_journal(self, id_dict, issue_id, volume_id):
        retrieved_journal = self.retrieve(id_dict, 'both')

        if retrieved_journal is not None:
            cur_issue = self.from_issue_partof_journal.get((retrieved_journal, volume_id, issue_id))

            if cur_issue is None:
                if volume_id is None:
                    query = """
                            SELECT DISTINCT ?br WHERE {{
                                ?br a <{}> ;
                                    <{}> <{}> ;
                                    <{}> "{}"
                            }} LIMIT 1
                        """.format(GraphEntity.journal_issue, GraphEntity.part_of, retrieved_journal, GraphEntity.has_sequence_identifier, issue_id)
                else:
                    query = """
                            SELECT DISTINCT ?br WHERE {{
                                ?br a <{}> ;
                                    <{}> [
                                        a <{}> ;
                                        <{}> <{}> ;
                                        <{}> "{}" 
                                    ] ;
                                    <{}> "{}" . 
                            }} LIMIT 1
                        """.format(GraphEntity.journal_issue, GraphEntity.part_of, GraphEntity.journal_volume, GraphEntity.part_of, retrieved_journal, GraphEntity.has_sequence_identifier, volume_id, GraphEntity.has_sequence_identifier, issue_id)
                return self.__query(query)

            else:
                return cur_issue

    def retrieve_volume_from_journal(self, id_dict, volume_id):
        retrieved_journal = self.retrieve(id_dict, 'both')

        if retrieved_journal is not None:
            cur_volume = self.from_journal_volume.get((retrieved_journal, volume_id))

            if cur_volume is None:
                query = """
                        SELECT DISTINCT ?br WHERE {{
                            ?br a <{}> ;
                                <{}> <{}> ;
                                <{}> "{}"
                        }} LIMIT 1
                    """.format(GraphEntity.journal_volume, GraphEntity.part_of, retrieved_journal, GraphEntity.has_sequence_identifier, volume_id)
                return self.__query(query)

            else:
                return cur_volume

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

    def __retrieve_res_id_string(self, input_res, id_type, typ):
        if id_type is not None and input_res is not None:
            if type(input_res) is GraphEntity:
                res = input_res.res
            else:
                res = URIRef(input_res)

            # First check if locally there's something
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
            elif str(id_type) == 'http://purl.org/spar/datacite/crossref':
                store = self.crossref_store_type

            if str(id_type) == 'http://purl.org/spar/datacite/issn' or \
               str(id_type) == 'http://purl.org/spar/datacite/isbn':
                if res in store:
                    return store[res][0]

            elif res in store:
                return store[res]

            if typ != 'only_local':
                query = '''
                SELECT DISTINCT ?id WHERE {{
                    <{}> <{}> [
                        <{}> <{}> ;
                        <{}> ?id
                    ]
                }}'''.format(res, GraphEntity.has_identifier, GraphEntity.uses_identifier_scheme, id_type, GraphEntity.has_literal_value)
                return self.__query_blazegraph(query, typ)

    def __retrieve_res_id_by_type(self, input_res, id_string, id_type, typ):
        if type(input_res) is GraphEntity:
            res = input_res.res
        else:
            res = URIRef(input_res)

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
            elif str(id_type) == 'http://purl.org/spar/datacite/crossref':
                store = self.crossref_store_type_id

            if (res, id_string) in store:
                return store[(res, id_string)]

        if id_string is not None and typ != 'only_local':
            query = '''
            SELECT DISTINCT ?id WHERE {{
                <{}> <{}> ?id .
                ?id <{}> <{}> ;
                    <{}> "{}"
            }}'''.format(res, GraphEntity.has_identifier, GraphEntity.uses_identifier_scheme, id_type, GraphEntity.has_literal_value,id_string)

            return self.__query_blazegraph(query)

    def add_id_to_store(self, input_res, input_id, extracted_id, store_type_id, store_type, store, 
                        is_list=False):
        if type(input_res) is GraphEntity:
            cur_res = input_res.res
        else:
            cur_res = URIRef(input_res)

        if type(input_id) is GraphEntity:
            cur_id = input_id.res
        else:
            cur_id = URIRef(input_id)

        if cur_res is not None and cur_id is not None and extracted_id is not None:

            # Check if local store doesn't contains already the elements
            if (cur_res, extracted_id) not in store_type_id \
            and cur_res not in store_type \
            and extracted_id not in store:

                # Add it
                store_type_id[(cur_res, extracted_id)] = cur_id
                if is_list:
                    cur_list = store_type.get(cur_res)
                    if cur_list is None:
                        cur_list = []
                        store_type[cur_res] = cur_list
                    if extracted_id not in cur_list:
                        cur_list.append(extracted_id)
                else:
                    store_type[cur_res] = extracted_id
                store[extracted_id] = cur_res

    def add_doi_to_store(self, input_res, input_id, extracted_id):
        return self.add_id_to_store(input_res, input_id, extracted_id, 
                                    self.doi_store_type_id,
                                    self.doi_store_type,
                                    self.doi_store)

    def add_url_to_store(self, input_res, input_id, extracted_id):
        return self.add_id_to_store(input_res, input_id, extracted_id, 
                                    self.url_store_type_id,
                                    self.url_store_type,
                                    self.url_store)

    def add_pmid_to_store(self, input_res, input_id, extracted_id):
        return self.add_id_to_store(input_res, input_id, extracted_id,
                                    self.pmid_store_type_id,
                                    self.pmid_store_type,
                                    self.pmid_store)

    def add_pmcid_to_store(self, input_res, input_id, extracted_id):
        return self.add_id_to_store(input_res, input_id, extracted_id,
                                    self.pmcid_store_type_id,
                                    self.pmcid_store_type,
                                    self.pmcid_store)

    def add_crossref_to_store(self, input_res, input_id, extracted_id):
        return self.add_id_to_store(input_res, input_id, extracted_id, 
                                    self.crossref_store_type_id, 
                                    self.crossref_store_type, 
                                    self.crossref_store)

    def add_orcid_to_store(self, input_res, input_id, extracted_id):
        return self.add_id_to_store(input_res, input_id, extracted_id, 
                                    self.orcid_store_type_id, 
                                    self.orcid_store_type, 
                                    self.orcid_store)
    
    def add_isbn_to_store(self, input_res, input_id, extracted_id):
        return self.add_id_to_store(input_res, input_id, extracted_id, 
                                    self.isbn_store_type_id, 
                                    self.isbn_store_type, 
                                    self.isbn_store, True)
    
    def add_issn_to_store(self, input_res, input_id, extracted_id):
        return self.add_id_to_store(input_res, input_id, extracted_id, 
                                    self.issn_store_type_id, 
                                    self.issn_store_type, 
                                    self.issn_store, True)

    def add_issue_to_store(self, input_jou, volume, issue, input_id):
        if input_jou is not None and issue is not None and input_id is not None:
            if type(input_jou) is GraphEntity:
                jou_br = input_jou.res
            else:
                jou_br = URIRef(input_jou)

            if type(input_id) is GraphEntity:
                cur_id = input_id.res
            else:
                cur_id = URIRef(input_id)

            if (jou_br, volume, issue) not in self.from_issue_partof_journal:
                self.from_issue_partof_journal[(jou_br, volume, issue)] = cur_id

    def add_volume_to_store(self, input_jou, input_id, volume):
        if input_jou is not None and volume is not None and input_id is not None:
            if type(input_jou) is GraphEntity:
                jou_br = input_jou.res
            else:
                jou_br = URIRef(input_jou)

            if type(input_id) is GraphEntity:
                cur_id = input_id.res
            else:
                cur_id = URIRef(input_id)

            # Check if local store doesn't contains already the elements
            if (jou_br, volume) not in self.from_journal_volume:
                # Add it
                self.from_journal_volume[(jou_br, volume)] = cur_id

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
            elif str(id_type) == 'http://purl.org/spar/datacite/crossref':
                store = self.crossref_store

            if id_string in store:
                return store[id_string]

        # If nothing found, query blazegraph
        if typ != 'only_local':
            query = '''SELECT DISTINCT ?res WHERE {{ ?res <{}> ?id .
                ?id <{}> <{}> ;
                    <{}> "{}" .
                {}
            }}'''.format(GraphEntity.has_identifier, GraphEntity.uses_identifier_scheme, id_type,
                         GraphEntity.has_literal_value, id_string, extras)

            return self.__query(query, typ=typ)

    def __query(self, query, typ='only_blazegraph'):

        if self.ts is not None and (typ == 'both' or typ == 'only_blazegraph'):
            res = self.__query_blazegraph(query)
            if res is not None:
                return res

    def __query_blazegraph(self, query, typ=None):
        if self.ts is not None:

            if self.cache.__contains__(query):
                result = self.cache[query]
                return result
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
