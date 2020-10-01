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
        if g_set is not None:
            self.update_graph_set(g_set)
        if ts_url is None:
            self.ts = None
        else:
            self.ts = ConjunctiveGraph('SPARQLUpdateStore')
            self.ts.open((ts_url, ts_url))
            self.ts.namespace_manager.store.nsBindings = {}

        self.doi_store = {}
        self.orcid_store = {}
        self.pmid_store = {}
        self.pmcid_store = {}
        self.url_store = {}
        self.issn_store = {}
        self.isbn_store = {}

        self.doi_store_citing = {}
        self.orcid_store_citing = {}
        self.pmid_store_citing = {}
        self.pmcid_store_citing = {}
        self.url_store_citing = {}
        self.issn_store_citing = {}
        self.isbn_store_citing = {}

        # Used in __retrieve_res_id_string() when you query for the {res}_{type} and want to get ids literal values
        self.doi_store_type = {}
        self.orcid_store_type = {}
        self.pmid_store_type = {}
        self.pmcid_store_type = {}
        self.url_store_type = {}
        self.issn_store_type = {}
        self.isbn_store_type = {}

        # Used in __retrieve_res_id_by_type() res_type_idstring when you query for the {res}_{type}_{id_literal} and
        # want to get id's URI
        self.doi_store_type_id = {}
        self.orcid_store_type_id = {}
        self.pmid_store_type_id = {}
        self.pmcid_store_type_id = {}
        self.url_store_type_id = {}
        self.issn_store_type_id = {}
        self.isbn_store_type_id = {}

        # Used in __retrieve_from_journal() where you query for {id_type}_{id_string}_{part_type}_{part_seq_id} and get the res
        self.from_journal = {}

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
                    self.add_triples_in_graph(cur_g)

    def add_triples_in_graph(self, g):
        if g is not None:
            for s, p, o in g.triples((None, None, None)):
                self.g.add((s, p, o))

    def update_graph_set(self, g_set):
        for g in g_set.graphs()[self.index_for_graph_set:]:
            self.add_triples_in_graph(g)
            self.index_for_graph_set += 1

    def retrieve(self, id_dict):
        for id_type in id_dict:
            for id_string in id_dict[id_type]:
                res = self.__id_with_type(id_string, id_type)
                if res is not None:
                    return res

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

    def retrieve_from_orcid(self, string):
        return self.__id_with_type(string, GraphEntity.orcid)

    def retrieve_modification_date(self, res_iri):
        query = f"""
                SELECT DISTINCT ?res WHERE {{
                    <{res_iri}> ^<{ProvEntity.specialization_of}> ?snapshot .
                    FILTER NOT EXISTS {{ ?snapshop <{ProvEntity.invalidated_at_time}> ?inv_date }}
                    ?snapshop <{ProvEntity.generated_at_time}> ?res
                }}"""
        return self.__query(query)

    def retrieve_entity(self, string, type):
        query = f"""
                SELECT DISTINCT ?res WHERE {{
                    BIND(iri("{string}") as ?res) .
                    ?res a <{str(type)}>
                }}"""
        return self.__query(query)

    def retrieve_citing_from_doi(self, string):
        return self.__id_with_type(
            string.lower(), GraphEntity.doi, "?res <%s> ?cited" % GraphEntity.cites)

    def retrieve_citing_from_pmid(self, string):
        return self.__id_with_type(
            string, GraphEntity.pmid, "?res <%s> ?cited" % GraphEntity.cites)

    def retrieve_citing_from_pmcid(self, string):
        return self.__id_with_type(
            string, GraphEntity.pmcid, "?res <%s> ?cited" % GraphEntity.cites)

    def retrieve_citing_from_url(self, string):
        return self.__id_with_type(
            string.lower(), GraphEntity.url, "?res <%s> ?cited" % GraphEntity.cites)

    def retrieve_from_doi(self, string):
        return self.__id_with_type(string.lower(), GraphEntity.doi)

    def retrieve_from_pmid(self, string):
        return self.__id_with_type(string, GraphEntity.pmid)

    def retrieve_from_pmcid(self, string):
        return self.__id_with_type(string, GraphEntity.pmcid)

    def retrieve_from_url(self, string):
        return self.__id_with_type(string.lower(), GraphEntity.url)

    def retrieve_from_issn(self, string):
        return self.__id_with_type(string, GraphEntity.issn)

    def retrieve_from_isbn(self, string):
        return self.__id_with_type(string, GraphEntity.isbn)

    def retrieve_issue_from_journal(self, id_dict, issue_id, volume_id):
        if volume_id is None:
            return self.__retrieve_from_journal(id_dict, GraphEntity.journal_issue, issue_id)
        else:
            retrieved_volume = self.retrieve_volume_from_journal(id_dict, volume_id)
            if retrieved_volume is not None:
                query = f"""
                    SELECT DISTINCT ?br WHERE {{
                        ?br a <{GraphEntity.journal_issue}> ;
                            <{GraphEntity.part_of}> <{str(retrieved_volume)}> ;
                            <{GraphEntity.has_sequence_identifier}> "{issue_id}"
                    }} LIMIT 1
                """
                return self.__query_blazegraph(query)

    def retrieve_volume_from_journal(self, id_dict, volume_id):
        return self.__retrieve_from_journal(id_dict, GraphEntity.journal_volume, volume_id)

    def retrieve_url_string(self, res):
        return self.__retrieve_res_id_string(res, GraphEntity.url)

    def retrieve_doi_string(self, res):
        return self.__retrieve_res_id_string(res, GraphEntity.doi)

    def retrieve_pmid_string(self, res):
        return self.__retrieve_res_id_string(res, GraphEntity.pmid)

    def retrieve_pmcid_string(self, res):
        return self.__retrieve_res_id_string(res, GraphEntity.pmcid)

    def retrieve_br_url(self, res, string):
        return self.__retrieve_res_id_by_type(res, string.lower(), GraphEntity.url)

    def retrieve_br_doi(self, res, string):
        return self.__retrieve_res_id_by_type(res, string.lower(), GraphEntity.doi)

    def retrieve_br_pmid(self, res, string):
        return self.__retrieve_res_id_by_type(res, string, GraphEntity.pmid)

    def retrieve_br_pmcid(self, res, string):
        return self.__retrieve_res_id_by_type(res, string, GraphEntity.pmcid)

    def retrieve_last_snapshot(self, prov_subj):
        query = f'''
            SELECT DISTINCT ?se WHERE {{
                ?se <{ProvEntity.specialization_of}> <{str(prov_subj)}> .
                FILTER NOT EXISTS {{?se <{ProvEntity.was_invalidated_by}> ?ca }}
            }} LIMIT 1
        '''
        return self.__query_blazegraph(query)

    def __retrieve_res_id_string(self, res, id_type):

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
        if store.__contains__(f'{res}_{type}'):
            return store[f'{res}_{type}']

        query = f'''
        SELECT DISTINCT ?id WHERE {{
            <{res}> <{GraphEntity.has_identifier}> [
                <{GraphEntity.uses_identifier_scheme}> <{id_type}> ;
                <{GraphEntity.has_literal_value}> ?id
            ]
        }}'''
        return self.__query_blazegraph(query)

    def __retrieve_res_id_by_type(self, res, id_string, id_type):

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
        if store.__contains__(f'{res}_{type}_{id_string}'):
            return store[f'{res}_{type}_{id_string}']

        if id_string is not None:
            query = f'''
            SELECT DISTINCT ?id WHERE {{
                <{res}> <{GraphEntity.has_identifier}> ?id .
                ?id <{GraphEntity.uses_identifier_scheme}> <{id_type}> ;
                    <{GraphEntity.has_literal_value}> "{id_string}"
            }}'''

            return self.__query_blazegraph(query)

    def __retrieve_from_journal(self, id_dict, part_type, part_seq_id):
        # Check locally
        for id_type in id_dict:
            for id_string in id_dict[id_type]:
                if self.from_journal.__contains__(f'{id_type}_{id_string}_{part_type}_{part_seq_id}'):
                    return self.from_journal[f'{id_type}_{id_string}_{part_type}_{part_seq_id}']

        # If not present, check in blazegraph
        for id_type in id_dict:
            for id_string in id_dict[id_type]:
                query = f'''
                SELECT DISTINCT ?res WHERE {{
                    ?j <{GraphEntity.has_identifier}> ?id .
                    ?id
                        <{GraphEntity.uses_identifier_scheme}> <{id_type}> ;
                        <{GraphEntity.has_literal_value}> "{id_string}" .
                    ?res a <{part_type}> ;
                        <{GraphEntity.part_of}>+ ?j ;
                        <{GraphEntity.has_sequence_identifier}> "{part_seq_id}"
                }}'''
                return self.__query_blazegraph(query)


    def __id_with_type(self, id_string, id_type, extras=""):
        """This method is called when we need to get the resource having a certain identifier. It first check locally
        if something has already been stored and then check on the blazegraph instance"""

        # First check if locally there's something
        if id_type is not None and id is not None:
            if str(id_type) == 'http://purl.org/spar/datacite/url':
                store = self.url_store if extras == "" else self.url_store_citing
            elif str(id_type) == 'http://purl.org/spar/datacite/doi':
                store = self.doi_store if extras == "" else self.doi_store_citing
            elif str(id_type) == 'http://purl.org/spar/datacite/orcid':
                store = self.orcid_store if extras == "" else self.orcid_store_citing
            elif str(id_type) == 'http://purl.org/spar/datacite/pmid':
                store = self.pmid_store if extras == "" else self.pmid_store_citing
            elif str(id_type) == 'http://purl.org/spar/datacite/pmcid':
                store = self.pmcid_store if extras == "" else self.pmcid_store_citing
            elif str(id_type) == 'http://purl.org/spar/datacite/issn':
                store = self.issn_store if extras == "" else self.issn_store_citing
            elif str(id_type) == 'http://purl.org/spar/datacite/isbn':
                store = self.isbn_store if extras == "" else self.isbn_store_citing
        if store.__contains__(id_string):
            return store[id_string]

        # If nothing found, query blazegraph
        query = f'''SELECT DISTINCT ?res WHERE {{ ?res <{GraphEntity.has_identifier}> ?id .
            ?id <{GraphEntity.uses_identifier_scheme}> <{id_type}> ;
                <{GraphEntity.has_literal_value}> "{id_string}" .
            {extras}
        }}'''
        return self.__query_blazegraph(query)



    def __query(self, query, id_string=None, id_type=None):
        """
        if self.ts is not None:
            result = self.ts.query(query)
            for res, in result:
                return res

        # If nothing has been returned, check if there is something
        # in the current graph set
        result = self.g.query(query)
        for res, in result:
            return res
        """
        res = self.__query_local(query, id_string, id_type)
        if res is not None:
            return res
        elif self.ts is not None:
            res = self.__query_blazegraph(query)
            if res is not None:
                return res

    def __query_blazegraph(self, query):
        if self.ts is not None:
            result = self.ts.query(query)
            for res, in result:
                return res

    def __query_local(self, query, id_string=None, id_type=None):
        result = self.g.query(query)
        for res, in result:
            print(f"Found {res}")
            return res

