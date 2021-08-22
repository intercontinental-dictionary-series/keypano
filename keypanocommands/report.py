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
    local_, global_, global_gt1_ = get_cogids_for(table, index)
    local_ = list(local_.values)
    global_ = list(global_.values)
    global_gt1_ = list(global_gt1_.values)
    cogids_table = list(zip(family_, local_, global_, global_gt1_))
    return cogids_table


def get_cogids_by_family(table):
    # Table is intermediate result from get_cogids_table_for
    language_family_set = sorted(set([row[0] for row in table]))
    lf_global_cognates_gt1 = {}

    # global_gt1 in [3] of table.
    for lf in language_family_set:
        lf_global_cognates = set([row[3] for row in table if row[0] == lf and row[3] != 0])
        # Construct dictionary of counters for each language family.
        cognates_gt1_ = {lf_: Counter() for lf_ in language_family_set}
        for row in table:
            if row[3] in lf_global_cognates:
                cognates_gt1_[row[0]][row[3]] += 1

        # Condense detail down to numbers of distinct cognates and words.
        cognates_gt1_stats = {lf_: [len(counter), sum(counter.values())] for lf_, counter in cognates_gt1_.items()}

        lf_global_cognates_gt1[lf] = cognates_gt1_stats

    return lf_global_cognates_gt1


def report_cogids_table(lf_global_cognates, selector=0):
    # Display as table.
    # Selector 0 : cognates, 1: words
    lf_cognates_table = []
    language_families = [lf for lf in lf_global_cognates.keys()]

    for lf, lf_cognates in lf_global_cognates.items():
        lf_cognates_table.append([lf] + [lf_cognates[lf_][selector] for lf_ in language_families])

    header0 = 'Language ' + ('Cognates' if not selector else 'Words')
    print(tabulate(lf_cognates_table, headers=[header0] + language_families))


def report_cogids_by_family(table, index=0, selector=0):
    cogids = get_cogids_table_for(table, index=index)
    cogids_by_family = get_cogids_by_family(cogids)
    report_cogids_table(cogids_by_family, selector=selector)


def register(parser):
    parser.add_argument(
        "--dataset",
        type=str,
        default='output/pano_analysis.tsv',
        help="File path for flat file lexstat wordlist in .tsv format.",
    )
    parser.add_argument(
        "--index",
        type=int,
        default=0,
        help='Index of threshold used in cognate analysis',
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
    report_cogids_by_family(table, index=args.index, selector=args.selector)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    register(parser)
    run(parser.parse_args())
