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

__author__ = 'essepuntato'

from script.spacin.orcidfinder import ORCIDFinder
import unittest
import os


class SupportTest(unittest.TestCase):

    def setUp(self):
        self.TEST_DIR = os.path.dirname(os.path.abspath(__file__))

    def test_get_orcid_records_remote(self):
        oc = ORCIDFinder(os.path.join(self.TEST_DIR, '..', 'orcid_conf.json'), query_interface='remote')
        names = ["Peroni"]
        doi = "10.3233/DS-170012"
        orcid = "0000-0003-0530-4305"
        items = oc.get_orcid_ids(doi, names)
        self.assertEqual(len(items), 1)
        self.assertIn(orcid, items[0]["orcid"])

    def  test_get_orcid_records_local(self):
        oc = ORCIDFinder(os.path.join(self.TEST_DIR, '..', 'orcid_conf.json'), query_interface='local')
        names = ["Peroni"]
        doi = "10.3233/DS-170012"
        orcid = "0000-0003-0530-4305"
        items = oc.get_orcid_ids(doi, names)
        self.assertEqual(len(items), 1)
        self.assertIn(orcid, items[0]["orcid"])
        self.assertEquals("Silvio", items[0]["given"])
        self.assertEquals("Peroni", items[0]["family"])

if __name__ == '__main__':
    unittest.main()
