from abc import ABC, abstractmethod

__author__ = 'Gabriele Pisciotta'

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
