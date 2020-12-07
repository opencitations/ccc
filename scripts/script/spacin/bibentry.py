from script.support.support import dict_get as dg
from script.ocdm.crossrefdatahandler import CrossrefDataHandler
from script.spacin.formatproc import FormatProcessor

__author__ = "Gabriele Pisciotta"


class Bibentry:
    def __init__(self, full_entry, repok, reperr, query_interface, resourcefinder, get_bib_entry_doi, message, do_process_entry=True):

        self.id = "Crossref"
        self.repok = repok
        self.reperr = reperr
        self.query_interface = query_interface
        self.rf = resourcefinder
        self.get_bib_entry_doi = get_bib_entry_doi
        self.message = message

        self.extracted_doi_used = False
        self.do_process_entry = do_process_entry
        self.entry = dg(full_entry, ["bibentry"])
        self.provided_doi = dg(full_entry, ["doi"])
        self.provided_pmid = dg(full_entry, ["pmid"])
        self.provided_pmcid = dg(full_entry, ["pmcid"])
        self.provided_url = dg(full_entry, ["url"])
        self.process_string = dg(full_entry, ["process_entry"])


        # Variables used to store results
        self.process_doi_result = None
        self.process_pmid_result = None
        self.process_pmcid_result = None
        self.process_url_result = None
        self.existing_bibref_entry = None
        self.extracted_doi = None
        self.extracted_url = None
        self.cur_res = None
        self.existing_res_on_blazegraph = None

        if self.process_string is not None:
            self.do_process_entry = self.process_string.lower().strip() == "true"

        if self.provided_url is not None:
            self.provided_url = FormatProcessor.extract_url(self.provided_url)
        else:
            self.extracted_url = FormatProcessor.extract_url(self.entry)

        self.extracted_doi = FormatProcessor.extract_doi(self.entry)

        # Start to query for data
        self.process_remote()


    # Run remote queries
    def process_remote(self):

        if self.provided_doi is not None:
            self._process_doi(self.provided_doi)

        if self.cur_res is None and self.entry is not None:
            self._process_entry(self.entry)

        if self.provided_pmid is not None:
            self._process_pmid(self.provided_pmid)

        if self.provided_pmcid is not None:
            self._process_pmcid(self.provided_pmcid)




    # Remote version
    def _process_doi(self, doi: str):
        existing_res = self.rf.retrieve_from_doi(doi, typ='only_blazegraph')
        if existing_res is not None:
            self.cur_res = existing_res
        else:
            self.process_doi_result = self.query_interface.get_data_crossref_doi(doi)

    # Remote version
    def _process_pmid(self, pmid: str):
        existing_res = self.rf.retrieve_from_pmid(pmid, typ='only_blazegraph')
        if existing_res is not None:
            self.cur_res = existing_res

    # Remote version
    def _process_pmcid(self, pmcid: str):
        existing_res = self.rf.retrieve_from_pmcid(pmcid, typ='only_blazegraph')
        if existing_res is not None:
            self.cur_res = existing_res

    # Remote version
    def _process_url(self, url: str):
        existing_res = self.rf.retrieve_from_url(url, typ='only_blazegraph')
        if existing_res is not None:
            self.cur_res = existing_res

    # Remote version
    def _process_entry(self, entry: str):
        if self.do_process_entry:
            self.existing_bibref_entry = self.query_interface.get_data_crossref_bibref(entry)
            if self.existing_bibref_entry is not None:
                self.cur_res = self.rf.retrieve(CrossrefDataHandler.get_ids_for_type(self.existing_bibref_entry), typ='only_blazegraph')

    # Remote version
    def process_extra_doi(self):
        if self.existing_bibref_entry is None and self.get_bib_entry_doi and self.extracted_doi is not None:
            self.extracted_doi_used = True
            self._process_doi(self.extracted_doi)