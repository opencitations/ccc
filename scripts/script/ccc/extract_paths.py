#!/usr/bin/env python
# -*- coding: utf-8 -*-
import script.ccc.conf_bee as conf
import uuid , itertools , os , pprint ,re , string , glob
from lxml import etree as ET
from itertools import groupby
from collections import defaultdict, Counter
from nltk.tokenize.punkt import PunktSentenceTokenizer, PunktParameters

from script.spacin.formatproc import FormatProcessor
from script.ocdm.graphlib import *
from script.ocdm.conf import context_path as context_path


pp = pprint.PrettyPrinter(indent=1)
parents,children = set(),set()
for xml_doc in glob.iglob('dump_oa_bulk_pmc/comm_use.A-B.xml/' + '**/*.nxml', recursive=True):
    #for xml_doc in glob.iglob('dump_oa_bulk_pmc/comm_use.A-B.xml/3_Biotech/*.nxml'):
    root = ET.parse(xml_doc).getroot()
    for xref in root.findall('.//xref[@rid]'):
        for par in xref.getparent():
            parents.add(par.tag)
        for chil in xref.iter():
            children.add(chil.tag)
print(parents, '\n', children)
