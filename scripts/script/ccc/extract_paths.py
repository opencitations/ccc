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
text,children = list(),set()
#for xml_doc in glob.glob(os.path.abspath(os.getcwd()) + 'comm_use/**/*.nxml', recursive=True):
PATH = os.path.dirname(os.path.realpath(__file__))
for path, dirs, files in os.walk(PATH):
    for filename in files:
        if 'nxml' in filename:
            xml_doc = os.path.join(path, filename)
            print(filename)
            #for xml_doc in glob.iglob('dump_oa_bulk_pmc/comm_use.A-B.xml/3_Biotech/*.nxml'):
            root = ET.parse(xml_doc).getroot()
            # for xref in root.findall('.//xref[@rid]'):
            #     for par in xref.getparent():
            #         parents.add(par.tag)
            #     for chil in xref.iter():
            #         children.add(chil.tag)
            for body in root.findall(".//body"):
                text_par = ([root.text] if root.text else []) + [child.tail for child in root]
                text.append(text_par)
                print(text_par)
                for child in body:
                    children.add(child.tag)

pp.pprint(children)
pp.pprint(text)
