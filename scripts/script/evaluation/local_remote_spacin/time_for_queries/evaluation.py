from os import listdir
from os.path import isfile, join
import json
import pandas as pd
from script.support.queryinterface import LocalQuery, RemoteQuery
import tqdm
import datetime
import numpy as np

np.set_printoptions(precision=2)
from script.ccc.conf_spacin import orcid_conf_path
from copy import deepcopy
from script.spacin.orcidfinder import ORCIDFinder

query_interface_local = LocalQuery(reperr=None, repok=None, threshold=0)
query_interface_remote = RemoteQuery(0.95,
                                    headers={"User-Agent": "SPACIN / CrossrefProcessor (via OpenCitations - "
                                    "http://opencitations.net; mailto:contact@opencitations.net)"},
                                    sec_to_wait=10,
                                    max_iteration=6,
                                    timeout=30,
                                    reperr=None,
                                    repok=None,
                                    is_json=True)

orcid_finder_local = ORCIDFinder(orcid_conf_path, query_interface='local')
orcid_finder_remote = ORCIDFinder(orcid_conf_path, query_interface='remote')

def extract_references():
    explicit_dois = []
    bibrefs = []

    json_files = [f for f in listdir('/home/gabriele/Universita/Ricerca/OpenCitations CCC/progetti/ccc/scripts/script/evaluation/local_remote_spacin/time_for_queries/BEE_json') if isfile(join('/home/gabriele/Universita/Ricerca/OpenCitations CCC/progetti/ccc/scripts/script/evaluation/local_remote_spacin/time_for_queries/BEE_json', f))]
    for f in json_files:
        file_content = json.load(open(join('/home/gabriele/Universita/Ricerca/OpenCitations CCC/progetti/ccc/scripts/script/evaluation/local_remote_spacin/time_for_queries/BEE_json', f), 'r'))

        for reference in file_content['references']:
            if 'bibentry' in reference and 'DOI' not in reference['bibentry']:
                bibrefs.append(reference['bibentry'])

            if 'doi' in reference:
                explicit_dois.append(reference['doi'])


    df_doi = pd.DataFrame({'doi':explicit_dois})
    df_doi.to_csv('/home/gabriele/Universita/Ricerca/OpenCitations CCC/progetti/ccc/scripts/script/evaluation/local_remote_spacin/time_for_queries/dataset_doi.csv', index=False)

    df_bibref = pd.DataFrame({'bibref': bibrefs })
    df_bibref.to_csv('/home/gabriele/Universita/Ricerca/OpenCitations CCC/progetti/ccc/scripts/script/evaluation/local_remote_spacin/time_for_queries/dataset_bibref.csv', index=False)



def query_local_bibref(df):
    start = datetime.datetime.now()
    for idx, row in tqdm.tqdm(df.iterrows()):
        query_interface_local.get_doi_from_bibref(row['bibref'])

    end = datetime.datetime.now()
    print("[local index - BIBREF] Total query {}".format(len(df)))
    print("[local index - BIBREF] Total seconds spent {}".format((end-start).total_seconds()))
    print("[local index - BIBREF] Mean seconds for a query {}".format((end-start).total_seconds()/len(df)))


def query_remote_bibref(df):
    toquery = []
    for idx, row in df.iterrows():
        if "DOI" in row['bibref']:
            continue
        else:
            toquery.append(row['bibref'])
    df = pd.DataFrame({'bibref': toquery})

    start = datetime.datetime.now()
    for idx, row in tqdm.tqdm(df.iterrows()):

        query_interface_remote.get_data_crossref_bibref(row['bibref'])

    end = datetime.datetime.now()
    print("[remote API - BIBREF] Total query {}".format(len(df)))
    print("[remote API - BIBREF] Total seconds spent {}".format((end - start).total_seconds()))
    print("[remote API - BIBREF] Mean seconds for a query {}".format((end - start).total_seconds() / len(df)))


def query_local_doi(df):
    start = datetime.datetime.now()
    for idx, row in tqdm.tqdm(df.iterrows()):
        query_interface_local.get_data_crossref_doi(row['doi'])

    end = datetime.datetime.now()
    print("[local index - DOI] Total query {}".format(len(df)))
    print("[local index - DOI] Total seconds spent {}".format((end - start).total_seconds()))
    print("[local index - DOI] Mean seconds for a query {}".format((end - start).total_seconds() / len(df)))


def query_remote_doi(df):
    start = datetime.datetime.now()
    for idx, row in tqdm.tqdm(df.iterrows()):
        try:
            query_interface_remote.get_data_crossref_doi(row['doi'])
        except:
            continue

    end = datetime.datetime.now()
    print("[remote API - DOI] Total query {}".format(len(df)))
    print("[remote API - DOI] Total seconds spent {}".format((end - start).total_seconds()))
    print("[remote API - DOI] Mean seconds for a query {}".format((end - start).total_seconds() / len(df)))

def query_local_orcid(df):
    start = datetime.datetime.now()
    for idx, row in tqdm.tqdm(df.iterrows()):
        try:
            names = row['names'].replace("[","").replace("]", "").split(",")
            print(orcid_finder_local.get_orcid_ids(row['doi'], names))
        except:
            continue

    end = datetime.datetime.now()
    print("[local index - ORCID] Total query {}".format(len(df)))
    print("[local index - ORCID] Total seconds spent {}".format((end - start).total_seconds()))
    print("[local index- ORCID] Mean seconds for a query {}".format((end - start).total_seconds() / len(df)))


def query_remote_orcid(df):
    start = datetime.datetime.now()
    for idx, row in tqdm.tqdm(df.iterrows()):
        try:
            names = row['names'].replace("[","").replace("]", "").split(",")
            orcid_finder_remote.get_orcid_ids(row['doi'], names)
        except:
            continue

    end = datetime.datetime.now()
    print("[remote API - ORCID] Total query {}".format(len(df)))
    print("[remote API - ORCID] Total seconds spent {}".format((end - start).total_seconds()))
    print("[remote API - ORCID] Mean seconds for a query {}".format((end - start).total_seconds() / len(df)))

def main():
    extract_references()

    df_doi = pd.read_csv('/home/gabriele/Universita/Ricerca/OpenCitations CCC/progetti/ccc/scripts/script/evaluation/local_remote_spacin/time_for_queries/dataset_doi.csv')
    df_bibref = pd.read_csv('/home/gabriele/Universita/Ricerca/OpenCitations CCC/progetti/ccc/scripts/script/evaluation/local_remote_spacin/time_for_queries/dataset_bibref.csv')
    df_orcid = pd.read_csv('/home/gabriele/Universita/Ricerca/OpenCitations CCC/progetti/ccc/scripts/script/evaluation/local_remote_spacin/time_for_queries/dataset_orcid.csv', sep=';')

    print("\n---\n")
    query_local_orcid(df_orcid)
    print("\n---\n")
    query_remote_orcid(df_orcid)
    #query_local_doi(df_doi)
    print("\n---\n")
    #query_local_bibref(df_bibref)
    print("\n---\n")
    #query_remote_bibref(df_bibref)
    print("\n---\n")
    #query_remote_doi(df_doi)
    print("\n---\n")



if __name__ == '__main__':
    print("Start at: ", datetime.datetime.now())
    main()
    print("End at: ", datetime.datetime.now())

