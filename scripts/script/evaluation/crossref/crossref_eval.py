import requests , json , csv , os.path
from urllib.parse import quote
from SPARQLWrapper import SPARQLWrapper, JSON

sparql = SPARQLWrapper("http://localhost:9999/blazegraph/sparql")
sparql.setQuery("""
    SELECT distinct ?doiLiteral ?beLiteral
    WHERE {?br <http://purl.org/spar/datacite/hasIdentifier> ?doi .
       ?be <http://purl.org/spar/biro/references> ?br ; <http://purl.org/spar/c4o/hasContent> ?beLiteral .
       ?doi <http://purl.org/spar/datacite/usesIdentifierScheme> <http://purl.org/spar/datacite/doi> ; <http://www.essepuntato.it/2010/06/literalreification/hasLiteralValue> ?doiLiteral.}
    LIMIT 1000
""")
sparql.setReturnFormat(JSON)
data = sparql.query().convert()

# with open('be_list.json') as json_file:
#     data = json.load(json_file)
# with open('results_bibliographic_parameter.csv', 'w', newline='') as file:
#     writer = csv.writer(file)
#     writer.writerow(["known_doi", "retrieved_doi", "score", "query_be"])
#     for result in data["results"]["bindings"]:
#         doi, be = result["doiLiteral"]["value"], result["beLiteral"]["value"]
#         response = requests.get("https://api.crossref.org/works?query.bibliographic="+quote(be))
#         records = response.json()
#         if records["status"] == 'ok':
#             best_match_doi , score = records["message"]["items"][0]["DOI"] , records["message"]["items"][0]["score"]
#             writer.writerow([doi, best_match_doi, score, be])
#             print(doi, best_match_doi, score, be,'\n')

with open('results_bibliographic_parameter.csv', 'r') as file:
    reader = csv.reader(file)
    for row in reader:
        if row[0].lower().strip() != row[1].lower().strip() :
            print(row[3])
