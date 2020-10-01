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

import json
import argparse
from script.support.reporter import Reporter
from script.support.support import dict_get as dg
from script.support.support import dict_add as da
from script.support.support import normalise_ascii as na
from script.support.queryinterface import LocalQuery, RemoteQuery

from urllib.parse import quote


class ORCIDFinder(object):
    __api_url = "https://pub.orcid.org/v2.1/search?q="
    __personal_url = "https://pub.orcid.org/v2.1/%s/personal-details"

    def __init__(self, conf_file, sec_to_wait=10, max_iteration=6, timeout=30, query_interface= 'remote'):
        with open(conf_file) as f:
            conf_json = json.load(f)
            self.headers = {
                "Authorization": "Bearer %s" % conf_json["access_token"],
                "Content-Type": "application/json"
            }
            self.id = "ORCID"
            self.name = "SPACIN " + self.__class__.__name__
            self.repok = Reporter(prefix="[%s - INFO] " % self.name)
            self.reper = Reporter(prefix="[%s - ERROR] " % self.name)
            self.__last_query_done = None
            self.sec_to_wait = sec_to_wait
            self.max_iteration = max_iteration
            self.timeout = timeout

            if query_interface == 'local':
                self.query_interface = LocalQuery(reperr=self.reper,
                                                  repok=self.repok)
            elif query_interface == 'remote':
                self.query_interface = RemoteQuery(max_iteration=max_iteration,
                                                   sec_to_wait=sec_to_wait,
                                                   timeout=timeout,
                                                   headers=self.headers,
                                                   reperr=self.reper,
                                                   repok=self.repok,
                                                   is_json=True)
            else:
                raise ValueError("query_interface param must be `local` or `remote`")

    def get_last_query(self):
        return self.__last_query_done

    def get_orcid_data(self, orcid_string):
        self.repok.new_article()
        self.reper.new_article()
        self.__last_query_done = ORCIDFinder.__personal_url % orcid_string
        print(self.__last_query_done)
        return self.query_interface.get_orcid_data(orcid_string)

    def get_orcid_records(self, doi_string, family_names=[]):
        self.repok.new_article()
        self.reper.new_article()

        # If we're making a local query, we only need to use the doi string
        if isinstance(self.query_interface, LocalQuery):
            return self.query_interface.get_orcid_records(doi_string.lower())

        # Otherwise we need to setup the query in ther format that follows
        else:
            cur_query = "doi-self:\"%s\"" % doi_string
            doi_string_l = doi_string.lower()
            doi_string_u = doi_string.upper()
            if doi_string_l != doi_string or doi_string_u != doi_string:
                cur_query = "(" + cur_query
                if doi_string_l != doi_string:
                    cur_query += " OR doi-self:\"%s\"" % doi_string_l
                if doi_string_u != doi_string:
                    cur_query += " OR doi-self:\"%s\"" % doi_string_u
                cur_query += ")"

            if family_names:
                cur_query += " AND ("
                first_name = True
                for idx, family_name in enumerate(family_names):
                    if family_name is not None:
                        if first_name:
                            first_name = False
                        else:
                            cur_query += " OR "
                        cur_query += "family-name:\"%s\"" % na("" + family_name)

                cur_query += ")"

            self.__last_query_done = ORCIDFinder.__api_url + quote(cur_query)

            returned_data = self.query_interface.get_orcid_records(quote(cur_query))
            return returned_data

    def get_orcid_ids(self, doi_string, family_names=[]):
        result = []
        records = self.get_orcid_records(doi_string, family_names)
        if records is not None:
            if isinstance(self.query_interface, RemoteQuery):
                for orcid_id in dg(records, ["result", "orcid-identifier", "path"]):
                    personal_details = self.get_orcid_data(orcid_id)
                    if personal_details is not None:
                        given_name = dg(personal_details, ["name", "given-names", "value"])
                        family_name = dg(personal_details, ["name", "family-name", "value"])
                        credit_name = dg(personal_details, ["name", "credit-name", "value"])
                        other_names = dg(personal_details, ["other-names", "other-name", "content"])
                        result += [da({
                            "orcid": orcid_id,
                            "given": given_name,
                            "family": family_name,
                            "credit": credit_name,
                            "other": other_names
                        })]
            else:
                for author in records:
                    result += [da({
                        "orcid": author['orcid'],
                        "given": author['given_names'],
                        "family": author['family_name'],
                        "credit": "", # actually we don't manage this
                        "other": ""# actually we don't manage this
                    })]

        return result


# Main
if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser("orcidfinder.py")
    arg_parser.add_argument("-c", "--conf", metavar="file_path", dest="c", required=True,
                            help="The configuration file to access the ORCID API.")
    arg_parser.add_argument("-d", "--doi", dest="doi", required=True,
                            help="The DOI of the paper to look for.")
    arg_parser.add_argument("-n", "--family_names", metavar="name", type=str, nargs="+", dest="n",
                            help="The family names of the possible authors of the paper "
                                 "indicated by the DOI.")
    args = arg_parser.parse_args()

    of = ORCIDFinder(args.c)
    print(json.dumps(of.get_orcid_ids(args.doi, args.n), indent=4, ensure_ascii=False))

