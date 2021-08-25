"""
    Report on cognates identified by Lingpy clustering methods.

    John E. Miller, Aug 21, 2021
"""
from collections import Counter
import argparse
import pandas as pd
from tabulate import tabulate


def get_table(filename=None):
    # Read Lexstat wordlist in flat file .tsv format from specified filename.
    if not filename.endswith('.tsv'):
        filename += '.tsv'
    table = pd.read_csv(filename, sep='\t')
    table.drop(table.index[[-3, -2, -1]], inplace=True)
    print(f"{len(table)} words in {filename}.")
    return table


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
    local_, global_, global_gt1_ = get_cogids_for(table, index)
    local_ = list(local_.values)
    global_ = list(global_.values)
    global_gt1_ = list(global_gt1_.values)
    cogids_table = list(zip(family_, language_, local_, global_, global_gt1_))
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

    lu_unit_set = sorted(set([row[lu_idx] for row in table]))
    lu_global_cognates_gt1 = {}

    # global_gt1 in [4] of table.
    for lu in lu_unit_set:
        cognates_gt1 = set([row[4] for row in table
                            if row[lu_idx] == lu and row[4] != 0])

        # Construct dictionary of counters for each language family.
        cognates_gt1_ = {lu_: Counter() for lu_ in lu_unit_set}
        for row in table:
            if row[4] in cognates_gt1:
                cognates_gt1_[row[lu_idx]][row[4]] += 1

        # Condense detail down to numbers of distinct cognates and words.
        lu_global_cognates_gt1[lu] = {lu_: [len(counter), sum(counter.values())]
                                      for lu_, counter in cognates_gt1_.items()}

    return lu_global_cognates_gt1


def report_cogids_table(global_cognates, selector=0):
    # Display as table.
    # Selector 0 : cognates, 1: words
    # lu == language unit -- language, language_family
    cognates_table = []
    lu_keys = [key for key in global_cognates.keys()]

    for lu, lu_cognates in global_cognates.items():
        cognates_table.append([lu] + [lu_cognates[lu_][selector] for lu_ in lu_keys])

    header0 = 'Language ' + ('Cognates' if not selector else 'Words')
    print(tabulate(cognates_table, headers=[header0] + lu_keys))


def report_cogids_by_family(table, family=None, index=0, selector=0):
    cogids_table = get_cogids_table_for(table, index=index)
    lu_cogids_gt1 = get_cogids_by_family(cogids_table, family=family)
    report_cogids_table(lu_cogids_gt1, selector=selector)


def register(parser):
    parser.add_argument(
        "--dataset",
        type=str,
        default='output/pano_analysis.tsv',
        help="File path for flat file lexstat wordlist in .tsv format.",
    )
    parser.add_argument(
        "--family",
        type=str,
        default=None,
        help="Family name to report or None if report over all families."
    )
    parser.add_argument(
        "--index",
        type=int,
        default=0,
        help='Index of threshold used for report.',
    )
    parser.add_argument(
        "--selector",
        type=int,
        default=0,
        choices=[0, 1],
        help='Whether reporting for cognates=0 or words=1.',
    )


def run(args):
    table = get_table(args.dataset)
    report_basic_for(table, index=args.index)
    report_cogids_by_family(table, family=args.family,
                            index=args.index, selector=args.selector)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    register(parser)
    run(parser.parse_args())
