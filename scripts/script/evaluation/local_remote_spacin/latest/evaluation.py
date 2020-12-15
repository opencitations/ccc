from os import listdir
from os.path import isfile, join
import json
import pandas as pd
from script.support.queryinterface import LocalQuery, RemoteQuery
import tqdm
import datetime
import numpy as np

np.set_printoptions(precision=2)
from copy import deepcopy
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


def extract_references():
    explicit_dois = []
    bibrefs = []

    json_files = [f for f in listdir('/home/gabriele/Universita/Ricerca/OpenCitations CCC/progetti/ccc/scripts/script/evaluation/local_remote_spacin/BEE_json') if isfile(join('/home/gabriele/Universita/Ricerca/OpenCitations CCC/progetti/ccc/scripts/script/evaluation/local_remote_spacin/BEE_json', f))]
    for f in json_files:
        file_content = json.load(open(join('/home/gabriele/Universita/Ricerca/OpenCitations CCC/progetti/ccc/scripts/script/evaluation/local_remote_spacin/','BEE_json', f), 'r'))
        for reference in file_content['references']:
            if 'bibentry' in reference:
                bibrefs.append(reference['bibentry'])
            else:
                bibrefs.append("")

            if 'doi' in reference:
                explicit_dois.append(reference['doi'])
            else:
                explicit_dois.append("")

    df = pd.DataFrame({'explicit_doi':explicit_dois, 'bibref': bibrefs })
    df.to_csv('evaluation_dataset.csv', index=False)

def retrieve_local_doi(bibref):
    return query_interface_local.get_doi_from_bibref(bibref)

def retrieve_remote_doi(bibref):
    return query_interface_remote.get_data_crossref_bibref(bibref)['DOI']


def query_local():

    df = pd.read_csv('/home/gabriele/Universita/Ricerca/OpenCitations CCC/progetti/ccc/scripts/script/evaluation/local_remote_spacin/round3/evaluation_dataset_plus_remote_annotated.csv')
    df['retrieved_local_doi'] = ""
    df['local_score'] = 0

    for idx, row in tqdm.tqdm(df.iterrows()):
        df['retrieved_local_doi'].iloc[idx], df['local_score'].iloc[idx] = retrieve_local_doi(row['bibref'])

    df.to_csv('/home/gabriele/Universita/Ricerca/OpenCitations CCC/progetti/ccc/scripts/script/evaluation/local_remote_spacin/round3/evaluation_dataset_plus_score.csv', index=False)


def query_remote():
    df = pd.read_csv('evaluation_dataset_plus_local.csv')
    df['retrieved_remote_doi'] = ""

    for idx, row in tqdm.tqdm(df.iterrows()):
        try:
            row['retrieved_remote_doi'] = retrieve_remote_doi(row['bibref'])
        except Exception as e:
            row['retrieved_remote_doi'] = 'EXCEPTION: {}'.format(e)
    df.to_csv('evaluation_dataset_plus_remote.csv', index=False)

def preprocessing_1(df):
    """ Preprocess the dataset according to the assumptions made in the experimental setup """

    df = deepcopy(df[df['manual_doi'] != "???"])

    return df


def preprocessing(df):
    """ Preprocess the dataset according to the assumptions made in the experimental setup """

    temp = deepcopy(df[df['manual_doi'] != "???"])
    n_of_not_exist = 0
    temp['exists_doi_in_crossref'] = 0
    for idx, row in temp.iterrows():
        if query_interface_local.check_doi_in_collection(row['manual_doi']):
            temp.loc[temp['manual_doi'] == row['manual_doi'], 'exists_doi_in_crossref'] = 1
        else:
            n_of_not_exist += 1
    temp.to_csv('evaluation_dataset_without_notfoundmanual_with_incrossref.csv', index=False)
    final_df = temp[temp['exists_doi_in_crossref']==1]
    del final_df['exists_doi_in_crossref']
    final_df = final_df.drop_duplicates()
    final_df.to_csv('preprocessed.csv')
    #print(f"Finished: {n_of_not_exist} DOI not in crossref")
    #print(f"Total record for the experimentation: {len(final_df)}")

    return final_df

def precision(relevant, retrieved):
    return len(set(relevant).intersection(set(retrieved)))/len(set(retrieved))
def recall(relevant, retrieved):
    return len(set(relevant).intersection(set(retrieved))) /len(set(relevant))
def f_1(p, r):
    return 2* ((p*r)/(p+r))

def compute_metrics(df, threshold):
    total_rows = len(df)
    n_corresponding_local_remote = 0
    n_corresponding_local_manual = 0
    n_corresponding_remote_manual = 0
    n_local_is_correct_and_remote_is_not = 0
    n_remote_is_correct_and_local_is_not = 0
    n_both_wrong_but_equals = 0
    n_both_wrong_but_different = 0
    n_both_equals_and_correct = 0
    n_local_supplement = 0
    n_remote_supplement = 0
    n_local_wrong = 0
    n_remote_wrong = 0
    scartati = 0
    correct_mean_score = []
    wrong_mean_score = []

    relevant = []
    retrieved = []
    retrieved_crossref = []

    for idx, row in df.iterrows():

        retrieved_crossref.append(row['retrieved_remote_doi'].strip().lower())
        relevant.append(row['manual_doi'].strip().lower())
        skip_local = False

        if row['retrieved_local_doi'] != row['retrieved_local_doi'] or row['local_score'] < threshold:
            #print("Scarto: ")
            for r in query_interface_local.crossref_query_instance.search(fl='*,score', q='id:"{}"'.format(row['retrieved_local_doi'])):
                retr = r['bibref'][0]
                break
            #print("\t ", row['bibref'])
            #print("\t ", retr)
            scartati += 1
            skip_local = True
            #continue

        else:
            local_doi = row['retrieved_local_doi'].strip().lower()
            retrieved.append(local_doi)


        manual_doi = row['manual_doi'].strip().lower()
        remote_doi = row['retrieved_remote_doi'].strip().lower()
        local_is_correct = False
        remote_is_correct = False
        local_remote_equals = False


        if manual_doi in local_doi and manual_doi != local_doi and not skip_local:
            n_local_supplement += 1

        if manual_doi in remote_doi and manual_doi != remote_doi:
            n_remote_supplement += 1

        if local_doi == manual_doi and not skip_local:
            n_corresponding_local_manual += 1
            local_is_correct = True
            correct_mean_score += [row['local_score']]


        else:
            if not skip_local:
                n_local_wrong += 1
                wrong_mean_score += [row['local_score']]
                for r in query_interface_local.crossref_query_instance.search(fl='*,score', q='id:"{}"'.format(row['retrieved_local_doi'])):
                    retr = r['bibref']
                    break
                #print("Da cercare: {},  trovato: {}".format(row['bibref'], retr))


        if remote_doi == manual_doi:
            n_corresponding_remote_manual += 1
            remote_is_correct = True
        else:
            n_remote_wrong += 1

        if remote_doi == local_doi:
            local_remote_equals = True
            if local_is_correct and remote_is_correct:
                n_both_equals_and_correct +=1

        if remote_doi == local_doi:
            n_corresponding_local_remote += 1

        if local_is_correct and not remote_is_correct:
            n_local_is_correct_and_remote_is_not += 1

        if not local_is_correct and remote_is_correct:
            n_remote_is_correct_and_local_is_not += 1

        if not local_is_correct and not remote_is_correct:
            if local_remote_equals:
                n_both_wrong_but_equals += 1
            else:
                n_both_wrong_but_different += 1

    total_rows -= scartati

    print(f"- Numero di volte in cui il DOI locale è corretto e quello remoto no: {n_local_is_correct_and_remote_is_not}")
    print(f"- Numero di volte in cui il DOI remoto è corretto e quello locale no: {n_remote_is_correct_and_local_is_not}")
    print(f"- Numero di volte in cui sono entrambi errati e identici: {n_both_wrong_but_equals}")
    print(f"- Numero di volte in cui sono entrambi errati ma differenti: {n_both_wrong_but_different}")
    print(f"- Numero di volte in cui sono entrambi corretti e identici: {n_both_equals_and_correct}")
    print(f"- Numero di volte in cui vengono restituiti supplementi dall'indice locale: {n_local_supplement}")
    print(f"- Numero di volte in cui vengono restituiti supplementi dalle API: {n_remote_supplement}")
    print(f"- Percentuale locali sbagliati che sono supplementi (sul totale): {n_local_supplement*100/total_rows:.2f}")
    print(f"- Percentuale remoti sbagliati che sono supplementi (sul totale): {n_remote_supplement*100/total_rows:.2f}")
    print(f"- Percentuale locali sbagliati che sono supplementi (sui locali sbagliati): {n_local_supplement * 100 / n_local_wrong:.2f}")
    print(f"- Percentuale remoti sbagliati che sono supplementi (sui remoti sbagliati): {n_remote_supplement * 100 / n_remote_wrong:.2f}")

    print(f"- Percentuale di corrispondenza tra DOI locale e DOI manuale (quanta - correttezza usando l'indice): {n_corresponding_local_manual * 100 / total_rows:.2f}")
    print(f"- Percentuale di corrispondenza tra DOI remoto e DOI manuale (quanta correttezza usando le API remote): {n_corresponding_remote_manual * 100 / total_rows:.2f}")
    print(f"- Percentuale di corrispondenza tra DOI remoto e DOI locale (quanta corrispondenza tra l'indice e le API): {n_corresponding_local_remote * 100 / total_rows:.2f}")
    n_wrong = n_both_wrong_but_equals + n_both_wrong_but_different
    print(f"- Percentuale entrambi corretti: {n_both_equals_and_correct*100/total_rows:.2f}")
    print(f"- Percentuale entrambi errati e identici: {n_both_wrong_but_equals*100/total_rows:.2f} ")
    print(f"- Percentuale entrambi errati ma differenti: {n_both_wrong_but_different*100/total_rows:.2f} ")
    print("- Media score nei corretti {:.2f}".format(np.mean(correct_mean_score)))
    print("- Media score negli sbagliati {:.2f}".format(np.mean(wrong_mean_score)))
    print("- Scartati {}".format(scartati))
    print("")

    print("Se sbagliano entrambi:")
    print(f"- Percentuale entrambi errati e identici su tutti gli errati: {n_both_wrong_but_equals*100/n_wrong:.2f} ")
    print(f"- Percentuale entrambi errati ma differenti su tutti gli errati: {n_both_wrong_but_different*100/n_wrong:.2f} ")

    print("")
    print("Metriche riassuntive:")
    print("")
    p = precision(relevant, retrieved)
    r = recall(relevant, retrieved)
    f1 = f_1(p, r)

    p_crossref = precision(relevant, retrieved_crossref)
    r_crossref = recall(relevant, retrieved_crossref)
    f1_crossref = f_1(p_crossref, r_crossref)

    df_metrics = pd.DataFrame(columns=['', 'Local', 'Crossref'])
    df_metrics.loc[0] = ['Precision', p, p_crossref]
    df_metrics.loc[1] = ['Recall', r, r_crossref]
    df_metrics.loc[2] = ['F1', f1, f1_crossref]
    print(df_metrics.set_index('').to_markdown())
    print("")

def find_best_threshold(df):
    train, test = \
        np.split(df.sample(frac=1, random_state=42),
                 [int(.8 * len(df))])

    thresholds = range(0, 50, 1)
    max_fscore = 0

    df_scores = pd.DataFrame(columns=['θ', 'F1', 'P', 'R'])

    for i, threshold in enumerate(thresholds):
        scartati = 0
        relevant = []
        retrieved = []

        for idx, row in train.iterrows():
            relevant.append(row['manual_doi'])

            if row['retrieved_local_doi'] != row['retrieved_local_doi'] or row['local_score'] < threshold:
                # print("Scarto: ")
                for r in query_interface_local.crossref_query_instance.search(fl='*,score', q='id:"{}"'.format(
                        row['retrieved_local_doi'])):
                    retr = r['bibref'][0]
                    break
                # print("\t ", row['bibref'])
                # print("\t ", retr)
                scartati += 1
                continue

            else:
                local_doi = row['retrieved_local_doi'].strip().lower()
                retrieved.append(local_doi)

            manual_doi = row['manual_doi'].strip().lower()
            remote_doi = row['retrieved_remote_doi'].strip().lower()
            local_is_correct = False
            remote_is_correct = False
            local_remote_equals = False

        p = precision(relevant, retrieved)
        r = recall(relevant, retrieved)
        fscore = f_1(p, r)
        df_scores.loc[i] = [threshold, fscore, p, r]

        print("{} {:.3f} {:.3f} {:.3f}".format(threshold, fscore, p, r))
        if fscore > max_fscore:
            max_fscore = fscore
            best_threshold = threshold

    print("Max f_score (train): {}".format(max_fscore))
    print("Best threshold on train: {}".format(best_threshold))

    retrieved = []
    relevant = []
    for idx, row in test.iterrows():

        if row['retrieved_local_doi'] != row['retrieved_local_doi'] or row['local_score'] < best_threshold:
            relevant.append(row['manual_doi'])
            continue

        else:
            local_doi = row['retrieved_local_doi'].strip().lower()
            retrieved.append(local_doi)
            relevant.append(row['manual_doi'])
    p = precision(relevant, retrieved)
    r = recall(relevant, retrieved)
    f1_valid = f_1(p, r)
    print("F1 on validation: {}".format(f1_valid))
    print("Precision on validation: {}".format(p))
    print("Recall on validation: {}".format(r))
    print()

    print(df_scores.set_index('θ').to_markdown())
    return best_threshold

def main():

    df = pd.read_csv('/home/gabriele/Universita/Ricerca/OpenCitations CCC/progetti/ccc/scripts/script/evaluation/local_remote_spacin/round3/evaluation_dataset_plus_score.csv')
    df = df.drop_duplicates()
    df = preprocessing_1(df)
    print("without deleting missing DOI in crossref")
    print()
    compute_metrics(df, 0)
    print("Cerco soglia...")
    threshold = find_best_threshold(df)
    compute_metrics(df, threshold)


    df = pd.read_csv('/home/gabriele/Universita/Ricerca/OpenCitations CCC/progetti/ccc/scripts/script/evaluation/local_remote_spacin/round3/evaluation_dataset_plus_score.csv')
    df = df.drop_duplicates()
    df = preprocessing(df)
    print("deleting missing DOI in crossref")
    print()
    compute_metrics(df, 0)
    print("Cerco soglia...")
    threshold = find_best_threshold(df)
    compute_metrics(df, threshold)

if __name__ == '__main__':
    print("Start at: ", datetime.datetime.now())
    main()
    print("End at: ", datetime.datetime.now())

