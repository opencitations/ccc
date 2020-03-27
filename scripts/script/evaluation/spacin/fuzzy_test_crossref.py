from fuzzywuzzy import fuzz
from script.ccc.jats2oc import Jats2OC as jt

import Levenshtein as lev
import json, pprint, requests

pp = pprint.PrettyPrinter(indent=1)
# case 1: match with str_2
str_b = "Gussew, A, Rzanny, R, Güllmar, D, Scholle, H-C, Reichenbach, JR. 1H-MR spectroscopic detection of metabolic changes in pain processing brain regions in the presence of non-specific chronic low back pain, Neuroimage, 2011, 54, 2, 1315, 1323, DOI: 10.1016/j.neuroimage.2010.09.039, PMID: 20869447"
str0 = "WITHDRAWN: Erratum to “1H-MR spectroscopic detection of metabolic changes in pain processing brain regions in the presence of non-specific chronic low back pain” [NeuroImage 54/2 (2011) 1315–1323]"
str1 = "Erratum to “1H-MR spectroscopic detection of metabolic changes in pain processing brain regions in the presence of non-specific chronic low back pain” [NeuroImage 54/2 (2011) 1315–1323]"
str2 = "1H-MR spectroscopic detection of metabolic changes in pain processing brain regions in the presence of non-specific chronic low back pain"

response  = requests.get("https://api.crossref.org/works?rows=3&query.bibliographic="+str_b)
json_crossref = json.loads(response.text)
result = jt.fuzzy_match(str_b, json_crossref["message"]["items"],95.0)
pp.pprint(result)
# str_b | str0 | str1 | str2:
# lev: 126 128 157 <-
# ratio: 70 71 64 NO
# partial: 86 89 100 <-
# tsort: 74 76 67 NO
# tset: 94 97 100 <-

# case 2: match with str_1
str_b = "Dettmer, U, Newman, AJ, Soldner, F, Luth, ES, Kim, NC, von Saucken, VE, Sanderson, JB, Jaenisch, R, Bartels, T, Selkoe, D. Parkinson-causing α-synuclein missense mutations shift native tetramers to monomers as a mechanism for disease initiation, Nat Commun, 2015b, 6, 7314, PMID: 26076669"
str0 = "Erratum: Corrigendum: Parkinson-causing α-synuclein missense mutations shift native tetramers to monomers as a mechanism for disease initiation"
str1 = "Parkinson-causing α-synuclein missense mutations shift native tetramers to monomers as a mechanism for disease initiation"
str2 = "Defining the Native State of α-Synuclein"

response  = requests.get("https://api.crossref.org/works?rows=3&query.bibliographic="+str_b)
json_crossref = json.loads(response.text)
result = jt.fuzzy_match(str_b, json_crossref["message"]["items"],95.0)
pp.pprint(result)

# str_b | str0 | str1 | str2:
# lev: 155 167 256 NO
# ratio: 62 59 20 NO
# partial: 90 100 48 <-
# tsort: 64 63 24 NO
# tset: 92 100 62 <-

distance_0 = lev.distance(str_b.lower(),str0.lower())
distance_1 = lev.distance(str_b.lower(),str1.lower())
distance_2 = lev.distance(str_b.lower(),str2.lower())

ratio_0 = fuzz.ratio(str_b.lower(),str0.lower())
ratio_1 = fuzz.ratio(str_b.lower(),str1.lower())
ratio_2 = fuzz.ratio(str_b.lower(),str2.lower())

partial_0 = fuzz.partial_ratio(str_b.lower(),str0.lower())
partial_1 = fuzz.partial_ratio(str_b.lower(),str1.lower())
partial_2 = fuzz.partial_ratio(str_b.lower(),str2.lower())

tsort_0 = fuzz.token_sort_ratio(str_b,str0)
tsort_1 = fuzz.token_sort_ratio(str_b,str1)
tsort_2 = fuzz.token_sort_ratio(str_b,str2)

tset_0 = fuzz.token_set_ratio(str_b,str0)
tset_1 = fuzz.token_set_ratio(str_b,str1)
tset_2 = fuzz.token_set_ratio(str_b,str2)

#print("str_b | str0 | str1 | str2: \nlev:",distance_0, distance_1,distance_2,  '\nratio:',ratio_0, ratio_1, ratio_2,'\npartial:',partial_0,partial_1, partial_2, '\ntsort:',tsort_0, tsort_1, tsort_2,'\ntset:',tset_0,tset_1, tset_2)
