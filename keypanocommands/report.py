"""
    Report on cognates identified by Lingpy clustering methods.

    John E. Miller, Aug 21, 2021
"""
from collections import Counter, defaultdict
from pathlib import Path
import argparse
import pandas as pd
from tabulate import tabulate

import keypanocommands.util as util


def get_table(store='store', infile=None):
    # Read Lexstat wordlist in flat file .tsv format from specified store and infile.
    if not infile.endswith('.tsv'):
        infile += '.tsv'
    filepath = Path(store).joinpath(infile).as_posix()
    table = pd.read_csv(filepath, sep='\t')
    parameters = table.iloc[-3:]['ID'].values
    print("Analysis file details:")
    print(parameters[0])
    print(parameters[1])
    print(parameters[2])
    print()
    table.drop(table.index[[-3, -2, -1]], inplace=True)
    print(f"{len(table)} words in {filepath}.")
    return table, parameters


def get_cogids_for(table, index=0):
    # Get local, local>1, global, global>1 for series index.
    local_label = f"SCA_{index}ID"
    global_family_label = f"SCA_{index}"
    global_gt1_label = f"SCALLID_{index}"
    local_series = table[local_label].astype('int')
    global_gt1_series = table[global_gt1_label].astype('int')
    global_family_series = table[global_family_label]
    global_series = global_family_series.str.extract(r'(\d+)\-')[0].astype('int')
    return local_series, global_series, global_gt1_series


def report_basic(local_, global_, global_gt1_):
    counts_local_cognates = local_.value_counts()
    print(f"Number of words: {sum(counts_local_cognates)}, " +
          f"number of distinct local cognates: {len(counts_local_cognates)}")
    counts_local_cognates_gt1 = counts_local_cognates[counts_local_cognates.values > 1]
    print(f"Number of words for >1 local cognates: {sum(counts_local_cognates_gt1)}, " +
          f"number of distinct >1 local cognates: {len(counts_local_cognates_gt1)}")

    counts_global_cognates = global_.value_counts()
    print(f"Number of words: {sum(counts_global_cognates)}, " +
          f"number distinct global cognates: {len(counts_global_cognates)}")
    counts_global_cognates_gt1 = global_gt1_.value_counts()
    # Drop the 0 cognate as it is not a family global cognate.
    counts_global_cognates_gt1 = counts_global_cognates_gt1[counts_global_cognates_gt1.index != 0]
    print(f"Number of words for >1 family global cognates: {sum(counts_global_cognates_gt1)}, " +
          f"number of distinct >1 family global cognates: {len(counts_global_cognates_gt1)}")


def report_basic_for(table, index=0):
    local_, global_, global_gt1_ = get_cogids_for(table, index)
    report_basic(local_, global_, global_gt1_)


def get_cogids_table_for(table, index=0):
    family_ = list(table.LANGUAGE_FAMILY.values)
    language_ = list(table.DOCULECT.values)
    concepts_ = list(table.CONCEPT.values)
    tokens_ = list(table.TOKENS.values)
    local_, global_, global_gt1_ = get_cogids_for(table, index)
    local_ = list(local_.values)
    global_ = list(global_.values)
    global_gt1_ = list(global_gt1_.values)
    loan_ = [int(value) for value in table.LOAN.values]
    cogids_table = list(zip(family_, language_,
                            local_, global_, global_gt1_,
                            loan_, tokens_, concepts_))
    return cogids_table


def get_cogids_by_family(table, family=None):
    # Table is intermediate result from get_cogids_table_for
    # lu refers to language unit - language or family.
    if family:
        # Family is given, so
        # Filter on family, and construct language unit set on languages.
        table = [row for row in table if row[0] == family]
        lu_idx = 1
    else:
        lu_idx = 0

    lu_unit_set = sorted(set(row[lu_idx] for row in table))
    lu_global_cognates_gt1 = {}

    # global_gt1 in [4] of table.
    for lu in lu_unit_set:
        cognates_gt1 = set(row[4] for row in table
                           if row[lu_idx] == lu and row[4] != 0)

        # Construct dictionary of counters for each language family.
        cognates_gt1_ = {lu_: Counter() for lu_ in lu_unit_set}
        for row in table:
            if row[4] in cognates_gt1:
                cognates_gt1_[row[lu_idx]][row[4]] += 1

        # Condense detail down to numbers of distinct cognates and words.
        lu_global_cognates_gt1[lu] = {lu_: [len(counter), sum(counter.values())]
                                      for lu_, counter in cognates_gt1_.items()}

    return lu_global_cognates_gt1


def report_cogids_table(global_cognates, selector=0, threshold=None):
    # Display as table.
    # Selector 0 : cognates, 1: words
    # lu == language unit -- language, language_family
    cognates_table = []
    lu_keys = [key for key in global_cognates.keys()]

    for lu, lu_cognates in global_cognates.items():
        cognates_table.append([lu] + [lu_cognates[lu_][selector] for lu_ in lu_keys])

    unit = 'Cognates' if not selector else 'Words'
    print(f"Report number of {unit} for cross-family concepts at threshold: {threshold:0.3f}.")
    header0 = 'Language ' + unit
    print(tabulate(cognates_table, headers=[header0] + lu_keys))


def report_cogids_by_family(cogids_table, family=None, threshold=None):
    lu_cogids_gt1 = get_cogids_by_family(cogids_table, family=family)
    report_cogids_table(lu_cogids_gt1, selector=0, threshold=threshold)
    report_cogids_table(lu_cogids_gt1, selector=1, threshold=threshold)


def get_language_unit_table(table, family=None, exclude=None):
    # Works with languages from single family or over families.
    # Exclude family not included in calculation.
    # Exclude family should be that which is intruder or source of most borrowings.
    table = [row for row in table if row[0] != exclude]

    # lu refers to language unit - language or family.
    if family:  # Select on family.
        # Filter on family, and construct language unit set on languages.
        table = [row for row in table if row[0] == family]
        lu_idx = 1  # Use language name
    else:
        lu_idx = 0  # Use language family name

    lu_units = sorted(set([row[lu_idx] for row in table]))
    return table, lu_units, lu_idx


def get_words_results(table, donor_forms, require_cogid=False, status=util.PredStatus.F):
    # Report by language unit iterating on lu_unit_set.
    words = []
    family = ''
    language = ''
    concept = ''
    table_ = sorted(table, key=lambda table_row: table_row[7])
    table_ = sorted(table_, key=lambda table_row: table_row[1])
    table_ = sorted(table_, key=lambda table_row: table_row[0])

    cnt = 0  # Testing.
    for row in table_:
        cnt += 1
        # if cnt > 2000: break
        cogid_ = row[4]

        if require_cogid and cogid_ == 0: continue

        pred = 0 if cogid_ == 0 else 1
        loan = row[5]
        status_ = util.assess_pred(pred, loan)

        if not util.report_assessment(status, status_): continue
        if family != row[0]: words.append([])
        family_ = row[0] if family != row[0] else ''
        family = row[0]

        if language != row[1]: words.append([])
        language_ = row[1] if language != row[1] else ''
        language = row[1]

        concept_ = row[7] if concept != row[7] else ''
        concept = row[7]

        borrowed_ = True if loan else False
        tokens_ = row[6]
        status_name = status_.name
        # Add in donor forms
        if cogid_ != 0:
            donors = donor_forms[cogid_]
            if len(donors.items()) == 0:
                words.append([family_, language_, concept_, tokens_,
                              cogid_, borrowed_, status_name, 'Unknown', 'Unknown'])
            else:
                for key, value in donors.items():
                    words.append([family_, language_, concept_, tokens_,
                                  cogid_, borrowed_,  status_name,
                                  key, value])
                    family_ = ''
                    language_ = ''
                    concept_ = ''
                    cogid_ = ''
                    borrowed_ = ''
                    tokens_ = ''
                    status_name = ''

        else:
            words.append([family_, language_, concept_, tokens_,
                          cogid_, borrowed_,  status_name])
        # family, language, concept, tokens, loan, status

    return words


def report_words_table(words, threshold=None,
                       output=None, series='', first_time=True):

    filename = f"cluster-{threshold:0.2f}-{series}{'-' if series else ''}words-status"
    file_path = Path(output).joinpath(filename).as_posix()
    header = ['Family', 'Language', 'Concept',  'Tokens', 'Cog_id',
              'Borrowed', 'Status', 'Donor Language', 'Donor Tokens']
    words_table = tabulate(words, headers=header, tablefmt="pip")
    with open(file_path + '.txt', 'w' if first_time else 'a') as f:
        print(f"Threshold: {threshold:0.3f}.", file=f)
        print(words_table, file=f)


def get_metrics_by_language_unit(table, lu_units, lu_idx):
    # Consider all together.
    pred = [0 if row[4] == 0 else 1 for row in table]
    loan = [1 if row[5] else 0 for row in table]
    qa = util.prf(pred, loan)

    # Report by language unit iterating on lu_unit_set.
    # Wasteful since not taking advantage of sorted table, but it works.
    metrics = []
    for lu in lu_units:
        pred = [0 if row[4] == 0 else 1 for row in table if row[lu_idx] == lu]
        loan = [1 if row[5] else 0 for row in table if row[lu_idx] == lu]
        q = util.prf(pred, loan)
        metrics.append([lu] + q)
    metrics.append(['Total'] + qa)
    return metrics


def build_donor_forms_dict(cogids_table, donor_family):
    # From cogids_table:
    #     family_, language_, local_, global_, global_gt1_,
    #     loan_, tokens_, concepts_
    # Use: family_, language_, global_gt1_, tokens_
    # Row: 0,       1,         4,           6

    donor_stuff = defaultdict(lambda: defaultdict(list))
    for row in cogids_table:
        if row[0] == donor_family and row[4] > 0:
            donor_stuff[row[4]][row[1]].append(row[6])
    return donor_stuff


def report_metrics_table(metrics, family=None, threshold=None):
    print()
    print(f"Threshold: {threshold:0.3f}.")
    header0 = 'Language ' + ('' if family else 'Family')
    print(tabulate(metrics,
          headers=[header0, 'tp', 'tn', 'fp', 'fn',
                   'precision', 'recall', 'F1 score', 'accuracy'],
                   tablefmt="pip", floatfmt=".3f"))
    total = metrics[-1]
    print(f"Total: borrowed {total[1]+total[4]}, "
          f"inherited {total[2]+total[3]}, "
          f"total {total[1] + total[2] + total[3] + total[4]}")


def report_metrics_by_family(cogids_table,
                             family=None,
                             exclude=None,
                             require_cogid=False,
                             report_status=None,
                             threshold=None,
                             output=None,
                             series=''):
    # Construct dictionary of donor forms of possible borrowed words for words report.
    # Use exclude list of languages as donor languages.
    donor_forms = build_donor_forms_dict(cogids_table, donor_family=exclude)

    table, lu_units, lu_idx = get_language_unit_table(
        cogids_table, family=family, exclude=exclude)
    metrics = get_metrics_by_language_unit(table, lu_units=lu_units, lu_idx=lu_idx)
    report_metrics_table(metrics, family=family, threshold=threshold)

    words = get_words_results(table, donor_forms=donor_forms,
                              require_cogid=require_cogid, status=report_status)
    report_words_table(words, threshold=threshold, output=output, series=series)


def register(parser):
    parser.add_argument(
        "--store",
        type=str,
        default='store',
        help='Directory from which to load analysis wordlist.',
    )
    parser.add_argument(
        "--infile",
        type=str,
        default="analysis-cluster"
    )
    parser.add_argument(
        "--family",
        type=str,
        default=None,
        help="Family name to report or None if report over all families."
    )
    parser.add_argument(
        "--exclude",
        type=str,
        default=None,
        help="Family name to exclude from calculation of putative recall, precision, F1 score."
    )
    parser.add_argument(
        "--index",
        type=int,
        default=0,
        help='Index of threshold used for report.',
    )
    parser.add_argument(
        "--cogid",
        action="store_true",
        help='Report only concepts and words with cross family cognate id.'
    )
    parser.add_argument(
        "--status",
        type=str,
        default='ntn',
        choices=[s.name.lower() for s in util.PredStatus],
        help='Code for reporting words for status.',
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output",
        help='Directory to write output.'
    )
    parser.add_argument(
        "--series",
        type=str,
        default='',
        help='Filename prefix for borrowed word predictions.'
    )


def run(args):
    table, parameters = get_table(args.store, args.infile)
    report_basic_for(table, index=args.index)
    cogids_table = get_cogids_table_for(table, index=args.index)
    thresholds = util.get_thresholds(parameters[-1])
    report_cogids_by_family(cogids_table,
                            family=args.family,
                            threshold=thresholds[args.index])
    report_metrics_by_family(cogids_table,
                             family=args.family,
                             exclude=args.exclude,
                             require_cogid=args.cogid,
                             report_status=util.PredStatus[args.status.upper()],
                             threshold=thresholds[args.index],
                             output=args.output,
                             series=args.series)


def get_total_run_result(store, infile, family, exclude):
    table, parameters = get_table(store, infile)
    cogids_table = get_cogids_table_for(table, index=0)
    table_, lu_units, lu_idx = get_language_unit_table(
        cogids_table, family=family, exclude=exclude)
    metrics = get_metrics_by_language_unit(table_, lu_units=lu_units, lu_idx=lu_idx)
    q = metrics[-1]
    # print(q)
    return q[1:]


if __name__ == "__main__":
    parser_ = argparse.ArgumentParser()
    register(parser_)
    run(parser_.parse_args())
