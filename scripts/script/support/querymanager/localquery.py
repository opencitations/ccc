from .queryinterface import QueryInterface
from time import sleep
import requests
import sys
import json
from requests.exceptions import ReadTimeout, ConnectTimeout
import pysolr

__author__ = 'Gabriele Pisciotta'

class LocalQuery(QueryInterface):

    def __init__(self,
                 max_iteration,
                 sec_to_wait,
                 timeout,
                 repok,
                 reper,
                 is_json=True):
        self.max_iteration = max_iteration
        self.sec_to_wait = sec_to_wait
        self.timeout = timeout
        self.repok = repok
        self.reper = reper
        self.is_json = is_json

        # change these urls according to the local instance of Solr
        self.__crossref_url = 'http://localhost:8983/solr/crossref_without_metadata'
        self.__orcid_url = 'http://localhost:8983/solr/orcid'

        self.crossref_query_instance = pysolr.Solr(self.__crossref_url, always_commit=True, timeout=100)
        self.orcid_query_instance = pysolr.Solr(self.__orcid_url, always_commit=True, timeout=100)

    def get_data_crossref_doi(self, entity):
        query = 'id:"{}"'.format(entity)
        results = self.crossref_query_instance.search(fl='*,score', q=query)

        if len(results) < 1:
            self.reper.add_sentence("[LocalQuery - Crossref] Error with: `{}`".format(entity))
            return None
        else:
            return results

    def get_data_crossref_bibref(self, entity):
        query = 'bibref:({})'.format(entity)
        results = self.crossref_query_instance.search(fl='*,score', q=query)

        if len(results) < 1:
            self.reper.add_sentence("[LocalQuery - Crossref] Error with: `{}`".format(entity))
            return None
        else:
            return results

    def get_data_orcid(self, entity):
        get_url = self.__personal_url % entity
        return self.__get_data(get_url)

    def get_records_orcid(self, entity):
        get_url = self.__orcid_api_url + entity
        return self.__get_data(get_url)
