"""
    Report on pairwise alignments with Spanish and Portugues languages.

    Johann-Mattis List, Aug 22, 2021
"""
# import csv
import argparse
from lingpy import *
from lexibank_keypano import Dataset as keypano
from itertools import product
from tabulate import tabulate
from pylexibank import progressbar


def compose_wl():
    wl = Wordlist.from_cldf(
        keypano().cldf_dir / "cldf-metadata.json",
        columns=["language_id",
                 "language_family",
                 "concept_name",
                 "concept_concepticon_id",
                 "value",
                 "form",
                 "segments"])
    return wl


def construct_alignments(wl, mode, donors):
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
                    pair.align(distance=True, mode=mode)
                    dist = pair.alignments[0][2]
                    # Save donor word reference to store.
                    bb[doculect][concept][idxB] += [(donor, dist, wordA)]

    return bb


def screen_word_hits(tmp_words, delta_threshold):
    # Organize according to requirements of discrimination between donors.
    # Get index of min distance word.
    min_idx = min(enumerate(tmp_words), key=lambda x: x[1][1])[0]
    min_dist = tmp_words[min_idx][1]
    tmp_words_ = []
    for idx, row in enumerate(tmp_words):
        if idx == min_idx:
            tmp_words_ += [row + ['*']]
        elif row[1] <= min_dist+delta_threshold:
            tmp_words_ += [row + ['-']]
        else:
            tmp_words_ += [row + ['']]
    return tmp_words_


def report_borrowing(wl, bb,
                     thresholds, delta_threshold,
                     donors, donor_words_out,
                     donor_words_policy, combine_policy):

    rdr = keypano().cldf_reader()
    families = {language["ID"]: language["Family"] for language in rdr['LanguageTable']}
    for threshold in thresholds:
        props = []
        words = []
        for language, concepts in bb.items():
            language_ = language
            # determine proportion of borrowed words
            prop = {donor: [] for donor in donors}
            concept_count = 0
            for concept, idxs in concepts.items():
                concept_ = concept
                tmp_prop = {donor: 0 for donor in donors}
                for idx, hits in idxs.items():
                    word = wl[idx, 'tokens']
                    word_ = word
                    tmp_words = []
                    for donor_lang, dist, donor_word in hits:
                        if dist <= threshold:
                            tmp_words += [[donor_lang, dist, donor_word]]

                    if not tmp_words: continue
                    tmp_words = screen_word_hits(tmp_words, delta_threshold)
                    for row in tmp_words:
                        # Skip words not near minimum distance.
                        if donor_words_policy == "exclude" and not row[3]: continue
                        tmp_prop[row[0]] += 1
                        words.append([language_, concept_, word_,
                                      row[0], f'{row[1]:0.2f}', row[2], row[3]])
                        language_ = ''
                        concept_ = ''
                        word_ = ''

                if idxs:
                    for donor_lang, score in tmp_prop.items():
                        prop[donor_lang] += [score/len(idxs)]
                    concept_count += 1

            props += [[
                language,
                families[language],
                concept_count] +
                [sum(prop[donor]) for donor in donors] +
                [sum(prop[donor])/concept_count for donor in donors]
            ]

        if donor_words_out:
            headers = ["Language", "Concept", "Word",
                       "Donor", "Distance", "Donor word", "Marker"]
            words_table = tabulate(words, headers=headers, tablefmt="simple")
            with open(donor_words_out + '.txt', "w") as f:
                print(words_table, file=f)

        print(f"\nPairwise alignment with threshold {threshold:0.2f} and "
              f"delta threshold {delta_threshold:0.2f}.")
        headers = ["Language", "Family", "Concepts"] + [
            donor for donor in donors] + [
            donor+'P' for donor in donors]
        if combine_policy:
            # Construct combined columns for summary report.
            headers += ["Combined", "CombinedP"]
            # Upgrade props to include combined.
            props_ = props
            props = []
            for row in props_:
                props += [row + [sum(row[3:3+len(donors)])] + [sum(row[3:3+len(donors)])/row[2]]]

        print(tabulate(
            sorted(props, key=lambda x: (x[1], x[0])),
            headers=headers, tablefmt="pip", floatfmt=".2f"))


def register(parser):
    parser.add_argument(
        "--threshold",
        nargs="*",
        type=float,
        default=[0.4],
        help='Threshold(s) to use with pairwise alignment method.',
    )
    parser.add_argument(
        "--delta_threshold",
        type=float,
        default=0.1,
        help='Threshold to distinguish difference between candidate donors.',
    )

    parser.add_argument(
        "--mode",
        type=str,
        default="global",
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
        "--donor_words_out",
        type=str,
        default="output/donor_words",
        help='Filename for detail list of candidate donor words.'
    )
    parser.add_argument(
        "--donor_words_policy",
        type=str,
        default="exclude",
        choices=["exclude", "retain"],
        help='Whether to exclude or retain candidate words far from minimum.'
    )
    parser.add_argument(
        "--disable_combine",
        dest='combine_policy',
        action='store_false',
        help='Disable combine language statistics.'
    )


def run(args):
    wl = compose_wl()
    bb = construct_alignments(wl, mode=args.mode, donors=args.donor)
    report_borrowing(wl, bb, thresholds=args.threshold,
                     delta_threshold=args.delta_threshold,
                     donors=args.donor,
                     donor_words_out=args.donor_words_out,
                     donor_words_policy=args.donor_words_policy,
                     combine_policy=args.combine_policy)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    register(parser)
    run(parser.parse_args())
