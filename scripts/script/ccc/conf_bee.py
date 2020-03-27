#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os , re
from script.ocdm.graphlib import GraphEntity

# ABBREVIATIONS FOR SENTENCE TOKENIZER
abbreviations_list_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'Abbreviations.txt'))
#escape_xpath = ["\u2000","\u2001","\u2002","\u2003","\u2004","\u2005","\u2006","\u2007","\u2008","\u2009","\u200A"]
escape_xpath = ["\u205f×\u205f"]
false_endings = ['etal.','etal.(','etal.[','etal(','etal[','Fig.','Figs.','ref.']
list_separators = [('[', ']'), ('[',']') , ('(', ')'), ('[',']')]
rp_separators_in_list = [','.encode('utf-8'), '\u2013'.encode('utf-8'), '\u002D'.encode('utf-8'), ';'.encode('utf-8'), '-','–',',',',','–'] # first lists separator, second sequences separator

# XPATH
rp_path = './/xref[@rid = //ref/@id]'
rp_tail = '/following-sibling::text()[1]'
rp_closest_parent = '/ancestor::*[1]'
rp_child = '/child::*[1]'
citing_doi = './/article-id[@pub-id-type="doi"]'

# XML elements mapped to the OC model
section_tag = 'sec'
caption_tag = 'caption'
title_tag = 'title'
table_tag = 'table'
notes_tag = 'notes'
footnote_tag = 'fn'
paragraph_tag = 'p'
be_tag = 'ref'

# other XML elements
front_tag = 'front'
back_tag = 'back'

parent_elements_names = [notes_tag, section_tag, caption_tag, title_tag, table_tag, footnote_tag, paragraph_tag, 'tr','td','th','bold','italic','attrib']

# mapping to OCDM (graphlib) bibliographic entities
elem_mapping = [(caption_tag,GraphEntity.caption),\
				(paragraph_tag,GraphEntity.paragraph),\
				(table_tag,GraphEntity.table),\
				(footnote_tag,GraphEntity.footnote),\
				(notes_tag,GraphEntity.footnote),\
				(title_tag,GraphEntity.section_title),\
				(section_tag,GraphEntity.section)]
