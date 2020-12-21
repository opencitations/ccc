# CCC spacin configuration
base_dir = "/srv/data/ccc/"
base_iri = "https://w3id.org/oc/ccc/"
triplestore_url = "http://localhost:3002/blazegraph/sparql"
triplestore_url_real = "https://w3id.org/oc/ccc/sparql"
context_path = "https://w3id.org/oc/ccc/context.json"
context_file_path = "/srv/data/ccc/context.json"
info_dir = "/srv/share/ccc/id-counter/"
temp_dir_for_rdf_loading = "/tmp/"
orcid_conf_path = "/srv/dev/ccc/scripts/script/spacin/orcid_conf.json"
reference_dir = "/srv/share/ccc/ref/todo/"
reference_dir_error = "/srv/data/ccc/bee/err/"
reference_dir_done = "/srv/data/ccc/bee/done/"
dataset_home = "https://w3id.org/oc/ccc"
dir_split_number = 10000  # This must be multiple of the following one
items_per_file = 1000
default_dir = ""
do_parallel = False
# the following are not used in ccc
supplier_dir = {
    "101": "01110",
    "102": "01120",
    "103": "01130",
    "104": "01140",
    "105": "01150",
    "106": "01160",
    "107": "01170",
    "108": "01180",
    "109": "01190",
    "110": "01910",
    "111": "01210",
    "112": "01220",
    "113": "01230",
    "114": "01240",
    "115": "01250",
    "116": "01260",
    "117": "01270",
    "118": "01280",
    "119": "01290",
    "120": "01920",
    "121": "01310",
    "122": "01320",
    "123": "01330",
    "124": "01340",
    "125": "01350",
    "126": "01360",
    "127": "01370",
    "128": "01380",
    "129": "01390",
    "130": "01930"
}

interface = "eth0"
sharing_dir = "test/data/"

crossref_query_interface_type = 'local'
orcid_query_interface_type = 'local'