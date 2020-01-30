#!/usr/bin/env python
# -*- coding: utf-8 -*-
import script.ccc.conf_bee as conf
import uuid , itertools , os , pprint ,re , string
from lxml import etree as ET
from itertools import groupby
from collections import defaultdict, Counter
from nltk.tokenize.punkt import PunktSentenceTokenizer, PunktParameters

from script.spacin.formatproc import FormatProcessor
from script.ocdm.graphlib import *
from script.ocdm.conf import context_path as context_path


pp = pprint.PrettyPrinter(indent=1)
class Jats2OC(object):

	def __init__(self, xml_doc): # xml_doc is root
		#self.xml_doc = xml_doc
		self.root = xml_doc
		self.xmlp = ET.XMLParser(encoding="utf-8")
		#self.tree = ET.parse(xml_doc, self.xmlp) # comm for run.py
		#self.root = self.tree.getroot() # comm for run.py
		self.et = ET.ElementTree(self.root)


	def extract_intext_refs(self):
		"""process a XML file and return a list of lists of dictionaries"""
		self.metadata = []
		rp_list = Jats2OC.preprocess_xref(self.root, self.et) # list of xref

		# 1. pl in parent element
		parent_pl_set = list({ (rp["xml_element"].getparent(), self.et.getpath(rp["xml_element"].getparent()) ) \
			for rp in rp_list if rp["xml_element"].getparent().tag not in conf.parent_elements_names})

		for parent_el, parent_el_path in parent_pl_set: # sup w/ comma or dash separated xref [TEST 4]
			pl_string = ET.tostring(parent_el, method="text", encoding='unicode', with_tail=False).strip().replace('\n','')
			pl_xpath = self.et.getpath(parent_el)
			context_xpath = Jats2OC.xpath_sentence(parent_el, self.root, conf.abbreviations_list_path, None)
			containers_title = Jats2OC.find_container_title(parent_el, conf.section_tag, self.root)
			parent_el_list = Jats2OC.parent_pl(self.root, pl_string, pl_xpath, context_xpath, containers_title, parent_el, rp_list)[0]
			rp_list = Jats2OC.parent_pl(self.root, pl_string, pl_xpath, context_xpath, containers_title, parent_el, rp_list)[1]
			self.metadata.append(parent_el_list)

		# 2. pl in xref (already found)
		pl_set = {rp["pl_xpath"] for rp in rp_list if "pl_xpath" in rp.keys()}
		pl_dict = {pl : [rp for rp in rp_list if "pl_xpath" in rp.keys() and rp["pl_xpath"] == pl] for pl in pl_set}
		for pl, pl_list in pl_dict.items():
			self.metadata.append(pl_list)
			rp_list = [rp for rp in rp_list if 'pl_xpath' not in rp.keys() or ("pl_xpath" in rp.keys() and rp["pl_xpath"] != pl)]


		# 3. pl in separators
		sentences_set = {rp["context_xpath"] for rp in rp_list}
		sentences_dict = {sent : [rp for rp in rp_list if rp["context_xpath"] == sent] for sent in sentences_set}
		all_groups = []

		for sent, xref_list in sentences_dict.items():
			if len(xref_list) == 1: # only one rp in sentence (do not care about separator)
				Jats2OC.add_rp_in_sentence(self.metadata, xref_list, rp_list)

			if len(xref_list) > 1: # rp and pl in sentence
				xref_in_sent = [rp["rp_xpath"] for rp in xref_list if "rp_xpath" in rp.keys()]
				# tail in text or in sup
				tails = []
				for xref in xref_in_sent:
					if self.root.xpath('/'+xref+'/following-sibling::*[1][contains(text(), ",")]'):
						tails.append(self.root.xpath('/'+xref+'/following-sibling::*[1]/text()')[0])
					else:
						if len(self.root.xpath('/'+xref+conf.rp_tail)) != 0:
							tails.append(self.root.xpath('/'+xref+conf.rp_tail)[0])
						else:
							tails.append('')

				#tails = [self.root.xpath('/'+xref+conf.rp_tail)[0] if self.root.xpath('/'+xref+conf.rp_tail) else '' for xref in xref_in_sent]

				end_separator = Jats2OC.rp_end_separator(tails) # includes also end_separator = ''
				if len(end_separator) != 0 and end_separator[0][0] not in list(string.ascii_letters) and end_separator[0][0] not in list(string.digits): # separators
					context = []
					for xref in xref_in_sent:
						# look for in-list separators in sibling elements
						if self.root.xpath('/'+xref+'/following-sibling::*[1][contains(text(), ",")]'): # include <sup>,</sup>
							context.append(Jats2OC.clean_list(self.root.xpath('/'+xref+'| /'+xref+'/following-sibling::*[1]/text()')))
						else:
							# force end of list when there is an in-list separator and a text longer than 30 characters
							# so as to reduce mistakes in parsing lists with inconsistent markup
							xref_elem = self.root.xpath(xref)[0]
							if xref_elem.tail and len(xref_elem.tail) < 20:
								context.append(Jats2OC.clean_list(self.root.xpath('/'+xref)))
								context.append(Jats2OC.clean_list(self.root.xpath('/'+xref+conf.rp_tail)))
							else:
								context.append(Jats2OC.clean_list(self.root.xpath('/'+xref)))
								if end_separator[0][0] and end_separator[0][0] != '':
									context.append(end_separator[0][0])
								elif end_separator[0][0] == '':
									context.append('E')

					# FIX? when there is (xref;xref) but the second xref is not @ref-type='bibr'
					# it creates a list and includes the first following rp in sentence if exists (otherwise single rp)
					context = [y for x in context for y in x]
					context = [x if x != 'E' else '' for x in context] # replace fake separator with empty string because cannot append it

					rp_and_separator = [Jats2OC.clean(elem).decode('utf-8') if isinstance(elem, str) else elem for elem in context] # list of rp and separator
					rp_groups = [list(x[1]) for x in groupby(rp_and_separator, lambda x: x==end_separator[0][0]) if not x[0]] # group rp by separator
					rp_groups_and_types = Jats2OC.add_group_type(rp_groups)
					groups = [list(i for i in j if i not in conf.rp_separators_in_list) for j in rp_groups_and_types] # remove separators
					Jats2OC.add_rp_and_pl_in_sentence(self.root, self.et, self.metadata, groups, rp_list, end_separator)

				else: # no separator / weird separators / the worst case scenario
					groups = Jats2OC.handle_no_separators(self.root, xref_in_sent)[0]
					lonely = Jats2OC.handle_no_separators(self.root, xref_in_sent)[1]

					if len(groups) != 0:
						all_groups.append(groups)
					if len(lonely) != 0:
						all_groups.append(lonely)

		# 4. no separator, weird internal separators
		sublists = [Jats2OC.sublist(group) for group in all_groups]
		rp_dictionaries = []
		for group_in_sent in sublists:
			for group_list in group_in_sent:
				rp_dict = [rp for rp in rp_list for tup in group_list if ("rp_xpath" in rp.keys() and rp["rp_xpath"] == tup[1]) or ("pl_xpath" in rp.keys() and rp["pl_xpath"] == tup[1]) ]
				rp_dictionaries.append(rp_dict)

		# add pl_xpath/string to groups missing it
		for rp_d in rp_dictionaries:
			rp_d = Jats2OC.add_pl_info(rp_d, self.root) if len(rp_d) > 1 else rp_d
			self.metadata.append(rp_d)

		# sort rp in incremental order
		self.metadata = sorted(self.metadata, key=lambda rp : rp[0]["n_rp"])

		# remove useless key:value pairs
		for group in self.metadata:
			for rp in group:
				rp.pop("n_rp", None)
				rp.pop("xml_element", None)

		return self.metadata


	#########################
	#### METHODS FOR XML ####
	#########################


	@staticmethod
	def preprocess_xref(root, et):
		n_rp = 100 # start from 100 to include floating numbers (corresponding to rp extracted from sequences in post process)
		rp_list = []
		for xref in root.xpath(conf.rp_path):
			n_rp += 100
			xref_id = xref.get('rid')
			xref_text = xref.text if xref.text else ET.tostring(xref, method="text", encoding='unicode', with_tail=False)
			rp_string = xref_text.strip().replace('\n','') if xref.text else xref_text.strip().replace('\n','')
			rp_xpath = et.getpath(xref)
			parent = None if xref.getparent().tag in conf.parent_elements_names else xref.getparent().tag
			context_xpath = Jats2OC.xpath_sentence(xref, root, conf.abbreviations_list_path, parent)
			containers_title = Jats2OC.find_container_title(xref, conf.section_tag, root)
			pl_string , pl_xpath = None , None
			char_before = re.sub(r"\s+", "", "".join(Jats2OC.get_text_before(xref)))[-1] if len(re.sub(r"\s+", "", "".join(Jats2OC.get_text_before(xref)))) != 0 else None
			char_after = re.sub(r"\s+", "", "".join(Jats2OC.get_text_after(xref)))[0] if len(re.sub(r"\s+", "", "".join(Jats2OC.get_text_after(xref)))) != 0 else None
			if char_before and char_after and (char_before == conf.list_separators[1][0] or char_before == conf.list_separators[2][0]) \
				and ( char_after == conf.list_separators[1][1] or char_after == conf.list_separators[2][1]):
				rp_string = char_before+rp_string+char_after
			if len(list(xref)) == 0: # no children
				seq = xref_text.encode('utf-8').split('\u2013'.encode('utf-8'))
				if len(seq) == 2 and Jats2OC.num(seq[0]) and Jats2OC.num(seq[1]): # more digits <xref rid="CIT0001">1-3</xref>
					pl_string , pl_xpath = rp_string , rp_xpath
					rp_dict = Jats2OC.rp_dict(xref , n_rp , xref_id , rp_string , rp_xpath , pl_string , pl_xpath, context_xpath, containers_title)
					rp_list.append(rp_dict)
					range_values = [int( val ) for val in seq if val.isdigit() ]
					if len(range_values) == 2:
						range_values.sort()
						for intermediate in range(int(range_values[0])+1,int(range_values[1])+1 ): # 2nd to last included
							n_rp += 100
							xref_id = Jats2OC.find_xmlid(str(intermediate),root)
							rp_dict_i = Jats2OC.rp_dict(xref , n_rp , xref_id , None , None , pl_string , rp_xpath, context_xpath, containers_title)
							rp_list.append(rp_dict_i)
					else: # no digits
						pass
				else: # simple string <xref rid="CIT0001">1</xref>

					rp_dict = Jats2OC.rp_dict(xref , n_rp , xref_id , rp_string , rp_xpath , None , None, context_xpath, containers_title)
					rp_list.append(rp_dict)
			else: # children
				rp_string = ET.tostring(xref, method="text", encoding='unicode', with_tail=False).strip().replace('\n','')
				if char_before and char_after and (char_before == conf.list_separators[1][0] or char_before == conf.list_separators[2][0]) \
					and ( char_after == conf.list_separators[1][1] or char_after == conf.list_separators[2][1]):
					rp_string = char_before+rp_string+char_after
				tail = (xref[0].tail).strip().replace('\n','') if xref[0].tail else ''
				child = (xref[0].text).strip().replace('\n','') if xref[0].text else rp_string
				rp_child_norm, child_tail_norm = re.sub(r"\s+", "", child) , re.sub(r"\s+", "", tail)
				#if len(xref_text.strip().replace('\n','')) != 0 or len(tail) != 0: # Amass <italic>et al.</italic>, 2000
				if len(rp_child_norm) != 0 and len(child_tail_norm) != 0: # Amass <italic>et al.</italic>, 2000
					rp_dict = Jats2OC.rp_dict(xref , n_rp , xref_id , rp_string , rp_xpath , None , None, context_xpath, containers_title)
					rp_list.append(rp_dict)
				elif len(rp_child_norm) != 0 and len(child_tail_norm) == 0: # xref/sup
					seq = (rp_child_norm).split('\u2013') if xref[0].text else ((ET.tostring(xref[0], method="text", encoding='unicode', with_tail=False)).strip().replace('\n','')).split('\u2013')
					if len(seq) == 2 and Jats2OC.num(seq[0]) and Jats2OC.num(seq[1]): # more digits <xref rid="CIT0001"><sup>1-3</sup></xref>
						pl_string , pl_xpath = rp_string , rp_xpath
						rp_dict = Jats2OC.rp_dict(xref , n_rp , xref_id , rp_string , rp_xpath , pl_string , pl_xpath, context_xpath, containers_title)
						rp_list.append(rp_dict)
						range_values = [int( val ) for val in seq if val.isdigit() ]
						if len(range_values) != 0:
							range_values.sort()
							for intermediate in range(int(range_values[0])+1,int(range_values[1])+1 ): # 2nd to last included
								n_rp += 100
								xref_id_int = Jats2OC.find_xmlid(str(intermediate),root)
								rp_dict_i = Jats2OC.rp_dict(xref , n_rp , xref_id_int , None , None , pl_string , pl_xpath, context_xpath, containers_title)
								rp_list.append(rp_dict_i)
					else: # simple string
						rp_string = ET.tostring(xref[0], method="text", encoding='unicode', with_tail=False).strip().replace('\n','')
						rp_dict = Jats2OC.rp_dict(xref , n_rp , xref_id , rp_string , rp_xpath , pl_string , pl_xpath, context_xpath, containers_title)
						rp_list.append(rp_dict)


		return rp_list


	@staticmethod
	def parent_pl(root,  pl_string, pl_xpath, context_xpath, containers_title, parent_el, rp_list):
		parent_el_list = []
		for xref_el in parent_el:
			n_rpn = [rp["n_rp"] for rp in rp_list if rp["xml_element"] == xref_el ][0]
			tail = (xref_el.tail)
			if tail and ('-' in tail.strip().replace('\n','') or '\u2013' in tail.strip().replace('\n','')): # this handles also mixed lists/sequences
				end_seq = xref_el.getnext()
				if end_seq.tag == 'xref' and ( (xref_el.text).isdigit() and (end_seq.text).isdigit() ):
					for intermediate in range(int(xref_el.text)+1,int(end_seq.text) ):
						# we assume that lists cannot include more than 100 elements
						n_rpn += 1
						xref_id = Jats2OC.find_xmlid(str(intermediate),root)
						rp_dict_i = Jats2OC.rp_dict(xref_el , n_rpn , xref_id , None , None , pl_string , pl_xpath, context_xpath, containers_title)
						#rp_list.append(rp_dict_i)
						parent_el_list.append(rp_dict_i)

			rp_list = sorted(rp_list, key=lambda rp: int(rp["n_rp"]))

			for rp in rp_list:
				if xref_el == rp["xml_element"]:
					rp["pl_string"] = pl_string.replace("\n","")
					rp["pl_xpath"] = pl_xpath
					parent_el_list.append(rp)
					rp_list.remove(rp)

			parent_el_list = sorted(parent_el_list, key=lambda rp: int(rp["n_rp"]))
		return parent_el_list , rp_list


	@staticmethod
	def add_pl_info(rp_d, root):
		first_el = rp_d[0]["xml_element"]
		last_el = rp_d[-1]["xml_element"] if isinstance(rp_d[-1]["xml_element"],str) == False else rp_d[-2]["xml_element"]
		for rp in rp_d:
			if "pl_xpath" not in rp.keys():
				pl_xpath = Jats2OC.xpath_list_between_elements(first_el, last_el, root)
				rp["pl_xpath"] = pl_xpath

				char_before = re.sub(r"\s+", "", "".join(Jats2OC.get_text_before(first_el)))[-1] if len(re.sub(r"\s+", "", "".join(Jats2OC.get_text_before(first_el)))) != 0 else None
				char_after = re.sub(r"\s+", "", "".join(Jats2OC.get_text_after(last_el)))[0] if len(re.sub(r"\s+", "", "".join(Jats2OC.get_text_after(last_el)))) != 0 else None
				if char_before and char_after and (char_before == conf.list_separators[1][0] or char_before == conf.list_separators[2][0]) \
					and ( char_after == conf.list_separators[1][1] or char_after == conf.list_separators[2][1]):
					rp["pl_string"] = (char_before+root.xpath(pl_xpath)+char_after).replace("\n","")
				else:
					rp["pl_string"] = root.xpath(pl_xpath).replace("\n","")
		return rp_d


	@staticmethod
	def add_rp_in_sentence(metadata, xref_list, rp_list):
		metadata.append(xref_list)
		for rp in rp_list:
			if rp == xref_list[0]:
				rp_list.remove(rp)


	@staticmethod
	def add_rp_and_pl_in_sentence(root, et, metadata, groups, rp_list, end_separator):
		for group in groups:
			if 'singleton' in group:
				for single_rp in group: # for some reasons sometimes there are more singletons
					if not isinstance(single_rp,str):
						singleton_path = et.getpath(single_rp)
						rp_dict = [rp for rp in rp_list if "rp_xpath" in rp.keys() and rp["rp_xpath"] == singleton_path]

						for rp in rp_dict:
							metadata.append(rp_dict)
							rp_list.remove(rp)

			if 'list' in group:
				elems_path = [et.getpath(elem) for elem in group if isinstance(elem, str) == False]
				rp_dicts = [rp for rp in rp_list for elem in elems_path if "rp_xpath" in rp.keys() and rp["rp_xpath"] == elem]
				rp_dicts = Jats2OC.add_pl_info(rp_dicts, root) if len(rp_dicts) > 1 else rp_dicts


				metadata.append(rp_dicts)
				for rp in rp_dicts:
					rp_list.remove(rp)

			if 'sequence' in group:
				elems_path = [et.getpath(elem) for elem in group if isinstance(elem, str) == False]
				rp_dicts = [rp for rp in rp_list for elem in elems_path if "rp_xpath" in rp.keys() and rp["rp_xpath"] == elem]
				range_values = [int(rp["rp_string"]) for rp in rp_list \
					for elem in elems_path if "rp_xpath" in rp.keys() \
					and rp["rp_xpath"] == elem and rp["rp_string"].isdigit()]
				if len(range_values) != 0:
					range_values.sort()
					n_rpn = rp_dicts[0]["n_rp"]
					for intermediate in range(int(range_values[0])+1,int(range_values[1]) ):
						n_rpn += 1 # TODO change
						xref_id = Jats2OC.find_xmlid(str(intermediate),root)
						rp = rp_dicts[0]["xml_element"]
						context_xpath = rp_dicts[0]["context_xpath"]
						containers_title = rp_dicts[0]["containers_title"]
						rp_dict_i = Jats2OC.rp_dict(None , n_rpn , xref_id , None , None , None , None, context_xpath, containers_title)
						rp_dicts.append(rp_dict_i)
						rp_dicts = sorted(rp_dicts, key=lambda rp: int(rp["n_rp"]))
						rp_dicts = Jats2OC.add_pl_info(rp_dicts, root) if len(rp_dicts) > 1 else rp_dicts

				metadata.append(rp_dicts)
				for rp in rp_dicts:
					if rp in rp_list:
						rp_list.remove(rp)

			if 'mixed' in group:
				extended_list = []
				for pos,xref_el in enumerate(group):
					if isinstance(xref_el,str) == False and pos < len(group)-1:
						for rp in rp_list:
							if xref_el == rp["xml_element"]:
								extended_list.append(rp)
						if '-' in group[pos+1] or '\u2013' in group[pos+1]:
							n_rpn = [rp["n_rp"] for rp in rp_list if rp["xml_element"] == group[pos] ][0]
							context_xpath = [rp["context_xpath"] for rp in rp_list if rp["xml_element"] == xref_el ][0]
							containers_title = [rp["containers_title"] for rp in rp_list if rp["xml_element"] == xref_el ][0]

							end_seq = group[pos+2]
							if end_seq.tag == 'xref' and ( (xref_el.text).isdigit() and (end_seq.text).isdigit() ):
								for intermediate in range(int(xref_el.text)+1,int(end_seq.text) ):
									# we assume that lists cannot include more than 100 elements
									n_rpn += 1
									xref_id = Jats2OC.find_xmlid(str(intermediate),root)
									rp_dict_i = Jats2OC.rp_dict(xref_el , n_rpn , xref_id , None , None , None , None, context_xpath, containers_title)
									extended_list.append(rp_dict_i)
					for rp in rp_list:
						if xref_el == rp["xml_element"]:
							rp_list.remove(rp)

				extended_list = sorted(extended_list, key=lambda rp: int(rp["n_rp"]))
				extended_list = Jats2OC.add_pl_info(extended_list, root) if len(extended_list) > 1 else extended_list

				metadata.append(extended_list)
				for rp in extended_list:
					if rp in rp_list:
						rp_list.remove(rp)

	@staticmethod
	def handle_no_separators(root, xref_in_sent): # TODO handle seq and lists together
		groups , lonely = [],[]
		for xref in xref_in_sent: # exception xref/sup + sup=, + xref/sup
			# start
			if len(root.xpath('/'+xref+'/following-sibling::*[1][contains(text(), ",")]')) != 0 \
				and len(root.xpath('/'+xref+'/preceding-sibling::*[1][contains(text(), ",")]')) == 0:
				if root.xpath('/'+xref+'/sup/text()'):
					groups.append(["1",xref, (root.xpath('/'+xref+'/sup/text()')[0]) ])
				else:
					groups.append(["1",xref, (root.xpath('/'+xref+'//text()')[0]) ])
			# alone
			elif len(root.xpath('/'+xref+'/following-sibling::*[1][contains(text(), ",")]')) == 0 \
				and len(root.xpath('/'+xref+'/preceding-sibling::*[1][contains(text(), ",")]')) == 0:
				if root.xpath('/'+xref+'/sup/text()'):
					lonely.append(["0",xref, (root.xpath('/'+xref+'/sup/text()')[0]) ])
				else:
					lonely.append(["0",xref, (root.xpath('/'+xref+'//text()')[0]) ]) # mistakes in lists with separators (e.g. 31411129, sec[1]/p[1]/xref[3])
			# inlist
			elif len(root.xpath('/'+xref+'/following-sibling::*[1][contains(text(), ",")]')) != 0 \
				and len(root.xpath('/'+xref+'/preceding-sibling::*[1][text() = ","]')) != 0:
				if root.xpath('/'+xref+'/sup/text()'):
					groups.append(["2",xref, (root.xpath('/'+xref+'/sup/text()')[0]) ])
				else:
					groups.append(["2",xref, (root.xpath('/'+xref+'//text()')[0]) ])
			# last
			elif len(root.xpath('/'+xref+'/following-sibling::*[1][contains(text(), ",")]')) == 0 \
				and len(root.xpath('/'+xref+'/preceding-sibling::*[1][contains(text(), ",")]')) != 0:
				if root.xpath('/'+xref+'/sup/text()'):
					groups.append(["3",xref, (root.xpath('/'+xref+'/sup/text()')[0]) ])
				else:
					groups.append(["3",xref, (root.xpath('/'+xref+'//text()')[0]) ]) # last
			# only rp
			else:
				if len(root.xpath('/'+xref+'/following-sibling::*[1][contains(text(), ",")]')) != 0 \
					and len(root.xpath('/'+xref+'/preceding-sibling::*[1][contains(text(), ",")]')) != 0:
					groups.append(["1",xref, (root.xpath('/'+xref+'//text()')[0]) ])
				else:
					lonely.append([ "0",xref, (root.xpath('/'+xref+'//text()')[0]) ])
		return groups, lonely

	@staticmethod
	def is_list(group):
		if ((conf.rp_separators_in_list[1].decode('utf-8') not in group) \
			and (conf.rp_separators_in_list[2].decode('utf-8') not in group)) \
			and (conf.rp_separators_in_list[0].decode('utf-8') in group \
			or conf.rp_separators_in_list[3].decode('utf-8') in group):
			return True
		return None

	@staticmethod
	def is_sequence(group):
		if (conf.rp_separators_in_list[1].decode('utf-8') in group \
			or conf.rp_separators_in_list[2].decode('utf-8') in group) \
			and (conf.rp_separators_in_list[0].decode('utf-8') not in group \
			and conf.rp_separators_in_list[3].decode('utf-8') not in group):
			return True
		return None

	@staticmethod
	def is_mixed(group):
		if ((conf.rp_separators_in_list[1].decode('utf-8') in group) \
			or (conf.rp_separators_in_list[2].decode('utf-8') in group)) \
			and ((conf.rp_separators_in_list[0].decode('utf-8') in group) \
				or (conf.rp_separators_in_list[3].decode('utf-8') in group)):
			return True
		return None

	@staticmethod
	def add_group_type(rp_groups):
		for group in rp_groups:
			if Jats2OC.is_list(group) == True:
				group.append('list')
			elif Jats2OC.is_sequence(group) == True:
				group.append('sequence')
			elif Jats2OC.is_mixed(group) == True:
				group.append('mixed')
			else:
				group.append('singleton')
		return rp_groups


	@staticmethod
	def sublist(groups):
		result_list = []
		sublist = []
		previous_number = None

		for current_number,path,val in groups:
			if previous_number is None or current_number > previous_number:
				sublist.append((current_number,path,val)) # still ascending, add to the current sublist
			else:
				result_list.append(sublist) # no longer ascending, add the current sublist
				sublist = [(current_number,path,val)] # start a new sublist
			previous_number = current_number
		if sublist: # add the last sublist, if there's anything there
			result_list.append(sublist)
		return result_list


	@staticmethod
	def num(s):
	    try:
	        return int(s)
	    except:
	        return None


	@staticmethod
	def get_be_id(elem):
		"""
		params: elem -- the XML element including the rp
		return: ID of the XML element including the be denoted by the rp
		"""
		return elem.get('rid') if 'rid' in elem.attrib else elem.getparent().get('rid')


	@staticmethod
	def find_xmlid(elem,root):
		"""
		params: elem -- the XML element OR the text value of the XML element including the rp
		params: root -- the root element of the XML document
		return: xmlid of the rp, i.e. of the bibentry denoted by the rp
		"""

		if isinstance(elem, str) == False:
			xmlid = Jats2OC.get_be_id(elem)
		else:
			for ref in root.xpath('.//ref-list/ref[label[contains(text(),'+elem+')]]'):
				if re.sub(r"\D+", "", ref.find('.//label').text ) == elem: # remove all non digits and look for the exact match
					xmlid = ref.get('id')
		return xmlid if not None else ''


	@staticmethod
	def get_text_before(elem):
		""" extract text before an xml element till the start tag of the parent element"""
		for item in elem.xpath("preceding-sibling::*//text()|preceding-sibling::text()"):
			item = item
			if item:
				yield item


	@staticmethod
	def get_text_after(elem):
		""" extract text after an xml element till the end tag of the parent element"""
		for item in elem.xpath("following-sibling::*//text()|following-sibling::text()"):
			item = item
			if item:
				yield item


	@staticmethod
	def xpath_sentence(elem, root, abb_list_path, parent=None):
		"""
		params: elem -- the rp
		params: root -- the root element of the XML document
		params: abb_list_path -- a txt file including the list of abbreviations for splitting sentences
		return: XPath of the sentence including the rp
		"""
		if parent:
			elem = elem.getparent()

		elem_value = ET.tostring(elem, method="text", encoding='unicode', with_tail=False)
		with open(abb_list_path, 'r') as f:
			abbreviations_list = [line.strip() for line in f.readlines() if not len(line) == 0]

		punkt_param = PunktParameters()
		punkt_param.abbrev_types = set(abbreviations_list)
		sentence_splitter = PunktSentenceTokenizer(punkt_param)

		string_before = "".join(Jats2OC.get_text_before(elem))
		string_after = "".join(Jats2OC.get_text_after(elem))
		# offset of sentence in the stringified parent element that include the rp
		# (0-based index transformed in 1-based index -- +1 -- to comply with XPath)
		if len(string_before) == 0:
			str_before = ''
			start_sent = 1
		elif len(string_before) != 0 and string_before.isspace():
			str_before = string_before
			start_sent = int([start for start, end in sentence_splitter.span_tokenize( string_before+elem_value )][-1])+1
		else:
			# if str_before finishes with . and str_after starts with uppercase than [-2 and -1]
			str_before = sentence_splitter.tokenize( string_before+elem_value )[-1]
			start_sent = int([start for start, end in sentence_splitter.span_tokenize( string_before+elem_value )][-1] )+1
		if len(string_after) == 0 or string_after.isspace():
			str_after = ''
		else:
			str_after = sentence_splitter.tokenize( string_after )[0]
		len_sent = len(str_before+str_after)
		sent_xpath_function = 'substring(string('+ET.ElementTree(root).getpath(elem.getparent())+'),'+str(start_sent)+','+str(len_sent)+')'
		return sent_xpath_function


	@staticmethod
	def xpath_list_between_elements(first_el, last_el, root):
		"""
		params: first_el -- first rp
		params: last_el -- last rp
		params: root -- the root element of the XML document
		return: xpath of the string including the pl that has no separators, nor parent element
		"""
		last_value = ET.tostring(last_el, method="text", encoding='unicode', with_tail=False)
		string_before = "".join(Jats2OC.get_text_before(first_el))
		string_before_last = "".join(Jats2OC.get_text_before(last_el))
		start_pl = int( len(string_before) )
		len_pl = int( len(string_before_last+last_value) ) - start_pl
		pl_xpath_function = 'substring(string('+ET.ElementTree(root).getpath(first_el.getparent())+'),'+str(start_pl+1)+','+str(len_pl)+')'
		return pl_xpath_function


	@staticmethod
	def find_container_title(elem, container_tag, root):
		"""
		params: elem -- an XML element
		params: container_tag -- the tag of the container element including the title
		return: title -- the tag of the element containing the title of the container
		"""
		et = ET.ElementTree(root)
		title_list = { et.getpath(x):ET.tostring( x, method="text", encoding='unicode', with_tail=False).strip() for x in elem.xpath('./ancestor::node()/'+conf.title_tag)}
		if len(title_list) == 0:
			title_list = ''
		return title_list


	@staticmethod
	def clean(stringa):
		"""return: encoded stripped string"""
		return stringa.encode('utf-8').strip()


	@staticmethod
	def clean_list(l):
		"""given a list of strings/elements returns a new list with stripped strings and elements"""
		# only strings
		new_l = []
		type_l = list({type(item) for item in l})
		string_list = True if len(type_l) == 1 and type_l[0] == str else False

		if string_list == True:
			for x in l:
				if len(x) != 0 and '\n' in x:
					y = x.replace("\n","")
					y = re.sub(r"\s+", "", y)
					if len(y) != 0:
						new_l.append(y[:1])
				elif len(x) != 0 and '\n' not in x:
					new_l.append(re.sub(r"\s+", "", x[:1]))
		else:
			for x in l: # strings and elems
				if isinstance(x, str) == True and len(x) != 0 and '\n' in x:
					y = x.replace("\n","")
					y = re.sub(r"\s+", "", y)
					if len(y) != 0:
						new_l.append(y[0])
				elif isinstance(x, str) == True and len(x) != 0 and '\n' not in x:
					new_l.append(re.sub(r"\s+", "", x[0]))
				else:
					new_l.append(x)
		return new_l


	@staticmethod
	def rp_end_separator(rp_path_list):
		"""given a list of separators (in sentence) retrieve the most common separator"""
		rp_end_separator = Jats2OC.clean_list(rp_path_list)
		rp_end_separator = [rp for rp in rp_end_separator if rp.encode('utf-8') not in conf.rp_separators_in_list]
		rp_end_separator = Counter(rp_end_separator).most_common(2)
		return rp_end_separator


	@staticmethod
	def rp_dict(xref , n_rp , xref_id , rp_string , rp_xpath , pl_string , pl_xpath, context_xpath, containers_title):
		""" create a dictionary w/ all the info on a rp to be refined and injected in a final JSON"""
		rp_dict = {}
		if xref is not None:
			rp_dict["xml_element"] = xref
		rp_dict["n_rp"] = n_rp
		rp_dict["xref_id"] = xref_id
		if rp_string is not None:
			rp_dict["rp_string"] = rp_string
		if pl_string is not None:
			rp_dict["pl_string"] = pl_string
		if rp_xpath is not None:
			rp_dict["rp_xpath"] = rp_xpath
		if pl_xpath is not None:
			rp_dict["pl_xpath"] = pl_xpath
		rp_dict["context_xpath"] = context_xpath
		rp_dict["containers_title"] = containers_title
		return rp_dict


	#########################
	#### METHODS FOR RDF ####
	#########################


	@staticmethod
	def process_reference_pointers(citing_entity, cited_entities_xmlid_be, reference_pointer_list, graph, resp_agent=None, source_provider=None, source=None):
		""" process a JSON snippet including reference pointers
		return RDF entities for rp, pl, and de, according to OCDM """
		de_resources , be_ids = [] , {}
		be_ids_list = [rp_dict['xref_id'] for pl_entry in reference_pointer_list for rp_dict in pl_entry]
		be_ids_counter = Counter(be_ids_list)

		for pl_entry in reference_pointer_list:
			if len(pl_entry) > 1:
				rp_entities_list =[]
				cur_pl = Jats2OC.process_pointer_list(pl_entry, citing_entity, graph, de_resources, resp_agent, source_provider, source)
				for rp_dict in pl_entry:
					rp_num = Jats2OC.retrieve_rp_occurrence(be_ids, rp_dict)
					rp_total_occurrence = str(be_ids_counter[rp_dict["xref_id"]])
					rp_entity = Jats2OC.process_pointer(rp_dict, rp_num, rp_total_occurrence, citing_entity, cited_entities_xmlid_be, graph, de_resources, resp_agent, source_provider, source, in_list=True)
					cur_pl.contains_element(rp_entity)
					rp_entities_list.append(rp_entity)
				for pos, sibling in enumerate(rp_entities_list):
					if pos < len(rp_entities_list)-1 and sibling != rp_entities_list[pos+1]:
						cur_rp, next_rp = rp_entities_list[pos] , rp_entities_list[pos+1]
						cur_rp.has_next_de(next_rp)

			else:
				rp_num = Jats2OC.retrieve_rp_occurrence(be_ids, pl_entry[0])
				rp_total_occurrence = str(be_ids_counter[pl_entry[0]["xref_id"]])
				rp_entity = Jats2OC.process_pointer(pl_entry[0], rp_num, rp_total_occurrence, citing_entity, cited_entities_xmlid_be, graph, de_resources, resp_agent, source_provider, source)

		for cited_entity, xmlid, be in cited_entities_xmlid_be:
			gen_an = graph.add_an(resp_agent, source_provider, source)
			gen_ci = graph.add_ci(resp_agent, citing_entity, cited_entity, source_agent=source_provider, source=source)
			gen_ci._create_citation(citing_entity, cited_entity)
			gen_an._create_annotation(gen_ci, be_res=be)

		siblings = Jats2OC.create_following_sibling(reference_pointer_list, de_resources)


	@staticmethod
	def process_pointer_list(pl_entry, citing_entity, graph, de_resources, resp_agent=None, source_provider=None, source=None):
		""" process a pl list of dict """
		cur_pl = graph.add_pl(resp_agent, source_provider, source)
		containers_title = pl_entry[0]["containers_title"]
		if "pl_string" in pl_entry[0]:
			cur_pl.create_content(pl_entry[0]["pl_string"])
		if "pl_xpath" in pl_entry[0]:
			pl_xpath = Jats2OC.add_xpath(graph, cur_pl, pl_entry[0]["pl_xpath"], resp_agent, source_provider, source)
		if "context_xpath" in pl_entry[0]:
			context = Jats2OC.create_context(graph, citing_entity, cur_pl, pl_entry[0]["context_xpath"], de_resources, containers_title, resp_agent)
		return cur_pl


	@staticmethod
	def process_pointer(dict_pointer, rp_num, rp_total_occurrence, citing_entity, cited_entities_xmlid_be, graph, de_resources, resp_agent=None, source_provider=None, source=None, in_list=False):
		""" process a rp_dict, create citation and annotation """
		cur_rp = graph.add_rp(resp_agent, source_provider, source)
		containers_title = dict_pointer["containers_title"]
		if "rp_xpath" in dict_pointer:
			rp_xpath = Jats2OC.add_xpath(graph, cur_rp, dict_pointer["rp_xpath"], resp_agent, source_provider, source)
		if "rp_string" in dict_pointer:
			cur_rp.create_content(dict_pointer["rp_string"])
		if in_list==False:
			if "context_xpath" in dict_pointer:
				context = Jats2OC.create_context(graph, citing_entity, cur_rp, dict_pointer["context_xpath"], de_resources, containers_title, resp_agent, source_provider, source)
		for cited_entity, xmlid, be in cited_entities_xmlid_be:
			if dict_pointer["xref_id"] == xmlid:
				cur_rp.denotes_be(be)
				rp_pid = Jats2OC.add_intrepid(graph, cur_rp, citing_entity, cited_entity, rp_num, rp_total_occurrence, resp_agent, source_provider, source)
				cur_an = graph.add_an(resp_agent, source_provider, source)
				cur_ci = graph.add_ci(resp_agent, citing_entity, cited_entity, rp_num, source_provider, source)
				cur_ci._create_citation(citing_entity, cited_entity)
				cur_an._create_annotation(cur_ci, rp_res=cur_rp)

		return cur_rp


	@staticmethod
	def add_xpath(graph, cur_res, xpath_string, resp_agent=None, source_provider=None, source=None): # new
		cur_id = graph.add_id(resp_agent, source_provider, source)
		cur_id.create_xpath(xpath_string)
		cur_res.has_id(cur_id)


	@staticmethod
	def add_intrepid(graph, cur_rp, citing_entity, cited_entity, rp_num, rp_total_occurrence, resp_agent, source_provider, source):
		citing_res , cited_res = str(citing_entity) , str(cited_entity)
		citing_count = citing_res.rsplit('/',1)[-1]
		cited_count = cited_res.rsplit('/',1)[-1]
		if rp_num is not None and rp_total_occurrence is not None:
			intrepid = citing_count+'-'+cited_count+'/'+rp_num+'-'+rp_total_occurrence
			cur_id = graph.add_id(resp_agent, source_provider, source)
			cur_id.create_intrepid(intrepid)
			cur_rp.has_id(cur_id)


	@staticmethod
	def create_context(graph, citing_entity, cur_rp_or_pl, xpath_string, de_resources, containers_title, resp_agent=None, source_provider=None, source=None):
		cur_sent = Jats2OC.de_finder(graph, citing_entity, xpath_string, de_resources, containers_title, resp_agent, source_provider, source)
		if cur_sent != None:
			cur_rp_or_pl.has_context(cur_sent)


	@staticmethod
	def de_finder(graph, citing_entity, xpath_string, de_resources, containers_title, resp_agent, source_provider=None, source=None):
		cur_de = [de_uri for de_path, de_uri in de_resources if xpath_string == de_path]
		if len(cur_de) == 0: # new de
			de_res = graph.add_de(resp_agent, source_provider, source)
			de_resources.append((xpath_string, de_res))
			if 'substring(string(' in xpath_string and conf.table_tag in xpath_string: # sentence or text chunk
				de_res.create_text_chunk()
			elif 'substring(string(' in xpath_string and conf.table_tag not in xpath_string:
				de_res.create_sentence()
			else:
				de_res.create_discourse_element(Jats2OC.elem_to_type(xpath_string))
			de_xpath = Jats2OC.add_xpath(graph, de_res, xpath_string, resp_agent, source_provider, source)
			if xpath_string+'/title' in containers_title:
				de_res.create_title(containers_title[xpath_string+'/title'])
			hierarchy = Jats2OC.create_hierarchy(graph, citing_entity, de_res, Jats2OC.get_subxpath_from(xpath_string), de_resources, containers_title, resp_agent, source_provider, source)
		else:
			de_res = cur_de[0]

		return de_res


	@staticmethod
	def elem_to_type(xpath):
		"""
		params: xpath -- XPath of an XML element to be mapped to RDF
		return: DOCO/DEO class
		"""
		pos = re.search( r"\[.*\]", xpath.rsplit('/', 1)[-1])
		if pos:
			elem = re.sub(r"\[.*\]" ,'', xpath.rsplit('/', 1)[-1])
		else:
			elem = xpath.rsplit('/', 1)[-1]
		cl = [el[1] for el in conf.elem_mapping if elem == el[0]]
		if len(cl) != 0:
			return cl[0]
		else:
			return None


	@staticmethod
	def get_subxpath_from(string):
		if "substring(string(" in string:
			pattern = re.search(r"substring\(string\((.*?)\)",string)
			xpath = pattern.group(1)
		else:
			xpath = string[:string.rfind('/')] # pop last element
		return xpath


	@staticmethod
	def create_hierarchy(graph, citing_entity, de_res, xpath_string, de_resources, containers_title, resp_agent=None, source_provider=None, source=None):
		if Jats2OC.is_path(xpath_string) and xpath_string != '/':
			cur_el = Jats2OC.de_finder(graph, citing_entity, xpath_string, de_resources,containers_title, resp_agent, source_provider, source)
			if cur_el != None:
				de_res.contained_in_discourse_element(cur_el)
				hierarchy = Jats2OC.create_hierarchy(graph, citing_entity, cur_el, Jats2OC.get_subxpath_from(xpath_string), de_resources, containers_title, resp_agent, source_provider, source)
				if xpath_string.count('/') == 3: # e.g. "/article/body/sec"
					citing_entity.contains_discourse_element(cur_el)


	@staticmethod
	def is_path(xpath):
		return re.search("^\/[^/]+/?[^/]+$", xpath) is None # if not '/article/body' or '/article/back'


	@staticmethod
	def retrieve_rp_occurrence(be_ids, rp_dict):
		if rp_dict["xref_id"] in be_ids:
			be_ids[rp_dict["xref_id"]] = be_ids[rp_dict["xref_id"]]+1
		else:
			be_ids[rp_dict["xref_id"]] = 1

		occurrence = be_ids[rp_dict["xref_id"]]
		return str(occurrence)


	@staticmethod
	def create_following_sibling(reference_pointer_list, de_resources):
		base_xpath = "(\/\w+\/\w+)(.*)$"
		list_xpaths = [Jats2OC.get_subxpath_from(rp["context_xpath"]) for pl in reference_pointer_list for rp in pl if "context_xpath" in rp]
		# for pl in reference_pointer_list:
		# 	for rp in pl:
		# 		if "context_xpath" in rp:
		# 			xp = re.sub(base_xpath, "\\2", Jats2OC.get_subxpath_from(rp["context_xpath"]) )
		# 			list_xpaths.append(xp)
		list_subpaths = [ Jats2OC.recursive_split(xpath) for xpath in list_xpaths ]
		list_siblings = zip(*list_subpaths)
		for siblings_tuple in list_siblings:
			for pos, sibling in enumerate(siblings_tuple):
				if pos < len(siblings_tuple)-1 and sibling != siblings_tuple[pos+1] and Jats2OC.is_path(sibling):
					cur_de, next_de = Jats2OC.map_to_de(siblings_tuple[pos], de_resources) , Jats2OC.map_to_de(siblings_tuple[pos+1], de_resources)
					if cur_de != None and next_de != None:
						cur_de.has_next_de(next_de)


	@staticmethod
	def map_to_de(xpath,de_resources):
		base_xpath = "(\/\w+\/\w+)(.*)$"
		cur_de = [de_uri for de_path, de_uri in de_resources if xpath == de_path ]
		if len(cur_de) == 0:
			return None
		return cur_de[0]


	@staticmethod
	def recursive_split(xpath, list_subpath=None):
		if list_subpath is None:
			list_subpath = []
		if xpath != '/' and xpath != '':
			list_subpath.append(xpath)
			Jats2OC.recursive_split(Jats2OC.get_subxpath_from(xpath), list_subpath)
		return list(reversed(list_subpath))
