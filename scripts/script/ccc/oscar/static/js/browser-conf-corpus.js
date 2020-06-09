var browser_conf = {
  "sparql_endpoint": "http://127.0.0.1:9999/blazegraph/sparql",
  //"sparql_endpoint": "https://w3id.org/oc/ccc/sparql",

  "prefixes": [
      {"prefix":"cito","iri":"http://purl.org/spar/cito/"},
      {"prefix":"dcterms","iri":"http://purl.org/dc/terms/"},
      {"prefix":"datacite","iri":"http://purl.org/spar/datacite/"},
      {"prefix":"literal","iri":"http://www.essepuntato.it/2010/06/literalreification/"},
      {"prefix":"biro","iri":"http://purl.org/spar/biro/"},
      {"prefix":"frbr","iri":"http://purl.org/vocab/frbr/core#"},
      {"prefix":"c4o","iri":"http://purl.org/spar/c4o/"},
      {"prefix":"bds","iri":"http://www.bigdata.com/rdf/search#"},
      {"prefix":"fabio","iri":"http://purl.org/spar/fabio/"},
      {"prefix":"pro","iri":"http://purl.org/spar/pro/"},
      {"prefix":"oco","iri":"https://w3id.org/oc/ontology/"},
      {"prefix":"rdf","iri":"http://www.w3.org/1999/02/22-rdf-syntax-ns#"},
      {"prefix":"prism","iri":"http://prismstandard.org/namespaces/basic/2.0/"}
    ],

  "categories":{

    "document": {
          "rule": "br\/.*",
          "query": [`
            SELECT DISTINCT ?my_iri ?id_lit ?id_issn ?short_iri ?title ?subtitle ?year ?type ?s_type ?author ?author_br_iri (count(?next) as ?tot) (COUNT(distinct ?cites) AS ?out_cits) (COUNT(distinct ?cited_by) AS ?in_cits) ?j_vol_br_iri ?j_br_iri ?journal ?journal_data
            WHERE{
              		BIND(<https://w3id.org/oc/ccc/[[VAR]]> as ?my_iri) .
              		BIND('[[VAR]]' as ?short_iri) .
                  ?my_iri rdf:type ?type .
                  BIND(REPLACE(STR(?type), 'http://purl.org/spar/fabio/', '', 'i') as ?s_type) .
                  {
                        OPTIONAL {?my_iri dcterms:title ?title .}
                        OPTIONAL {?my_iri fabio:hasSubtitle ?subtitle .}
                        OPTIONAL {?my_iri prism:publicationDate ?year .}
                        OPTIONAL {?my_iri cito:cites ?cites .}
                        OPTIONAL {?cited_by cito:cites ?my_iri .}
                        OPTIONAL {
                            ?my_iri datacite:hasIdentifier [
                            datacite:usesIdentifierScheme datacite:doi ;
                            literal:hasLiteralValue ?id_lit
                            ] .
                          }
                        ?my_iri pro:isDocumentContextFor ?role .
                        ?role pro:withRole pro:author ; pro:isHeldBy [
                            foaf:familyName ?f_name ; foaf:givenName ?g_name
                          ] ; pro:isHeldBy ?author_iri .
                        OPTIONAL {?role oco:hasNext* ?next .}
                        OPTIONAL {?my_iri frbr:partOf+ ?journal_iri .
                          ?journal_iri a fabio:Journal ; dcterms:title ?journal .}
                        OPTIONAL {
                         ?my_iri frbr:partOf+ ?j_vol_iri .
                         ?j_vol_iri a fabio:JournalVolume ; fabio:hasSequenceIdentifier ?volume .
                         ?my_iri frbr:embodiment ?manifestation .
                         ?manifestation prism:startingPage ?start ; prism:endingPage ?end .
                         BIND(CONCAT(', ', ?volume,': ',?start,'-',?end) as ?journal_data) .
                        }
                  } UNION {
                        OPTIONAL {?my_iri dcterms:title ?title .}
                        OPTIONAL {?my_iri frbr:partOf+ ?journal_iri .
                          ?journal_iri a fabio:Journal ; dcterms:title ?journal .}
                        OPTIONAL {
                            ?my_iri datacite:hasIdentifier [
                            datacite:usesIdentifierScheme datacite:issn ;
                            literal:hasLiteralValue ?id_issn
                            ] .
                          }
                        OPTIONAL {?my_iri fabio:hasSequenceIdentifier ?vol . }
                        BIND(COALESCE(?title, ?vol, "") AS ?title).
                        BIND("" as ?journal_data) .
                  }
                  BIND(REPLACE(STR(?author_iri), '/ccc/', '/browser/ccc/', 'i') as ?author_br_iri) .
                  BIND(REPLACE(STR(?journal_iri), '/ccc/', '/browser/ccc/', 'i') as ?j_br_iri) .
                  BIND(REPLACE(STR(?j_vol_iri), '/ccc/', '/browser/ccc/', 'i') as ?j_vol_br_iri) .
                  BIND(CONCAT(?g_name,' ',?f_name) as ?author) .
            } GROUP BY ?my_iri ?id_lit ?id_issn ?short_iri ?title ?subtitle ?year ?type ?s_type ?author ?author_br_iri ?j_vol_br_iri ?j_br_iri ?journal ?journal_data ORDER BY DESC(?tot)`
          ],
          "links": {
            "author": {"field":"author_br_iri","prefix":""},
            "s_type": {"field":"type","prefix":""},
            "id_lit": {"field":"id_lit","prefix":"http://dx.doi.org/"},
            "journal": {"field":"j_br_iri","prefix":""},
            "journal_data": {"field":"j_vol_br_iri","prefix":""}
          },
          "group_by": {"keys":["title"], "concats":["author","s_type"]},
          "none_values": {"subtitle": "", "author": "", "title": "Document without title", "id_lit":"", "id_issn":"","year":"", "journal":"", "journal_data":""},

          "text_mapping": {
              "s_type":[
                  {"regex": /Expression/g, "value":"Document"},
                  {"regex": /([a-z])([A-Z])/g, "value":"$1 $2"}
              ]
          },

          "contents": {
            "extra": {
                "browser_view_switch":{
                  "labels":["Switch to metadata view","Switch to browser view"],
                  "values":["short_iri","short_iri"],
                  "regex":["br\/.*","\/browser\/ccc\/br\/.*"],
                  "query":[["SELECT ?resource WHERE {BIND(<https://w3id.org/oc/ccc/[[VAR]]> as ?resource)}"],["SELECT ?resource WHERE {BIND(<https://w3id.org/oc/ccc/[[VAR]]> as ?resource)}"]],
                  "links":["https://w3id.org/oc/ccc/[[VAR]]","https://w3id.org/oc/browser/ccc/[[VAR]]"]
                }
            },
            "header": [
                {"classes":["20px"]},
                {"fields": ["s_type"], "concat_style":{"s_type": "last"} , "classes":["doc-type"]},
                {"fields": ["FREE-TEXT","short_iri"], "values":["Corpus ID: ", null] , "classes":["identifiers"]},
                {"fields": ["id_lit"], "classes":["identifiers doi_before"] },
                {"fields": ["id_issn"], "classes":["identifiers issn_before"] },
                {"classes":["20px"]},
                {"fields": ["title"], "classes":["header-title"]},
                {"fields": ["subtitle"], "classes":["sub-header-title"]},
                {"classes":["1px"]},
                {"fields": ["author"], "concat_style":{"author": "inline"}}
            ],
            "details": [
              {"fields": ["journal"], "classes":["journal-data"]},
              {"fields": ["journal_data"], "classes":["journal-data"]},
              {"fields": ["year"], "classes":["journal-data-separator"] }
              //{"fields": ["FREE-TEXT", "EXT_DATA"], "values": ["Publisher: ", "crossref4doi.message.publisher"]},
              ],
            "metrics": [
              {"classes":["20px"]},
              {"fields": ["in_cits"], "classes": ["cited"]},
              {"classes":["5px"]},
              {"fields": ["out_cits"], "classes": ["refs"]}
            ],
            "oscar_conf": {
                "progress_loader":{
                          "visible": false,
                          "spinner": false,
                          "title":"Loading the list of Citations and References ...",
                          //"subtitle":"Be patient - this might take several seconds!"
                          //"abort":{"title":"Abort", "href_link":""}
                        }
            },
            "oscar": [
              // {
              //   "query_text": "my_iri",
              //   "rule": "doc_cites_me_list",
              //   "label":"Cited by",
              //   "config_mod" : [
      				// 			{"key":"page_limit_def" ,"value":30},
              //       //{"key":"categories.[[name,citation]].fields.[[title,Cited reference]]" ,"value":"REMOVE_ENTRY"},
      				// 			{"key":"categories.[[name,document]].fields.[[title,Year]].sort.default" ,"value":{"order": "asc"}},
      				// 			{"key":"progress_loader.visible" ,"value":false},
              //       {"key":"timeout.text" ,"value":""}
      				// 	]
              // },
              {
                "query_text": "my_iri",
                "rule": "doc_cites_list",
                "label":"References",
                "config_mod" : [
      							{"key":"page_limit_def" ,"value":30},
      							{"key":"categories.[[name,document]].fields.[[title,Cited by]].sort.default" ,"value":{"order": "desc"}},
      							{"key":"progress_loader.visible" ,"value":false},
                    {"key":"timeout.text" ,"value":""}
      					]
              },
              {
                "query_text": "my_iri",
                "rule": "mari_doc_cites_me_list",
                "label":"Citations",
                "config_mod" : [
      							{"key":"page_limit_def" ,"value":30},
                    {"key":"categories.[[name,document_intext]].fields.[[title,Year]].sort.default" ,"value":{"order": "asc"}},
      							{"key":"progress_loader.visible" ,"value":false},
                    {"key":"timeout.text" ,"value":""}
      					]
              }
            ]
    },
          "ext_data": {
            //"crossref4doi": {"name": call_crossref, "param": {"fields":["id_lit","FREE-TEXT"],"values":[null,1]}}
          }
  },
    "author": {
          "rule": "ra\/.*",
          "query": [`
            SELECT ?orcid ?author_iri ?short_iri ?author ?s_type (COUNT(distinct ?doc) AS ?num_docs) (COUNT(distinct ?cites) AS ?out_cits) (COUNT(distinct ?cited_by) AS ?in_cits_docs) (COUNT(?cited_by) AS ?in_cits_tot) WHERE {
    	         BIND(<https://w3id.org/oc/ccc/[[VAR]]> as ?author_iri) .
               BIND(REPLACE(STR(?author_iri), 'https://w3id.org/oc/ccc/', '', 'i') as ?short_iri) .
               ?author_iri foaf:familyName ?fname .
    	         ?author_iri foaf:givenName ?name .
    	         BIND(CONCAT(STR(?name),' ', STR(?fname)) as ?author) .
    	         OPTIONAL {?role pro:isHeldBy ?author_iri ; pro:withRole ?aut_role.
                        ?doc pro:isDocumentContextFor ?role.
                        BIND(REPLACE(STR(?aut_role), 'http://purl.org/spar/pro/', '', 'i') as ?s_type) .
                        OPTIONAL {?doc cito:cites ?cites .}
                        OPTIONAL {?cited_by cito:cites ?doc .}
                  }

               OPTIONAL {
      	          ?author_iri datacite:hasIdentifier [
      		            datacite:usesIdentifierScheme datacite:orcid ;
  			              literal:hasLiteralValue ?orcid
                  ]
    	         }
             } GROUP BY ?orcid ?author_iri ?short_iri ?author ?s_type ?num_docs ?out_cits ?in_cits_docs
             `
          ],
          "links": {
            //"author": {"field":"author_iri"},
            "title": {"field":"doc"},
            "orcid": {"field":"orcid","prefix":"https://orcid.org/"}
          },
          "group_by": {"keys":["author"], "concats":["doc","title","year"]},

          "contents": {
            "extra": {
                "browser_view_switch":{
                    "labels":["ldd","Browser"],
                    "values":["short_iri","short_iri"],
                    "regex":["w3id.org\/oc\/ccc\/ra\/.*","w3id.org\/oc\/browser\/ccc\/ra\/.*"],
                    "query":[["PREFIX pro:<http://purl.org/spar/pro/> SELECT ?role WHERE {?role pro:isHeldBy <https://w3id.org/oc/ccc[[VAR]]>. ?role pro:withRole pro:author . }"],["SELECT ?role WHERE {BIND(<https://w3id.org/oc/ccc[[VAR]]> as ?role)}"]],
                    "links":["https://w3id.org/oc/ccc[[VAR]]","https://w3id.org/oc/browser/ccc[[VAR]]"]
                }
            },
            "header": [
              {"classes":["20px"]},
              {"fields": ["s_type"], "concat_style":{"s_type": "last"} , "classes":["doc-type"]},
              {"fields": ["FREE-TEXT","short_iri"], "values":["Corpus ID: ", null] , "classes":["identifiers author_ids"]},
              {"fields": ["orcid"], "classes":["identifiers author_ids orcid_before"]},
              {"classes":["20px"]},
              {"classes":["20px"]},
              {"fields": ["author"], "classes":["header-title wrapline"]}
            ],
            "details": [


            ],
            "metrics": [
                {"classes":["20px"]},
                {"fields": ["num_docs"], "classes": ["num_docs"]},
                {"classes":["10px"]},
                //{"fields": ["FREE-TEXT","in_cits_tot","FREE-TEXT"], "values": ["Cited ",null," number of times"], "classes": ["metric-entry","imp-value","metric-entry"]},
                {"fields": ["in_cits_docs"], "classes": ["cited"]}
                //{"classes":["5px"]}
                //{"fields": ["FREE-TEXT","in_cits_docs","FREE-TEXT"], "values": ["\xa0\xa0\xa0 by ",null," different documents"], "classes": ["metric-entry","imp-value","metric-entry"]}
            ],
            "oscar_conf": {
                "progress_loader":{
                          "visible": false,
                          "spinner": false,
                          "title":"Loading the list of Documents ...",
                          //"subtitle":"Be patient - this might take several seconds!"
                          //"abort":{"title":"Abort", "href_link":""}
                        }
            },
            "oscar": [
              {
                "query_text": "author_iri",
                "rule": "author_works",
                "label":"Author's documents",
                "config_mod" : [
      							{"key":"categories.[[name,document]].fields.[[title,Year]]" ,"value":"REMOVE_ENTRY"},
      							{"key":"page_limit_def" ,"value":20},
      							{"key":"categories.[[name,document]].fields.[[title,Year]].sort.default" ,"value":{"order": "desc"}},
                    {"key":"progress_loader.visible" ,"value":false},
                    {"key":"timeout.text" ,"value":""}
      					]
              }
            ]
          }
        },
    "role": {
          "rule": "ar\/.*",
          "query": [`
            SELECT ?role_iri ?short_iri ?s_type ?author ?author_br_iri ?title ?orcid ?doi ?doc_ref ?doc_br_iri ?year ?j_vol_br_iri ?j_br_iri ?journal ?journal_data
            WHERE {
               BIND(<https://w3id.org/oc/ccc/[[VAR]]> as ?role_iri) .
               ?role_iri pro:isHeldBy ?author_iri ;
                     pro:withRole ?aut_role ;
                     ^pro:isDocumentContextFor ?doc ;
                     rdf:type ?type .
               OPTIONAL {?doc dcterms:title ?doc_ref } .
               OPTIONAL {?doc frbr:partOf+ ?journal_iri .
                 ?journal_iri a fabio:Journal ; dcterms:title ?journal .
                 OPTIONAL {?doc prism:publicationDate ?year } .
                 OPTIONAL {
                  ?doc frbr:partOf+ ?j_vol_iri .
                  ?j_vol_iri a fabio:JournalVolume ; fabio:hasSequenceIdentifier ?volume .
                  ?doc frbr:embodiment ?manifestation .
                  ?manifestation prism:startingPage ?start ; prism:endingPage ?end .
                  BIND(CONCAT(', ', ?volume,': ',?start,'-',?end) as ?journal_data) .
                 }
               } .

               BIND('[[VAR]]' as ?short_iri) .
               BIND("role" as ?s_type) .
               BIND(REPLACE(STR(?aut_role), 'http://purl.org/spar/pro/', '', 'i') as ?r_type) .
               ?author_iri foaf:familyName ?fname .
    	         ?author_iri foaf:givenName ?name .
               OPTIONAL {
      	          ?author_iri datacite:hasIdentifier [
      		            datacite:usesIdentifierScheme datacite:orcid ;
  			              literal:hasLiteralValue ?orcid
                  ]
    	         }
               OPTIONAL {
                   ?doc datacite:hasIdentifier [
                   datacite:usesIdentifierScheme datacite:doi ;
                   literal:hasLiteralValue ?doi
                   ] .
                 }
    	         BIND(CONCAT(STR(?name),' ', STR(?fname)) as ?author) .
               BIND(CONCAT(STR(?author), ', ', STR(?r_type), ' of ' ) as ?title) .
               BIND(REPLACE(STR(?author_iri), '/ccc/', '/browser/ccc/', 'i') as ?author_br_iri) .
               BIND(REPLACE(STR(?doc), '/ccc/', '/browser/ccc/', 'i') as ?doc_br_iri) .
               BIND(REPLACE(STR(?journal_iri), '/ccc/', '/browser/ccc/', 'i') as ?j_br_iri) .
               BIND(REPLACE(STR(?j_vol_iri), '/ccc/', '/browser/ccc/', 'i') as ?j_vol_br_iri) .
             }`
          ],
          "links": {
            "doc_ref": {"field":"doc_br_iri","prefix":""},
            "doi": {"field":"doi","prefix":"http://dx.doi.org/"},
            "orcid": {"field":"orcid","prefix":"https://orcid.org/"},
            "journal": {"field":"j_br_iri","prefix":""},
            "journal_data": {"field":"j_vol_br_iri","prefix":""}
          },
          "group_by": {"keys":["title"], "concats":["doc","title","year"]},
          "none_values": {"title": "Author without name", "doi":"", "year":"", "journal":"", "journal_data":""},
          "contents": {
            "extra": {
                "browser_view_switch":{
                    "labels":["ldd","Browser"],
                    "values":["short_iri","short_iri"],
                    "regex":["w3id.org\/oc\/ccc\/ar\/.*","w3id.org\/oc\/browser\/ccc\/ar\/.*"],
                    "query":[["PREFIX pro:<http://purl.org/spar/pro/> SELECT ?role WHERE {?role pro:isHeldBy <https://w3id.org/oc/ccc[[VAR]]>. ?role pro:withRole pro:author . }"],["SELECT ?role WHERE {BIND(<https://w3id.org/oc/ccc[[VAR]]> as ?role)}"]],
                    "links":["https://w3id.org/oc/ccc[[VAR]]","https://w3id.org/oc/browser/ccc[[VAR]]"]
                }
            },
            "header": [
              {"classes":["20px"]},
              {"fields": ["s_type"], "concat_style":{"s_type": "last"} , "classes":["doc-type"]},
              {"fields": ["FREE-TEXT","short_iri"], "values":["Corpus ID: ", null] , "classes":["identifiers author_ids"]},
              {"fields": ["orcid"], "classes":["identifiers author_ids orcid_before"]},
              {"classes":["20px"]},
              {"classes":["20px"]},
              {"fields": ["title"], "classes":["header-title wrapline"]},
              {"fields": ["doc_ref"], "classes":["journal-data"]}
            ],
            "details": [
              {"fields": ["journal"], "classes":["journal-data"]},
              {"fields": ["journal_data"], "classes":["journal-data"]},
              {"fields": ["year"], "classes":["journal-data-separator"]},
              {"fields": ["doi"], "classes":["identifiers doi_before"] }

            ],
            "metrics": []
            // "oscar_conf": {
            //     "progress_loader":{
            //               "visible": false,
            //               "spinner": false,
            //               "title":"Loading the list of Documents ...",
            //               //"subtitle":"Be patient - this might take several seconds!"
            //               //"abort":{"title":"Abort", "href_link":""}
            //             }
            // },
            // "oscar": [
            //   {
            //     "query_text": "author_iri",
            //     "rule": "author_works",
            //     "label":"Author's documents",
            //     "config_mod" : [
      			// 				{"key":"categories.[[name,document]].fields.[[title,Year]]" ,"value":"REMOVE_ENTRY"},
      			// 				{"key":"page_limit_def" ,"value":20},
      			// 				{"key":"categories.[[name,document]].fields.[[title,Year]].sort.default" ,"value":{"order": "desc"}},
            //         {"key":"progress_loader.visible" ,"value":false},
            //         {"key":"timeout.text" ,"value":""}
      			// 		]
            //   }
            // ]
          }
        },
    "citation": {
          "rule": "ci\/.*",
          "query": [`
              SELECT ?short_iri ?s_type ?title ?oci ?citing_br_iri ?cited_br_iri ?year ?intrepid
              WHERE {
                BIND(<https://w3id.org/oc/ccc/[[VAR]]> as ?my_iri) .
                BIND('[[VAR]]' as ?short_iri) .
                BIND(REPLACE(STR(?short_iri), 'ci/', '', 'i') as ?oci) .
                ?my_iri rdf:type ?type .
                BIND(REPLACE(STR(?type), 'http://purl.org/spar/cito/', '', 'i') as ?s_type) .
                BIND(CONCAT('Citation ', STR(?oci)) as ?title) .

                ?my_iri cito:hasCitingEntity ?citing_iri ; cito:hasCitedEntity ?cited_iri .
                BIND(REPLACE(STR(?citing_iri), '/ccc/', '/browser/ccc/', 'i') as ?citing_br_iri) .
                BIND(REPLACE(STR(?cited_iri), '/ccc/', '/browser/ccc/', 'i') as ?cited_br_iri) .

                OPTIONAL {
                  ?citing_iri dcterms:title ?citing_title .
                }
                OPTIONAL {
                  ?cited_iri dcterms:title ?cited_title .
                }
              }
            `],
          "links": {
            "s_type": {"field":"type","prefix":"http://purl.org/spar/cito/"}
          },
          "group_by": {
            "keys":["title"], "concats":["author","s_type"]
          },
          "none_values": {},
          "contents": {
            "extra": {
                "browser_view_switch":{
                  "labels":["Switch to metadata view","Switch to browser view"],
                  "values":["short_iri","short_iri"],
                  "regex":["ci\/.*","\/browser\/ccc\/ci\/.*"],
                  "query":[["SELECT ?resource WHERE {BIND(<https://w3id.org/oc/ccc/[[VAR]]> as ?resource)}"],["SELECT ?resource WHERE {BIND(<https://w3id.org/oc/ccc/[[VAR]]> as ?resource)}"]],
                  "links":["https://w3id.org/oc/ccc/[[VAR]]","https://w3id.org/oc/browser/ccc/[[VAR]]"]
                }
            },
            "header": [
                {"classes":["20px"]},
                {"fields": ["s_type"], "concat_style":{"s_type": "last"} , "classes":["doc-type"]},
                {"fields": ["FREE-TEXT","short_iri"], "values":["Corpus ID: ", null] , "classes":["identifiers"]},
                {"fields": ["oci"], "classes":["identifiers oci_before"] },
                {"classes":["20px"]},
                {"classes":["20px"]},
                {"fields": ["title"], "classes":["header-title"]},
                {"classes":["20px"]},
                {"classes":["1px"]}
            ],
            "details": [
              // {"fields": ["journal"], "classes":["journal-data"]},
              // {"fields": ["journal_data"], "classes":["journal-data"]},
              // {"fields": ["year"], "classes":["journal-data-separator"] }
              //{"fields": ["FREE-TEXT", "EXT_DATA"], "values": ["Publisher: ", "crossref4doi.message.publisher"]},
              ]
          }
    }
    // ,
    // "citation": {
    //       "rule": "",
    //       "query": [``],
    //       "links": {},
    //       "group_by": {},
    //       "none_values": {},
    //       "contents": {}
    // }
  }
}



//"FUNC" {"name": call_crossref, "param":{"fields":[],"vlaues":[]}}
function call_crossref(str_doi, field){
  var call_crossref_api = "https://api.crossref.org/works/";
  var call_url =  call_crossref_api+ encodeURIComponent(str_doi);

  var result_data = "";
  $.ajax({
        dataType: "json",
        url: call_url,
        type: 'GET',
        async: false,
        success: function( res_obj ) {
            if (field == 1) {
              result_data = res_obj;
            }else {
              if (!b_util.is_undefined_key(res_obj,field)) {
                result_data = b_util.get_obj_key_val(res_obj,field);
              }
            }
            //console.log(result_data);
            //browser._update_page();
        }
   });
   return result_data;
}


//Heuristics
function more_than_zero(val){
  return parseInt(val) > 0
}
