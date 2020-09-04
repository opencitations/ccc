from abc import ABC, abstractmethod
__author__ = 'Gabriele Pisciotta'
import pysolr
from requests.exceptions import ReadTimeout, ConnectTimeout
import json
from time import sleep
import requests
import sys
from netifaces import ifaddresses, AF_INET
import re

class QueryInterface(ABC):

    @abstractmethod
    def get_data_crossref_doi(self, entity):
        raise NotImplementedError

    @abstractmethod
    def get_data_crossref_bibref(self, entity):
        raise NotImplementedError

    @abstractmethod
    def get_data_orcid(self, entity):
        raise NotImplementedError

    @abstractmethod
    def get_records_orcid(self, entity):
        raise NotImplementedError

class LocalQuery(QueryInterface):

    def __init__(self, reper = None, repok = None):
        self.reper = reper
        self.repok = repok

        # change these urls according to the local instance of Solr
        self.__crossref_url = 'http://localhost:8983/solr/crossref_without_metadata'
        self.__orcid_url = 'http://localhost:8983/solr/orcid'

        self.crossref_query_instance = pysolr.Solr(self.__crossref_url, always_commit=True, timeout=100)
        self.orcid_query_instance = pysolr.Solr(self.__orcid_url, always_commit=True, timeout=100)

    def get_data_crossref_doi(self, entity):
        query = 'id:"{}"'.format(entity)
        results = self.crossref_query_instance.search(fl='*,score', q=query)

        if len(results) < 1:
            if self.reper is not None:
                self.reper.add_sentence("[LocalQuery - Crossref] Error with: `{}`".format(entity))
            return None
        else:
            return [json.loads(str(r['original'][0]).replace("'", '"')) for r in results]

    def get_data_crossref_bibref(self, entity):
        entity = ' '.join(item for item in entity.split() if not (item.startswith('https://') and len(item) > 7))
        entity = ' '.join(item for item in entity.split() if not (item.startswith('http://') and len(item) > 7))
        entity = entity.replace("et al.", "")
        entity = entity.replace("Available at:", "")
        entity = re.sub('\W+', ' ', entity)
        entity = entity.strip()
        print(entity)
        query = 'bibref:({})'.format(entity)
        results = self.crossref_query_instance.search(fl='*,score', q=query)

        if len(results) < 1:
            if self.reper is not None:
                self.reper.add_sentence("[LocalQuery - Crossref] Error with: `{}`".format(entity))
            return None
        else:

            # This is a temporary code form in order to run on my local machine
            # where the `original` field has been added only for a few amount of docs

            toreturn = []
            for r in results:
                if 'original' in r:
                    toreturn.append(json.loads(r['original'][0]))


            return toreturn

    def get_data_orcid(self, entity):
        get_url = self.__personal_url % entity
        return self.__get_data(get_url)

    def get_records_orcid(self, entity):
        get_url = self.__orcid_api_url + entity
        return self.__get_data(get_url)

class RemoteQuery(QueryInterface):

    def __init__(self,
                max_iteration=6,
                sec_to_wait = 10,
                headers = {"User-Agent": "SPACIN / CrossrefProcessor (via OpenCitations - http://opencitations.net; "
                                         "mailto:contact@opencitations.net)"},
                timeout=30,
                repok = None,
                reper = None,
                is_json = True):

        self.max_iteration = max_iteration
        self.sec_to_wait = sec_to_wait
        self.headers = headers
        self.timeout = timeout
        self.repok = repok
        self.reper = reper
        self.is_json = is_json

        self.__crossref_doi_url = 'https://api.crossref.org/works/'
        self.__crossref_entry_url = 'https://api.crossref.org/works?query.bibliographic='
        self.__orcid_api_url = 'https://pub.orcid.org/v2.1/search?q='
        self.__personal_url = "https://pub.orcid.org/v2.1/%s/personal-details"

    def get_data_crossref_doi(self, entity):
        return self.__get_data(self.__crossref_doi_url + entity)

    def get_data_crossref_bibref(self, entity):
        return self.__get_data(self.__crossref_entry_url + entity)

    def get_data_orcid(self, entity):
        return self.__get_data(self.__personal_url % entity)

    def get_records_orcid(self, entity):
        return self.__get_data(self.__orcid_api_url + entity)

    def __get_data(self, get_url):
        tentative = 0
        error_no_200 = False
        error_read = False
        error_connection = False
        error_generic = False
        errors = []
        while tentative < self.max_iteration:
            if tentative != 0:
                sleep(self.sec_to_wait)
            tentative += 1

            try:
                response = requests.get(get_url, headers=self.headers, timeout=self.timeout)
                if response.status_code == 200:
                    if self.repok is not None:
                        self.repok.add_sentence("Data retrieved from '%s'." % get_url)
                    if self.is_json:
                        return json.loads(response.text)
                    else:
                        return response.text
                else:
                    err_string = "We got an HTTP error when retrieving data (HTTP status code: %s)." % \
                                 str(response.status_code)
                    if not error_no_200:
                        error_no_200 = True
                    if response.status_code == 404:
                        if self.repok is not None:
                            self.repok.add_sentence(err_string + " However, the process could continue anyway.")
                        # If the resource has not found, we can break the process immediately,
                        # by returning None so as to allow the callee to continue (or not) the process
                        return None
                    else:
                        errors += [err_string]

            except ReadTimeout as e:
                if not error_read:
                    error_read = True
                    errors += ["A timeout error happened when reading results from the API "
                               "when retrieving data. %s" % e]
            except ConnectTimeout as e:
                if not error_connection:
                    error_connection = True
                    errors += ["A timeout error happened when connecting to the API "
                               "when retrieving data. %s" % e]
            except Exception as e:
                if not error_generic:
                    error_generic = True
                    errors += ["A generic error happened when trying to use the API "
                               "when retrieving data. %s" % sys.exc_info()[0]]

        # If the process comes here, no valid result has been returned
        if self.reper is not None:
            self.reper.add_sentence(" | ".join(errors) + "\n\tRequested URL: " + get_url)
