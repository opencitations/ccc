import unittest
from script.ccc.conf_spacin import reference_dir, base_iri, context_path, info_dir, triplestore_url, orcid_conf_path, \
    base_dir, temp_dir_for_rdf_loading, context_file_path, dir_split_number, items_per_file, triplestore_url_real, \
    dataset_home, reference_dir_done, reference_dir_error, interface, supplier_dir, default_dir, do_parallel, \
    sharing_dir
import json
from script.spacin.resfinder import ResourceFinder as RF_1
from script.spacin.orcidfinder import ORCIDFinder
from script.spacin.crossrefproc import CrossrefProcessor as CrossrefProcessor
import os
import tracemalloc
tracemalloc.start()
from rdflib import Graph, ConjunctiveGraph, URIRef
from script.ocdm.graphlib import GraphEntity, ProvEntity
from script.ocdm.storer import Storer
import os
from script.support.support import find_paths
from script.ccc.conf_spacin import base_iri, triplestore_url
__author__ = 'Gabriele Pisciotta'

class Test(unittest.TestCase):
    # setup query come resfinder
    def setUp(self):
        self.base_iri = base_iri
        self.ts = ConjunctiveGraph('SPARQLUpdateStore')
        self.ts.open((triplestore_url, triplestore_url))
        self.ts.namespace_manager.store.nsBindings = {}

    def test_duplicate_journal(self):
        query = """PREFIX cito: <http://purl.org/spar/cito/>
                PREFIX dcterms: <http://purl.org/dc/terms/>
                PREFIX datacite: <http://purl.org/spar/datacite/>
                PREFIX literal: <http://www.essepuntato.it/2010/06/literalreification/>
                PREFIX biro: <http://purl.org/spar/biro/>
                PREFIX frbr: <http://purl.org/vocab/frbr/core#>
                PREFIX c4o: <http://purl.org/spar/c4o/>
                PREFIX fabio: <http://purl.org/spar/fabio/>
                PREFIX prism: <http://prismstandard.org/namespaces/basic/2.0/>
                SELECT ?j1 ?j2 ?id WHERE {{
                 ?j1 datacite:hasIdentifier [
                     datacite:usesIdentifierScheme datacite:issn ;
                     literal:hasLiteralValue ?id
                 ] .
                 ?j2 datacite:hasIdentifier [
                     datacite:usesIdentifierScheme datacite:issn ;
                     literal:hasLiteralValue ?id
                 ]
                 FILTER(?j1 != ?j2)
                }} LIMIT 1"""

        found = False
        result = self.ts.query(query)
        for res in result:
            found = True
            break
        self.assertFalse(found)

    def test_duplicate_volume(self):
        query = """PREFIX cito: <http://purl.org/spar/cito/>
                    PREFIX dcterms: <http://purl.org/dc/terms/>
                    PREFIX datacite: <http://purl.org/spar/datacite/>
                    PREFIX literal: <http://www.essepuntato.it/2010/06/literalreification/>
                    PREFIX biro: <http://purl.org/spar/biro/>
                    PREFIX frbr: <http://purl.org/vocab/frbr/core#>
                    PREFIX c4o: <http://purl.org/spar/c4o/>
                    PREFIX fabio: <http://purl.org/spar/fabio/>
                    PREFIX prism: <http://prismstandard.org/namespaces/basic/2.0/>
                    SELECT ?e1 ?e2 ?id ?str WHERE {{
                      ?j datacite:hasIdentifier [
                          datacite:usesIdentifierScheme datacite:issn ;
                          literal:hasLiteralValue ?id
                      ] ;
                        ^frbr:partOf ?e1 , ?e2 .  ?e1 a fabio:JournalVolume ;
                        fabio:hasSequenceIdentifier ?str .  ?e2 a fabio:JournalVolume ;
                        fabio:hasSequenceIdentifier ?str .
                      FILTER(?e1 != ?e2)
                    }} LIMIT 1"""
        found = False
        result = self.ts.query(query)
        for res in result:
            found = True
            break
        self.assertFalse(found)


    def test_duplicate_issue(self):
        query = """PREFIX cito: <http://purl.org/spar/cito/>
                PREFIX dcterms: <http://purl.org/dc/terms/>
                PREFIX datacite: <http://purl.org/spar/datacite/>
                PREFIX literal: <http://www.essepuntato.it/2010/06/literalreification/>
                PREFIX biro: <http://purl.org/spar/biro/>
                PREFIX frbr: <http://purl.org/vocab/frbr/core#>
                PREFIX c4o: <http://purl.org/spar/c4o/>
                PREFIX fabio: <http://purl.org/spar/fabio/>
                PREFIX prism: <http://prismstandard.org/namespaces/basic/2.0/>
                SELECT ?e1 ?e2 ?id ?str WHERE {{
                  ?j datacite:hasIdentifier [
                      datacite:usesIdentifierScheme datacite:issn ;
                      literal:hasLiteralValue ?id
                  ] ;
                    ^frbr:partOf ?v .  ?v a fabio:JournalVolume ; ^frbr:partOf ?e1 , ?e2 .  ?e1 a fabio:JournalIssue ;
                    fabio:hasSequenceIdentifier ?str .  ?e2 a fabio:JournalIssue ;
                    fabio:hasSequenceIdentifier ?str .
                  FILTER(?e1 != ?e2)
                }} LIMIT 1"""
        found = False
        result = self.ts.query(query)
        for res in result:
            found = True
            break
        self.assertFalse(found)

    def test_duplicate_with_same_doi(self):
        query = """
                PREFIX cito: <http://purl.org/spar/cito/>
                PREFIX dcterms: <http://purl.org/dc/terms/>
                PREFIX datacite: <http://purl.org/spar/datacite/>
                PREFIX literal: <http://www.essepuntato.it/2010/06/literalreification/>
                PREFIX biro: <http://purl.org/spar/biro/>
                PREFIX frbr: <http://purl.org/vocab/frbr/core#>
                PREFIX c4o: <http://purl.org/spar/c4o/>
                SELECT ?e1 ?e2 ?id WHERE {{
                  ?e1 datacite:hasIdentifier [
                      datacite:usesIdentifierScheme datacite:doi ;
                      literal:hasLiteralValue ?id
                  ] .
                  ?e2 datacite:hasIdentifier [
                      datacite:usesIdentifierScheme datacite:doi ;
                      literal:hasLiteralValue ?id
                  ]
                  FILTER(?e1 != ?e2)
                }} LIMIT 1"""
        found = False
        result = self.ts.query(query)
        for res in result:
            found = True
            break
        self.assertFalse(found)

    def test_duplicate_with_same_crossref(self):
        query = """
                PREFIX cito: <http://purl.org/spar/cito/>
                PREFIX dcterms: <http://purl.org/dc/terms/>
                PREFIX datacite: <http://purl.org/spar/datacite/>
                PREFIX literal: <http://www.essepuntato.it/2010/06/literalreification/>
                PREFIX biro: <http://purl.org/spar/biro/>
                PREFIX frbr: <http://purl.org/vocab/frbr/core#>
                PREFIX c4o: <http://purl.org/spar/c4o/>
                SELECT ?e1 ?e2 ?id WHERE {{
                  ?e1 datacite:hasIdentifier [
                      datacite:usesIdentifierScheme datacite:crossref ;
                      literal:hasLiteralValue ?id
                  ] .
                  ?e2 datacite:hasIdentifier [
                      datacite:usesIdentifierScheme datacite:crossref ;
                      literal:hasLiteralValue ?id
                  ]
                  FILTER(?e1 != ?e2)
                }} LIMIT 1"""
        found = False
        result = self.ts.query(query)
        for res in result:
            found = True
            break
        self.assertFalse(found)

    def test_duplicate_with_same_orcid(self):
        query = """
                PREFIX cito: <http://purl.org/spar/cito/>
                PREFIX dcterms: <http://purl.org/dc/terms/>
                PREFIX datacite: <http://purl.org/spar/datacite/>
                PREFIX literal: <http://www.essepuntato.it/2010/06/literalreification/>
                PREFIX biro: <http://purl.org/spar/biro/>
                PREFIX frbr: <http://purl.org/vocab/frbr/core#>
                PREFIX c4o: <http://purl.org/spar/c4o/>
                SELECT ?e1 ?e2 ?id WHERE {{
                  ?e1 datacite:hasIdentifier [
                      datacite:usesIdentifierScheme datacite:orcid ;
                      literal:hasLiteralValue ?id
                  ] .
                  ?e2 datacite:hasIdentifier [
                      datacite:usesIdentifierScheme datacite:orcid ;
                      literal:hasLiteralValue ?id
                  ]
                  FILTER(?e1 != ?e2)
                }} LIMIT 1"""
        found = False
        result = self.ts.query(query)
        for res in result:
            found = True
            break
        self.assertFalse(found)

    def test_duplicate_with_same_isbn(self):
        query = """
                PREFIX cito: <http://purl.org/spar/cito/>
                PREFIX dcterms: <http://purl.org/dc/terms/>
                PREFIX datacite: <http://purl.org/spar/datacite/>
                PREFIX literal: <http://www.essepuntato.it/2010/06/literalreification/>
                PREFIX biro: <http://purl.org/spar/biro/>
                PREFIX frbr: <http://purl.org/vocab/frbr/core#>
                PREFIX c4o: <http://purl.org/spar/c4o/>
                SELECT ?e1 ?e2 ?id WHERE {{
                  ?e1 datacite:hasIdentifier [
                      datacite:usesIdentifierScheme datacite:isbn ;
                      literal:hasLiteralValue ?id
                  ] .
                  ?e2 datacite:hasIdentifier [
                      datacite:usesIdentifierScheme datacite:isbn ;
                      literal:hasLiteralValue ?id
                  ]
                  FILTER(?e1 != ?e2)
                }} LIMIT 1"""
        found = False
        result = self.ts.query(query)
        for res in result:
            found = True
            break
        self.assertFalse(found)

    def test_duplicate_with_same_issn(self):
        query = """
                PREFIX cito: <http://purl.org/spar/cito/>
                PREFIX dcterms: <http://purl.org/dc/terms/>
                PREFIX datacite: <http://purl.org/spar/datacite/>
                PREFIX literal: <http://www.essepuntato.it/2010/06/literalreification/>
                PREFIX biro: <http://purl.org/spar/biro/>
                PREFIX frbr: <http://purl.org/vocab/frbr/core#>
                PREFIX c4o: <http://purl.org/spar/c4o/>
                SELECT ?e1 ?e2 ?id WHERE {{
                  ?e1 datacite:hasIdentifier [
                      datacite:usesIdentifierScheme datacite:issn ;
                      literal:hasLiteralValue ?id
                  ] .
                  ?e2 datacite:hasIdentifier [
                      datacite:usesIdentifierScheme datacite:issn ;
                      literal:hasLiteralValue ?id
                  ]
                  FILTER(?e1 != ?e2)
                }} LIMIT 1"""
        found = False
        result = self.ts.query(query)
        for res in result:
            found = True
            break
        self.assertFalse(found)

    def test_duplicate_with_same_pmid(self):
        query = """
                        PREFIX cito: <http://purl.org/spar/cito/>
                        PREFIX dcterms: <http://purl.org/dc/terms/>
                        PREFIX datacite: <http://purl.org/spar/datacite/>
                        PREFIX literal: <http://www.essepuntato.it/2010/06/literalreification/>
                        PREFIX biro: <http://purl.org/spar/biro/>
                        PREFIX frbr: <http://purl.org/vocab/frbr/core#>
                        PREFIX c4o: <http://purl.org/spar/c4o/>
                        SELECT ?e1 ?e2 ?id WHERE {{
                          ?e1 datacite:hasIdentifier [
                              datacite:usesIdentifierScheme datacite:pmid ;
                              literal:hasLiteralValue ?id
                          ] .
                          ?e2 datacite:hasIdentifier [
                              datacite:usesIdentifierScheme datacite:pmid ;
                              literal:hasLiteralValue ?id
                          ]
                          FILTER(?e1 != ?e2)
                        }} LIMIT 1"""
        found = False
        result = self.ts.query(query)
        for res in result:
            found = True
            break
        self.assertFalse(found)

    def test_duplicate_with_same_pmcid(self):
        query = """
                                PREFIX cito: <http://purl.org/spar/cito/>
                                PREFIX dcterms: <http://purl.org/dc/terms/>
                                PREFIX datacite: <http://purl.org/spar/datacite/>
                                PREFIX literal: <http://www.essepuntato.it/2010/06/literalreification/>
                                PREFIX biro: <http://purl.org/spar/biro/>
                                PREFIX frbr: <http://purl.org/vocab/frbr/core#>
                                PREFIX c4o: <http://purl.org/spar/c4o/>
                                SELECT ?e1 ?e2 ?id WHERE {{
                                  ?e1 datacite:hasIdentifier [
                                      datacite:usesIdentifierScheme datacite:pmcid ;
                                      literal:hasLiteralValue ?id
                                  ] .
                                  ?e2 datacite:hasIdentifier [
                                      datacite:usesIdentifierScheme datacite:pmcid ;
                                      literal:hasLiteralValue ?id
                                  ]
                                  FILTER(?e1 != ?e2)
                                }} LIMIT 1"""
        found = False
        result = self.ts.query(query)
        for res in result:
            found = True
            break
        self.assertFalse(found)

    def test_duplicate_with_same_oci(self):
        query = """
                                PREFIX cito: <http://purl.org/spar/cito/>
                                PREFIX dcterms: <http://purl.org/dc/terms/>
                                PREFIX datacite: <http://purl.org/spar/datacite/>
                                PREFIX literal: <http://www.essepuntato.it/2010/06/literalreification/>
                                PREFIX biro: <http://purl.org/spar/biro/>
                                PREFIX frbr: <http://purl.org/vocab/frbr/core#>
                                PREFIX c4o: <http://purl.org/spar/c4o/>
                                SELECT ?e1 ?e2 ?id WHERE {{
                                  ?e1 datacite:hasIdentifier [
                                      datacite:usesIdentifierScheme datacite:oci ;
                                      literal:hasLiteralValue ?id
                                  ] .
                                  ?e2 datacite:hasIdentifier [
                                      datacite:usesIdentifierScheme datacite:oci ;
                                      literal:hasLiteralValue ?id
                                  ]
                                  FILTER(?e1 != ?e2)
                                }} LIMIT 1"""
        found = False
        result = self.ts.query(query)
        for res in result:
            found = True
            break
        self.assertFalse(found)

    def test_duplicate_with_same_intrepid(self):
        query = """
                                PREFIX cito: <http://purl.org/spar/cito/>
                                PREFIX dcterms: <http://purl.org/dc/terms/>
                                PREFIX datacite: <http://purl.org/spar/datacite/>
                                PREFIX literal: <http://www.essepuntato.it/2010/06/literalreification/>
                                PREFIX biro: <http://purl.org/spar/biro/>
                                PREFIX frbr: <http://purl.org/vocab/frbr/core#>
                                PREFIX c4o: <http://purl.org/spar/c4o/>
                                SELECT ?e1 ?e2 ?id WHERE {{
                                  ?e1 datacite:hasIdentifier [
                                      datacite:usesIdentifierScheme datacite:intrepid ;
                                      literal:hasLiteralValue ?id
                                  ] .
                                  ?e2 datacite:hasIdentifier [
                                      datacite:usesIdentifierScheme datacite:intrepid ;
                                      literal:hasLiteralValue ?id
                                  ]
                                  FILTER(?e1 != ?e2)
                                }} LIMIT 1"""
        found = False
        result = self.ts.query(query)
        for res in result:
            found = True
            break
        self.assertFalse(found)

    def test_duplicate_anything(self):
        query = """
                                        PREFIX cito: <http://purl.org/spar/cito/>
                                        PREFIX dcterms: <http://purl.org/dc/terms/>
                                        PREFIX datacite: <http://purl.org/spar/datacite/>
                                        PREFIX literal: <http://www.essepuntato.it/2010/06/literalreification/>
                                        PREFIX biro: <http://purl.org/spar/biro/>
                                        PREFIX frbr: <http://purl.org/vocab/frbr/core#>
                                        PREFIX c4o: <http://purl.org/spar/c4o/>
                                        SELECT ?e1 ?e2 ?id WHERE {{
                                          ?e1 datacite:hasIdentifier [
                                              datacite:usesIdentifierScheme ?x ;
                                              literal:hasLiteralValue ?id
                                          ] .
                                          ?e2 datacite:hasIdentifier [
                                              datacite:usesIdentifierScheme ?x ;
                                              literal:hasLiteralValue ?id
                                          ]
                                          FILTER(?e1 != ?e2) .
                                          FILTER(?x != datacite:local-resource-identifier-scheme)

                                        }} LIMIT 1"""
        found = False
        result = self.ts.query(query)
        for res in result:
            found = True
            break
        self.assertFalse(found)

    def test_book_has_things(self):
        pass

    def test_bookchapter_has_things(self):
        pass

    def test_bookchapter_is_part_of_book(self):
        query = """SELECT ?s WHERE
                {{
                    ?s a <http://purl.org/spar/fabio/BookChapter> .
                     FILTER NOT EXISTS {{ ?s <http://purl.org/vocab/frbr/core#partOf> ?x .
                                        ?x a <http://purl.org/spar/fabio/Book>.
                    }}
                }} LIMIT 1
                            """
        found = False
        result = self.ts.query(query)
        for res in result:
            found = True
            break
        self.assertFalse(found)

    def test_volume_is_part_of_journal(self):
        query = """SELECT ?s WHERE {{
                    ?s a <http://purl.org/spar/fabio/JournalVolume> .
                    FILTER NOT EXISTS {{ 
                      ?s <http://purl.org/vocab/frbr/core#partOf> ?x .
                      ?x a <http://purl.org/spar/fabio/Journal> . }}
                    }} LIMIT 1
                    """
        found = False
        result = self.ts.query(query)
        for res in result:
            found = True
            break
        self.assertFalse(found)

    def test_journal_volume_without_incoming_link(self):
        query = """SELECT ?s WHERE {{
                    ?s a <http://purl.org/spar/fabio/JournalVolume> .
                    FILTER NOT EXISTS {{ 
                        ?x <http://purl.org/vocab/frbr/core#partOf> ?s . 
                        }}
                    }}
                    """
        found = False
        result = self.ts.query(query)
        for res in result:
            found = True
            break
        self.assertFalse(found)

    def test_issues_without_incoming_link(self):
        query = """SELECT ?s WHERE
                {{
                    ?s a <http://purl.org/spar/fabio/JournalIssue> .
                    FILTER NOT EXISTS {{ ?x <http://purl.org/vocab/frbr/core#partOf> ?s . }}
                }}"""
        found = False
        result = self.ts.query(query)
        for res in result:
            found = True
            break
        self.assertFalse(found)

    def test_journal_without_incoming_link(self):
        query = """SELECT ?s WHERE {{
              ?s a <http://purl.org/spar/fabio/Journal> .
              FILTER NOT EXISTS {{ ?x <http://purl.org/vocab/frbr/core#partOf> ?s . }}
            }}"""
        found = False
        result = self.ts.query(query)
        for res in result:
            found = True
            break
        self.assertFalse(found)

    def test_volume_is_part_of_something(self):
        query = """SELECT ?s WHERE
                {{
                    ?s a <http://purl.org/spar/fabio/JournalVolume> .
                     FILTER NOT EXISTS {{ ?s <http://purl.org/vocab/frbr/core#partOf> ?x . }}
                }}"""
        found = False
        result = self.ts.query(query)
        for res in result:
            found = True
            break
        self.assertFalse(found)

    def test_issue_is_part_of_something(self):
        query = """SELECT ?s WHERE
                {{
                    ?s a <http://purl.org/spar/fabio/JournaleIssue> .
                     FILTER NOT EXISTS {{ ?s <http://purl.org/vocab/frbr/core#partOf> ?x . }}
                }}"""
        found = False
        result = self.ts.query(query)
        for res in result:
            found = True
            break
        self.assertFalse(found)

    def test_book_is_part_of_bookchapter(self):
        query = """SELECT ?s WHERE
                    {{
                        ?s a <http://purl.org/spar/fabio/BookChapter> .
                         FILTER NOT EXISTS {{ ?s <http://purl.org/vocab/frbr/core#partOf> ?x . }}
                    }}"""
        found = False
        result = self.ts.query(query)
        for res in result:
            found = True
            break
        self.assertFalse(found)

    def test_book_without_incoming_link(self):
        query = """SELECT ?s WHERE
                    {{
                        ?s a <http://purl.org/spar/fabio/Book> .
                         FILTER NOT EXISTS {{ ?x <http://purl.org/spar/cito/cites> ?s . }}
                    }} LIMIT 1"""
        found = False
        result = self.ts.query(query)
        for res in result:
            found = True
            break
        self.assertFalse(found)


    #############
    ############
    def test_duplicate_doi(self):
        query = """
                PREFIX cito: <http://purl.org/spar/cito/>
                PREFIX dcterms: <http://purl.org/dc/terms/>
                PREFIX datacite: <http://purl.org/spar/datacite/>
                PREFIX literal: <http://www.essepuntato.it/2010/06/literalreification/>
                PREFIX biro: <http://purl.org/spar/biro/>
                PREFIX frbr: <http://purl.org/vocab/frbr/core#>
                PREFIX c4o: <http://purl.org/spar/c4o/>
                SELECT ?e1 ?e2 ?id WHERE {{
                  ?e1 datacite:usesIdentifierScheme datacite:doi ;
                      literal:hasLiteralValue ?id .
                  ?e2 datacite:usesIdentifierScheme datacite:doi ;
                      literal:hasLiteralValue ?id .
                  FILTER(?e1 != ?e2)
                }} LIMIT 1"""
        found = False
        result = self.ts.query(query)
        for res in result:
            found = True
            break
        self.assertFalse(found)

    def test_duplicate_crossref(self):
        query = """
                PREFIX cito: <http://purl.org/spar/cito/>
                PREFIX dcterms: <http://purl.org/dc/terms/>
                PREFIX datacite: <http://purl.org/spar/datacite/>
                PREFIX literal: <http://www.essepuntato.it/2010/06/literalreification/>
                PREFIX biro: <http://purl.org/spar/biro/>
                PREFIX frbr: <http://purl.org/vocab/frbr/core#>
                PREFIX c4o: <http://purl.org/spar/c4o/>
                SELECT ?e1 ?e2 ?id WHERE {{
                  ?e1 datacite:usesIdentifierScheme datacite:crossref ;
                      literal:hasLiteralValue ?id .
                  ?e2 datacite:usesIdentifierScheme datacite:crossref ;
                      literal:hasLiteralValue ?id .
                  FILTER(?e1 != ?e2)
                }} LIMIT 1"""
        found = False
        result = self.ts.query(query)
        for res in result:
            found = True
            break
        self.assertFalse(found)

    def test_duplicate_orcid(self):
        query = """
                PREFIX cito: <http://purl.org/spar/cito/>
                PREFIX dcterms: <http://purl.org/dc/terms/>
                PREFIX datacite: <http://purl.org/spar/datacite/>
                PREFIX literal: <http://www.essepuntato.it/2010/06/literalreification/>
                PREFIX biro: <http://purl.org/spar/biro/>
                PREFIX frbr: <http://purl.org/vocab/frbr/core#>
                PREFIX c4o: <http://purl.org/spar/c4o/>
                SELECT ?e1 ?e2 ?id WHERE {{
                  ?e1 datacite:usesIdentifierScheme datacite:orcid ;
                      literal:hasLiteralValue ?id .
                  ?e2 datacite:usesIdentifierScheme datacite:orcid;
                      literal:hasLiteralValue ?id .
                  FILTER(?e1 != ?e2)
                }} LIMIT 1"""
        found = False
        result = self.ts.query(query)
        for res in result:
            found = True
            break
        self.assertFalse(found)

    def test_duplicate_isbn(self):
        query = """
                PREFIX cito: <http://purl.org/spar/cito/>
                PREFIX dcterms: <http://purl.org/dc/terms/>
                PREFIX datacite: <http://purl.org/spar/datacite/>
                PREFIX literal: <http://www.essepuntato.it/2010/06/literalreification/>
                PREFIX biro: <http://purl.org/spar/biro/>
                PREFIX frbr: <http://purl.org/vocab/frbr/core#>
                PREFIX c4o: <http://purl.org/spar/c4o/>
                SELECT ?e1 ?e2 ?id WHERE {{
                    ?e1 datacite:usesIdentifierScheme datacite:isbn ;
                      literal:hasLiteralValue ?id .
                    ?e2 datacite:usesIdentifierScheme datacite:isbn ;
                      literal:hasLiteralValue ?id .
                  FILTER(?e1 != ?e2)
                }} LIMIT 1"""
        found = False
        result = self.ts.query(query)
        for res in result:
            found = True
            break
        self.assertFalse(found)

    def test_duplicate_issn(self):
        query = """
                PREFIX cito: <http://purl.org/spar/cito/>
                PREFIX dcterms: <http://purl.org/dc/terms/>
                PREFIX datacite: <http://purl.org/spar/datacite/>
                PREFIX literal: <http://www.essepuntato.it/2010/06/literalreification/>
                PREFIX biro: <http://purl.org/spar/biro/>
                PREFIX frbr: <http://purl.org/vocab/frbr/core#>
                PREFIX c4o: <http://purl.org/spar/c4o/>
                SELECT ?e1 ?e2 ?id WHERE {{
                  ?e1 datacite:usesIdentifierScheme datacite:issn ;
                      literal:hasLiteralValue ?id .
                  ?e2 datacite:usesIdentifierScheme datacite:issn ;
                      literal:hasLiteralValue ?id .
                  FILTER(?e1 != ?e2)
                }} LIMIT 1"""
        found = False
        result = self.ts.query(query)
        for res in result:
            found = True
            break
        self.assertFalse(found)

    def test_duplicate_pmid(self):
        query = """
                        PREFIX cito: <http://purl.org/spar/cito/>
                        PREFIX dcterms: <http://purl.org/dc/terms/>
                        PREFIX datacite: <http://purl.org/spar/datacite/>
                        PREFIX literal: <http://www.essepuntato.it/2010/06/literalreification/>
                        PREFIX biro: <http://purl.org/spar/biro/>
                        PREFIX frbr: <http://purl.org/vocab/frbr/core#>
                        PREFIX c4o: <http://purl.org/spar/c4o/>
                        SELECT ?e1 ?e2 ?id WHERE {{
                            ?e1 datacite:usesIdentifierScheme datacite:pmid ;
                                literal:hasLiteralValue ?id .
                            ?e2 datacite:usesIdentifierScheme datacite:pmid ;
                                literal:hasLiteralValue ?id .
                          FILTER(?e1 != ?e2)
                        }} LIMIT 1"""
        found = False
        result = self.ts.query(query)
        for res in result:
            found = True
            break
        self.assertFalse(found)

    def test_duplicate_pmcid(self):
        query = """
                        PREFIX cito: <http://purl.org/spar/cito/>
                        PREFIX dcterms: <http://purl.org/dc/terms/>
                        PREFIX datacite: <http://purl.org/spar/datacite/>
                        PREFIX literal: <http://www.essepuntato.it/2010/06/literalreification/>
                        PREFIX biro: <http://purl.org/spar/biro/>
                        PREFIX frbr: <http://purl.org/vocab/frbr/core#>
                        PREFIX c4o: <http://purl.org/spar/c4o/>
                        SELECT ?e1 ?e2 ?id WHERE {{
                            ?e1 datacite:usesIdentifierScheme datacite:pmcid ;
                                literal:hasLiteralValue ?id .
                            ?e2 datacite:usesIdentifierScheme datacite:pmcid ;
                                literal:hasLiteralValue ?id .
                          FILTER(?e1 != ?e2)
                        }} LIMIT 1"""
        found = False
        result = self.ts.query(query)
        for res in result:
            found = True
            break
        self.assertFalse(found)

    def test_duplicate_oci(self):
        query = """
                        PREFIX cito: <http://purl.org/spar/cito/>
                        PREFIX dcterms: <http://purl.org/dc/terms/>
                        PREFIX datacite: <http://purl.org/spar/datacite/>
                        PREFIX literal: <http://www.essepuntato.it/2010/06/literalreification/>
                        PREFIX biro: <http://purl.org/spar/biro/>
                        PREFIX frbr: <http://purl.org/vocab/frbr/core#>
                        PREFIX c4o: <http://purl.org/spar/c4o/>
                        SELECT ?e1 ?e2 ?id WHERE {{
                            ?e1 datacite:usesIdentifierScheme datacite:oci ;
                                literal:hasLiteralValue ?id .
                            ?e2 datacite:usesIdentifierScheme datacite:oci ;
                                literal:hasLiteralValue ?id .
                          FILTER(?e1 != ?e2)
                        }} LIMIT 1"""
        found = False
        result = self.ts.query(query)
        for res in result:
            found = True
            break
        self.assertFalse(found)

    def test_duplicate_intrepid(self):
        query = """
                        PREFIX cito: <http://purl.org/spar/cito/>
                        PREFIX dcterms: <http://purl.org/dc/terms/>
                        PREFIX datacite: <http://purl.org/spar/datacite/>
                        PREFIX literal: <http://www.essepuntato.it/2010/06/literalreification/>
                        PREFIX biro: <http://purl.org/spar/biro/>
                        PREFIX frbr: <http://purl.org/vocab/frbr/core#>
                        PREFIX c4o: <http://purl.org/spar/c4o/>
                        SELECT ?e1 ?e2 ?id WHERE {{
                            ?e1 datacite:usesIdentifierScheme datacite:intrepid ;
                                literal:hasLiteralValue ?id .
                            ?e2 datacite:usesIdentifierScheme datacite:intrepid ;
                                literal:hasLiteralValue ?id .
                          FILTER(?e1 != ?e2)
                        }} LIMIT 1"""
        found = False
        result = self.ts.query(query)
        for res in result:
            found = True
            break
        self.assertFalse(found)

    def test_journals_have_identifier(self):
        query = """PREFIX cito: <http://purl.org/spar/cito/>
                PREFIX dcterms: <http://purl.org/dc/terms/>
                PREFIX datacite: <http://purl.org/spar/datacite/>
                PREFIX literal: <http://www.essepuntato.it/2010/06/literalreification/>
                PREFIX biro: <http://purl.org/spar/biro/>
                PREFIX frbr: <http://purl.org/vocab/frbr/core#>
                PREFIX c4o: <http://purl.org/spar/c4o/>
                PREFIX fabio: <http://purl.org/spar/fabio/>
                PREFIX prism: <http://prismstandard.org/namespaces/basic/2.0/>
                SELECT ?j1 WHERE {{
                 ?j1 a fabio:Journal .
                 FILTER NOT EXISTS { ?j1 <http://purl.org/spar/datacite/hasIdentifier> ?x }
                }} LIMIT 1"""
        found = False
        result = self.ts.query(query)
        for res in result:
            found = True
            break
        self.assertFalse(found)

    def test_books_have_identifier(self):
        query = """PREFIX cito: <http://purl.org/spar/cito/>
                PREFIX dcterms: <http://purl.org/dc/terms/>
                PREFIX datacite: <http://purl.org/spar/datacite/>
                PREFIX literal: <http://www.essepuntato.it/2010/06/literalreification/>
                PREFIX biro: <http://purl.org/spar/biro/>
                PREFIX frbr: <http://purl.org/vocab/frbr/core#>
                PREFIX c4o: <http://purl.org/spar/c4o/>
                PREFIX fabio: <http://purl.org/spar/fabio/>
                PREFIX prism: <http://prismstandard.org/namespaces/basic/2.0/>
                SELECT ?j1  WHERE {{
                 ?j1 a fabio:Book .
                 FILTER NOT EXISTS { ?j1 <http://purl.org/spar/datacite/hasIdentifier> ?x }
                }} LIMIT 1"""
        found = False
        result = self.ts.query(query)
        for res in result:
            found = True
            break
        self.assertFalse(found)