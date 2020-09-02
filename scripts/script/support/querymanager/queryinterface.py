from abc import ABC, abstractmethod

class QueryInterface(ABC):

    @abstractmethod
    def get_data_crossref(self, entity):
        raise NotImplementedError

    @abstractmethod
    def get_data_orcid(self, entity):
        raise NotImplementedError

    @abstractmethod
    def get_records_orcid(self, entity):
        raise NotImplementedError
