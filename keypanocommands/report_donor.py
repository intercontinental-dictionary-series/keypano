"""
    Report on pairwise alignments with Spanish and Portuguese languages.

    Johann-Mattis List, Aug 22, 2021
    John Edward Miller, Oct 6, 2021
"""
from pathlib import Path
import argparse
from lingpy import *
from lexibank_keypano import Dataset as keypano
from itertools import product
from tabulate import tabulate
from pylexibank import progressbar
import keypanocommands.util as util
import keypanocommands.report as report


def construct_alignments(wl, model, mode, donors):
    # Construct borrowing-bookkeeping structure
    bb = {doculect: {} for doculect in wl.cols
          if not any((lambda x, y: x in y)(donor, doculect) for donor in donors)}

    for concept in progressbar(wl.rows, desc="pairwise SCA"):
        idxs = wl.get_dict(row=concept)
        donors_concepts = {donor: idxs.get(donor, []) for donor in donors}
        for doculect in idxs:
            if any((lambda x, y: x in y)(donor, doculect) for donor in donors): continue
            # if "Spanish" not in doc and "Portuguese" not in doc:
            bb[doculect][concept] = {idx: [] for idx in idxs[doculect]}
            for donor in donors:
                # All combinations of donor and doculect entries for this concept.
                for idxA, idxB in product(donors_concepts[donor], idxs[doculect]):
                    # Combination of donor and doculect entries.
                    wordA, wordB = wl[idxA, "tokens"], wl[idxB, "tokens"]
                    pair = Pairwise(wordA, wordB)
                    pair.align(distance=True, model=model, mode=mode)
                    dist = pair.alignments[0][2]
                    # Save donor word reference to store.  Save loanword status to store.
                    bb[doculect][concept][idxB] += [(donor, dist, wordA)]

    return bb


def screen_word_hits(tmp_words, threshold):
    # Organize according to requirements of discrimination between donors.
    # Get index of min distance word.
    min_idx = min(enumerate(tmp_words), key=lambda x: x[1][1])[0]
    min_dist = tmp_words[min_idx][1]
    min_idx = min_idx if min_dist < threshold else None
    tmp_words_ = []
    for idx, row in enumerate(tmp_words):
        if min_idx is None:
            tmp_words_ += [row + ['']]
        elif idx == min_idx:
            tmp_words_ += [row + ['*']]
        elif row[1] <= threshold:
            tmp_words_ += [row + ['-']]
        else:
            tmp_words_ += [row + ['']]
    return tmp_words_


def order_words_table(table, status=util.PredStatus.NTN):
    # Remove redundant use of family, language, concept, and word.
    # Sort table by family.  Stable sort so rest of order should be OK.
    # Change unchanged fields to blank after sort for better presentation.
    table = sorted(table, key=lambda table_row: table_row[0])
    ordered_words = []
    family = ''
    language = ''
    concept = ''
    word = ''
    for row in table:
        status_ = row[-1]
        if not util.report_assessment(status, status_): continue

        family_ = row[0] if family != row[0] else ''
        family = row[0]
        language_ = row[1] if language != row[1] else ''
        language = row[1]
        concept_ = row[2] if concept != row[2] else ''
        concept = row[2]
        word_ = row[3] if word != row[3] else ''
        word = row[3]
        borrowed_ = 'True' if row[4] and word_ else 'False' if not row[4] and word_ else ''
        ordered_words.append([family_, language_, concept_, word_, borrowed_] + row[5:-1] + [status_.name])

    return ordered_words


def report_pairwise_distance(words_table, threshold, output, series, first_time=True):
    # Report out.
    headers = ["Family", "Language", "Concept", "Word", "Borrowed",
               "Donor", "Distance", "Donor word", "Marker", "Status"]
    words_table = tabulate(words_table, headers=headers, tablefmt="simple")
    filename = f"{series}{'-' if series else ''}distance-{threshold:0.3f}.txt"
    filepath = Path(output).joinpath(filename).as_posix()
    with open(filepath, 'w' if first_time else 'a') as f:
        print(f"Threshold: {threshold:0.3f}.", file=f)
        print(words_table, file=f)
        print(file=f)


def report_donor_proportions(proportions, threshold, donors):

    print(f"\nPairwise alignment with threshold {threshold:0.3f}.")
    headers = ["Family", "Language", "Concepts"] + [
        donor for donor in donors] + ['Combined'] + [
                  donor + 'P' for donor in donors] + ['CombinedP']

    # Calculate total borrowed.
    concepts_count = 0
    combined_count = 0
    donor_counts = [0]*len(donors)
    for row in proportions:
        concepts_count += row[2]
        for d in range(len(donors)):
            donor_counts[d] += row[3+d]
        combined_count += row[len(donors)+3]
    donor_proportions = [count/concepts_count for count in donor_counts]
    combined_proportion = combined_count/concepts_count
    total_row = (['Total', '', concepts_count] +
                 donor_counts + [combined_count] +
                 donor_proportions + [combined_proportion])

    proportions = sorted(proportions, key=lambda x: (x[0], x[1]))
    proportions.append(total_row)

    print(tabulate(proportions, headers=headers, tablefmt="pip", floatfmt=".2f"))


def report_pairwise_detection(all_words, threshold):
    # print(all_words[:10])
    languages = sorted(set(row[1] for row in all_words))
    families = sorted(set(row[0] for row in all_words))
    # Report detection metrics by language
    # language, family, concept, word, pred, loan in all_words:
    pred = [1 if row[4] else 0 for row in all_words]
    loan = [1 if row[5] else 0 for row in all_words]
    q = util.prf(pred, loan)

    def calculate_metrics_table(table, lu_units, lu_idx):
        metrics_ = []
        for lu in lu_units:
            pred_ = [1 if row[4] else 0 for row in table if row[lu_idx] == lu]
            loan_ = [1 if row[5] else 0 for row in table if row[lu_idx] == lu]
            metrics_.append([lu] + util.prf(pred_, loan_))
        return metrics_

    metrics = calculate_metrics_table(all_words, lu_units=languages, lu_idx=1)
    metrics.append(['Total'] + q)
    report.report_metrics_table(metrics, family=True, threshold=threshold)

    metrics = calculate_metrics_table(all_words, lu_units=families, lu_idx=0)
    metrics.append(['Total'] + q)
    report.report_metrics_table(metrics, family=False, threshold=threshold)


def get_words_results(table, status=util.PredStatus.F):
    words = []
    family = ''
    language = ''
    concept = ''
    table_ = sorted(table, key=lambda table_row: table_row[2])
    table_ = sorted(table_, key=lambda table_row: table_row[1])
    table_ = sorted(table_, key=lambda table_row: table_row[0])
    for row in table_:
        # pred == True if global_gt1
        pred = int(row[4])
        loan = int(row[5])
        status_ = util.assess_pred(pred, loan)
        if util.report_assessment(status, status_):
            family_ = row[0] if family != row[0] else ''
            family = row[0]
            language_ = row[1] if language != row[1] else ''
            language = row[1]
            concept_ = row[2] if concept != row[2] else ''
            concept = row[2]
            words.append([family_, language_, concept_, status_.name, row[3], ])
            # family, language, concept, prediction_result, tokens,
    return words


def report_borrowing(wl, bb,
                     thresholds,
                     report_limit,
                     report_status,
                     donors,
                     policy,
                     output='output',
                     series=''):

    rdr = keypano().cldf_reader()
    families = {language["ID"]: language["Family"] for language in rdr['LanguageTable']}
    first_time = True
    for threshold in thresholds:
        proportions = []
        words = []  # Used for subsequent reporting of distances below threshold.
        all_words = []  # Used for subsequent calculation of detection metrics.
        for language, concepts in bb.items():
            family = families[language]
            # determine proportion of borrowed words
            prop = {donor: [] for donor in donors}
            # include combined donors category.
            prop['Combined'] = []
            concept_count = 0
            # idx is index of word in target language
            for concept, idxs in concepts.items():
                tmp_prop = {donor: 0 for donor in donors}
                for idx, hits in idxs.items():
                    word = wl[idx, 'tokens']
                    loan = wl[idx, 'loan']
                    pred = False
                    tmp_words = []
                    for donor, dist, donor_word in hits:
                        if dist <= threshold or (report_limit and dist < report_limit):
                            tmp_words += [[donor, dist, donor_word]]
                        if dist <= threshold:  # Only need 1 donor word < threshold.
                            pred = True

                    # Add word to all_words for words status report.
                    # Words are target language words, not possible donor words.
                    all_words.append([families[language], language,
                                      concept, word, pred, loan])

                    if not tmp_words: continue  # Nothing to add to distance report
                    # Add marker of minimum '*' or near minimum '-' < threshold.
                    tmp_words = screen_word_hits(tmp_words, threshold)
                    for row in tmp_words:
                        # Count hits for distance < threshold, or
                        # only words close to minimum distance < threshold.
                        if (policy == "retain" and row[1] < threshold or
                                policy == "exclude" and row[3]):
                            tmp_prop[row[0]] += 1
                        # Report marked words (words not near minimum distance), or
                        # unmarked words < threshold, or words < report_limit.
                        if (policy == "retain" and row[1] < threshold or
                                policy == "exclude" and row[3] or
                                report_limit and row[1] < report_limit):
                            pred_ = 1 if row[3] in ['*', '-'] else 0
                            status_ = util.assess_pred(pred_, int(loan))
                            words.append([family, language, concept, word, loan,
                                          row[0], f'{row[1]:0.2f}', row[2], row[3],
                                          status_])

                if idxs:
                    # Get max score for use with combined donors category.
                    max_score = 0
                    for donor, score in tmp_prop.items():
                        max_score = max(max_score, score)
                        prop[donor] += [score/len(idxs)]
                    # Add in score for Combined category.
                    prop['Combined'] += [max_score/len(idxs)]
                    concept_count += 1

            proportions += [[
                families[language],
                language,
                concept_count] +
                [sum(prop[donor]) for donor in donors] +
                [sum(prop['Combined'])] +
                [sum(prop[donor])/concept_count for donor in donors] +
                [sum(prop['Combined'])/concept_count]
            ]

        if series:
            word_distances = order_words_table(table=words, status=report_status)
            report_pairwise_distance(words_table=word_distances,
                                     threshold=threshold,
                                     output=output, series=series,
                                     first_time=first_time)

            word_assessments = get_words_results(table=all_words, status=report_status)
            report.report_words_table(word_assessments,
                                      threshold=threshold,
                                      output=output, series=series,
                                      first_time=first_time)

        report_donor_proportions(proportions, threshold, donors)
        first_time = False

        report_pairwise_detection(all_words, threshold)


def register(parser):
    parser.add_argument(
        "--model",
        type=str,
        choices=["sca", "asjp"],
        default="sca",
        help='Sound class model to transform tokens.'
    )
    parser.add_argument(
        "--threshold",
        nargs="*",
        type=float,
        default=[0.4],
        help='Threshold(s) to use with pairwise alignment method.',
    )
    parser.add_argument(
        "--limit",
        type=float,
        default=None,
        help="Limit to use for reporting words and donor candidate distances."
    )
    parser.add_argument(
        "--status",
        type=str,
        default='ntn',
        choices=[e.name.lower() for e in util.PredStatus],
        help="Status mask to use for reporting borrowed word detection status."
    )

    parser.add_argument(
        "--mode",
        type=str,
        default="overlap",
        choices=["global", "local", "overlap", "dialign"],
        help='Alignment mode.',
    )
    parser.add_argument(
        "--donor",
        nargs="*",
        type=str,
        default=["Spanish", "Portuguese"],
        help='Donor language(s).',
    )
    parser.add_argument(
        "--policy",
        type=str,
        default="exclude",
        choices=["exclude", "retain"],
        help='Whether to exclude or retain candidate words far from minimum.'
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
        default="pairwise-donor-words",
        help='Filename prefix for candidate donor words.'
    )


def run(args):
    wl = util.compose_wl()
    bb = construct_alignments(wl,
                              model=args.model,
                              mode=args.mode,
                              donors=args.donor)
    report_borrowing(wl, bb,
                     thresholds=args.threshold,
                     report_limit=args.limit,
                     report_status=util.PredStatus[args.status.upper()],
                     donors=args.donor,
                     policy=args.policy,
                     output=args.output,
                     series=args.series)


if __name__ == "__main__":
    parser_ = argparse.ArgumentParser()
    register(parser_)
    run(parser_.parse_args())
