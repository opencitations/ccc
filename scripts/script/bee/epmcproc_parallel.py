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
import uuid
from script.bee.refproc import ReferenceProcessor
from script.ccc.jats2oc import Jats2OC
from script.support.support import get_data, encode_url
from script.support.support import dict_get as dg
import os
from datetime import datetime
import re
from lxml import etree
import pandas as pd
import json
import time
import threading

__author__ = "Gabriele Pisciotta"

def run_in_thread(fn):
    def run(*k, **kw):
        t = threading.Thread(target=fn, args=k, kwargs=kw)
        t.start()
        return t
    return run


class EuropeanPubMedCentralProcessor(ReferenceProcessor):
    def __init__(self,
                 stored_file,
                 reference_dir,
                 error_dir,
                 pagination_file,
                 stopper,
                 headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10; "
                                        "rv:33.0) Gecko/20100101 Firefox/33.0"},
                 sec_to_wait=10,
                 max_iteration=6,
                 timeout=30,
                 max_query_per_sec=10,
                 p_size=1000,
                 debug=True,
                 intext_refs=False,
                 supplier_idx=()):
        if p_size > 1000 or p_size < 1:
            page_size = "1000"
        else:
            page_size = str(p_size)
        self.provider = "Europe PubMed Central"
        self.all_papers_api = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=" \
                              "has_reflist:y+sort_date:y&resulttype=lite&pageSize=%s&format=json" \
                              "&cursorMark=" % page_size
        self.ref_list_api = "https://www.ebi.ac.uk/europepmc/webservices/rest/XXX/YYY/references/" \
                            "1/1000/json"
        self.paper_api = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?resulttype=lite&" \
                         "format=json&query="
        self.xml_source_api = "https://www.ebi.ac.uk/europepmc/webservices/rest/XXX/fullTextXML"
        self.open_access_api = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=" \
                               "open_access:y+sort_date:y&resulttype=lite&pageSize=%s&format=json" \
                               "&cursorMark=" % page_size
        self.pagination_file = pagination_file
        self.max_query_per_sec = max_query_per_sec
        self.query_count = 1
        self.sec_threshold = None
        self.article_ids = {}

        self.__last_xml_source = None

        super(EuropeanPubMedCentralProcessor, self).__init__(
            stored_file, reference_dir, error_dir, stopper, headers, sec_to_wait,
            max_iteration, timeout, debug, supplier_idx)


    #@run_in_thread
    def process_article(self, paper, oa=False, intext_refs=False):
        cur_source = "MED"
        cur_doi = paper["cur_doi"]
        cur_pmid = int(paper["cur_pmid"])
        cur_pmcid = paper["cur_pmcid"]
        cur_name = paper["cur_name"]

        if cur_pmid != 0:
            cur_id = "PMID{}".format(cur_pmid)
        elif cur_pmcid != 0:
            cur_id = "{}".format(cur_pmcid)
        elif cur_doi is not None and cur_doi != "":
            cur_id = "DOI{}".format(cur_doi)
        else:
            self.repok.add_sentence("No id for this paper")
            return

        references = json.loads(paper["references"])

        cur_localid = "{}-{}".format(cur_source, cur_id)
        id_list = [str(cur_doi), str(cur_pmid), str(cur_pmid), cur_localid]

        if not self.rs.is_any_stored(id_list):

            self.repok.new_article()
            self.repok.add_sentence("Processing article with local id {}".format(cur_localid))

            if oa and not intext_refs:
                ref_list_url, ref_list, ref_pointer_list = self.process_xml_source(cur_pmid, cur_name, cur_doi, references, intext_refs=False)
            elif oa and intext_refs:
                ref_list_url, ref_list, ref_pointer_list = self.process_xml_source(cur_pmid, cur_name, cur_doi, references, intext_refs=True)
            #else:
            #    ref_list_url = self.process_references(cur_source, cur_id)

            if ref_list_url is not None:
                if cur_pmid == 0 or cur_pmid is None:
                    cur_pmid = ""
                if cur_pmcid == 0 or cur_pmid is None:
                    cur_pmcid = ""


                json_item = {}
                json_item["references"] = ref_list
                if cur_localid != "":
                    json_item["localid"] =  cur_id
                if cur_doi != "" and cur_doi != "nan" and cur_doi is not None:
                    json_item["doi"] = str(cur_doi)
                if cur_pmid != "" and cur_pmid != "0" and cur_pmid is not None:
                    json_item["pmid"] = str(cur_pmid)
                if cur_pmcid != "" and cur_pmcid != "0" and cur_pmcid is not None:
                    json_item["pmcid"] = str(cur_pmcid)
                if self.name is not None:
                    json_item["curator"] = str(self.name)
                if self.provider is not None:
                    json_item["source_provider"] = str(self.provider)
                if encode_url(ref_list_url) is not None:
                    json_item["source"] = str(encode_url(ref_list_url))
                if len(ref_pointer_list):
                    json_item["reference_pointers"] = ref_pointer_list

                cur_time = datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f_')
                local_file_name = str(uuid.uuid4()) + ".json"
                local_dir_name = self.rs.new_supplier() +   re.sub("^([0-9]+-[0-9]+-[0-9]+-[0-9]+).+$", "\\1", cur_time)

                new_dir_path = self.rs.ref_dir + os.sep + local_dir_name
                new_file_path = new_dir_path + os.sep + local_file_name

                if not os.path.exists(new_dir_path):
                    os.makedirs(new_dir_path)
                try:
                    with open(new_file_path, "w") as f:
                        json.dump(json_item, f, indent=4, ensure_ascii=False)
                        if cur_localid not in self.rs.stored:
                            with open(self.rs.csv_file, "a") as name_f:
                                name_f.write(cur_localid + "\n")
                                self.rs.stored.add(cur_localid)
                                return True
                except Exception as e:
                    print(e, "\n\n", json_item, "\n\n")

            else:
                self.reper.add_sentence(
                    "The article '%s' has no references or its PubMed Central "
                    "ID is not defined." % cur_localid)
        else:
            self.repok.add_sentence("The article '%s' has been already stored." % cur_localid)


    def process(self,
                dataset,
                oa=False,
                intext_refs=False,
                articles_path='/mie/europepmc.org/ftp/oa/articles/'):
        try:
            self.articles_path = articles_path
            self.df = dataset

            self.df['cur_pmid'] = self.df['cur_pmid'].fillna(0)
            self.df['cur_pmcid'] = self.df['cur_pmcid'].fillna(0)

            #self.df['cur_pmid'] = self.df['cur_pmid'].astype(int)
            #self.df['cur_pmcid'] = self.df['cur_pmcid'].astype(int)

            s = time.time()

            for _, paper in self.df.iterrows():
                if self.stopper.can_proceed():
                    self.process_article(paper, oa, intext_refs)
                else:
                    print("Stopping")
                    break

            e = time.time()
            t = (e-s)
            timefordoc = t/len(self.df)

            print("Time elapsed: {},\n amount of time for a single doc: {}".format(t, timefordoc))
            return self.stopper.can_proceed()
        except Exception as e:
            print("Exception: {}".format(e.with_traceback()))



    def process_xml_source(self, cur_pmid, cur_name, cur_doi=None, references=None, intext_refs=False):
        xml_source_url = None
        ref_list = []
        ref_pointer_list = []
        if cur_pmid is not None and cur_name is not None:
            xml_source_url = self.xml_source_api.replace("XXX", str(cur_pmid))

            if len(references):

                for idx, reference in enumerate(references):
                    if "entry_text" in reference:
                        entry_text = reference["entry_text"]
                        process_entry_text = True
                    else:
                        entry_text = None
                        process_entry_text = False

                    if cur_doi is not None and 'ref_doi' in reference and reference['ref_doi'] is not None and cur_doi == reference['ref_doi']:
                        pass
                    else:
                        returned_reference = {}

                        if entry_text is not None:
                            returned_reference["bibentry"] = entry_text
                            returned_reference["process_entry"] = str(process_entry_text)
                        #if local_id is not None:
                        #    returned_reference["localid"] = str(string_local_id)
                        if 'ref_doi' in reference and reference['ref_doi'] != "":
                            returned_reference["doi"] = str(reference['ref_doi'])
                        if 'ref_pmid' in reference and reference['ref_pmid'] != "":
                            returned_reference["pmid"] = str(reference['ref_pmid'])
                        if 'ref_pmcid' in reference and reference['ref_pmcid'] != "":
                            returned_reference["pmcid"] = str(reference['ref_pmcid'])
                        if 'ref_url' in reference and reference['ref_url'] != "":
                            returned_reference["url"] = str(reference['ref_url'])
                        if 'ref_xmlid' in reference and reference['ref_xmlid'] is not None:
                            returned_reference["xmlid"] = str(reference['ref_xmlid'])

                        ref_list += [returned_reference]


                try:
                    with open(os.path.join(self.articles_path, cur_name), 'r') as xml_source:

                        cur_xml = etree.fromstring(xml_source.read())
                        reference_pointers = cur_xml.xpath("//xref[@rid = //ref/@id]")

                        if intext_refs and len(reference_pointers):
                            #self.rs.new_ref_pointer_list() # create empty list
                            jats = Jats2OC(cur_xml) # add result to self.ref_pointer_list
                            refs = jats.extract_intext_refs()

                            if refs is not None:
                                for x in refs:
                                    ref_pointer_list.append(x)
                                    #self.rs.ref_pointer_list.append(x)
                except Exception as e:
                    ref_pointer_list = []
                    with open('exceptions.log', 'a') as exceptionslog:
                        exceptionslog.write("\n--\n{}".format(e))
                    print("Exception with Jats! " + e)


        return xml_source_url, ref_list, ref_pointer_list # now we return the ref_list, because isn't stored anymore in RS

