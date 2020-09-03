from . queryinterface import QueryInterface
from time import sleep
import requests
import sys
import json
from requests.exceptions import ReadTimeout, ConnectTimeout
__author__ = 'Gabriele Pisciotta'

class RemoteQuery(QueryInterface):

    def __init__(self,
                 max_iteration,
                 sec_to_wait,
                 headers,
                 timeout,
                 repok,
                 reper,
                 is_json=True):
        self.max_iteration = max_iteration
        self.sec_to_wait = sec_to_wait
        self.headers = headers
        self.timeout = timeout
        self.repok = repok
        self.reper = reper
        self.is_json = is_json
        self.__crossref_url = 'https://api.crossref.org/works?query.bibliographic='
        self.__orcid_api_url = 'https://pub.orcid.org/v2.1/search?q='
        self.__personal_url = "https://pub.orcid.org/v2.1/%s/personal-details"

    def get_data_crossref_doi(self, entity):
        return self.__get_data(entity)

    def get_data_crossref_bibref(self, entity):
        return self.__get_data(entity)

    def get_data_orcid(self, entity):
        get_url = self.__personal_url % entity
        return self.__get_data(get_url)

    def get_records_orcid(self, entity):
        get_url = self.__orcid_api_url + entity
        return self.__get_data(get_url)

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
        self.reper.add_sentence(" | ".join(errors) + "\n\tRequested URL: " + get_url)