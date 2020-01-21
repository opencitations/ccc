## NOTES
 * [Q] [NO] disambiguation of be? the case of two be referencing the same paper (13 out of 4018, i.e. 0.3%)
 * [Q] [NON CI INTERESSA] WSGI server? https://flask.palletsprojects.com/en/1.1.x/deploying/
 * [SP] add intrepid to datacite (and also Fabio's pids?)

## TODO RAMOSE

 * test RAMOSE with multiple APIs
 * [MEMO] change endpoint in cccapi.hf in production
 * [TODO] fork repo on github
 * [TODO] add methods to cccapi.hf
 * change test files with definitive one
 * modify documentation: write hf in documentation, describe param -css add examples : python, webserver with curl (say it can be done on browser)

## TODO Jats2OC

 * [FIX] which exceptions in pl should I resolve? see evaluation document
  * cerca i pl che finiscono nella sentence precedente: blabla {.} [pl] {U}ppercase oppure fine dell'elemnto parente)
  * risolvi liste senza separatori interni (non come liste)
  * risolvi liste e seq insieme
  * cerca di tenere le parentesi per rp e pl (BEE)
 * [ADD] control doi2doi self citation
 * evaluation on lists (compare cites and the presence of rp for that link)
 * [FIX] mistakes in pl_string bee - if there are problems return no string
 * [MEMO] config_spacin and ocdm/config - change folder names for production
 * [MEMO] run again SPACIN to check whether "derived_from" and "update_action" are correctly included in se

## DONE RAMOSE

 * [TODO] add css path argument
 * [Q] home page with paths and doc about ramose?
 * [DONE] flag per tirare su web server con flask o no.
 * [DONE] problem: cannot start the app without the starting /.  
  * python3 -m script.ccc.ramose -s script/ccc/ccc_v1.hf -w 127.0.0.1:8080 [throws error because the call is wrong]
 * [DONE] if the flag for the server is selected I change the call (that starts after the /) and then Ichange it back
  * python3 -m script.ccc.ramose -s script/ccc/ccc_v1.hf -c /api/v1/metadata/10.1080/14756366.2019.1680659 -w 127.0.0.1:8080

 * virtualenv and add requirements.txt
 * test with all the splits in the url
 * what happens with csv error handling? cannot be visualised in browser
 * the ACCEPT header never includes csv or json, hence the api takes what is written in the args or the default value

## DONE Jats2OC

 * [FIX] add again CrossrefProcessor for text search
 * [FIX] control hasNext for de
 * bug in labels graphlib / support
 * check if intrepid works correctly
 * normalise DOI in bee:
  try:
      doi_string = sub("\0+", "", sub("\s+", "", unquote(id_string[id_string.index("10."):])))
      return "%s%s" % (self.p if include_prefix else "", doi_string.lower().strip())
  except:  # Any error in processing the DOI will return None
      return None
 * remove be > hasAnnotation > oci/n for all the annotations related to rp
 * [FIX] no xmlid of be for intermediate
 * [FIX] duplicate rp
 * jats2oc.py - BEE: refactor extract_intext_refs() in functions
 * jats2oc.py - BEE: move all methods in conf in jats2oc.py and change prefix
 * add intrepid when creating the oci of the citation
 * BUG! http://localhost:9999/blazegraph/#explore:kb:%3Chttps://w3id.org/oc/ccc/be/0701%3E random annotations created for the same citation
 * remove all labels from data
 * simplify ProvSet
 * remove useless methods in conf_bee
 * conf_spacin.py - name and URI of new corpus w3id
 * conf_spacin.py - prefix of supplier
 * rp_n in JSON should start from 1 and not 0
 * "label": "OCC / br", to be changed
 * method for sentence/chunk for pl and rp
 * method for extracting all de from xpath
 * double check URI in final data
 * method for reconciling DE to the right one (no duplictes)
 * associate classes to DE and discard the elements that are not mapped to OCDM
 * remove prov folder pa.txt
 * refactor the URI patter for all the entities that need the prefix
 * method for associating titles to sections and not only  
 * annotation / citation .. annotations have incremental numbers!
 * ci modify support find_paths() for ci
 * graphlib - add methods for annotations (hasBody and hasAnnotation) and control prefixes everywhere
 * hasNext in graphlib and add in script
 * change add_ci to work without /n_rp
 * send prov to fabio
 * remove text search to api crossref
 * [FIX] WARNING:rdflib.term:https://w3id.org/oc/ccc/ci/07085-07089/Europe PubMed Central does not look like a valid URI,
 * [FIX] id-counter wrong folders
 * [FIX] ci folder structure: review regex find_paths : ci/070/10000/1000.json
 * jats2oc.py - BEE: remove n_rp
 * [7/1/2020] speed up CrossrefProcessor (text search)
 * [14/12/2019] merge with fabio's graphlib, storer (save in nt11) and support
 * [7/1/2020] preliminary questions to Leiden: what data would you like to access?
 * [DONE] provided_url to be changed

## PLAN


* [14/1/2020] deploy BEE/SPACIN on production: change config SPACIN, create new blazegraph (ccc.properties uguale al corpus)
* [20/1/2020] API Ramose (locally) + custom interesting stuff to provide
* [1/2/2020] API Ramose (remote) + agree w/ Leiden / Cambridge
* write papers? ISWC? Journal
