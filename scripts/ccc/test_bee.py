#!/usr/bin/env python
# -*- coding: utf-8 -*-
import script.ccc.jats2oc as jats2oc
import script.ccc.conf_bee as conf
import pprint , os , csv
from script.ocdm.graphlib import *
from lxml import etree as ET

# test
pp = pprint.PrettyPrinter(indent=1)
xml_doc = 'script/ccc/xml_PMC_sample/36test.xml'

jats = jats2oc.Jats2OC(xml_doc)
jats.extract_intext_refs()
pp.pprint(jats.metadata)
