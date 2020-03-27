#!/usr/bin/env python
# -*- coding: utf-8 -*-
import script.ccc.jats2oc as jats2oc
import script.ccc.conf_bee as conf
import pprint , os , csv
from script.ocdm.graphlib import *
from lxml import etree as ET


with open('evaluation.csv', mode='w',encoding='utf8') as csvfile:
    writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(['rp_string', 'pl_string', 'sentence', 'sentence_xpath', 'xml_name','status'])
    path = 'script/evaluation/bee_parser/xml_PMC_sample'
    for xml_doc in os.listdir(path):
        filename = os.fsdecode(xml_doc)
        xml_doc = os.path.join(path, filename)
        xmlp = ET.XMLParser(encoding="utf-8")
        tree = ET.parse(xml_doc, xmlp)
        root = tree.getroot()
        jats = jats2oc.Jats2OC(xml_doc)
        jats.extract_intext_refs()
        json = jats.metadata

        for pl in json:
            for rp in pl:
                rp_string = rp['rp_string'] if 'rp_string' in rp else 'in sequence'
                pl_string = rp['pl_string'] if 'pl_string' in rp else 'not in list'
                sentence_xpath = rp["context_xpath"] if "context_xpath" in rp else 'no sentence found'
                sentence = root.xpath(sentence_xpath).replace('\n','') if sentence_xpath != 'no sentence found' else 'no sentence found'
                writer.writerow([rp_string, pl_string, sentence, sentence_xpath, filename])
