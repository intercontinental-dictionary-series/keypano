"""
    Report on pairwise alignments with Spanish and Portugues languages.

    Johann-Mattis List, Aug 22, 2021
"""
import csv
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
    bb = {doc: {} for doc in wl.cols
          if not any((lambda x, y: x in y)(donor, doc) for donor in donors)}

    for concept in progressbar(wl.rows, desc="pairwise SCA"):
        idxs = wl.get_dict(row=concept)
        donors_concepts = {donor: idxs.get(donor, []) for donor in donors}
        for doc in idxs:
            if any((lambda x, y: x in y)(donor, doc) for donor in donors): continue
            # if "Spanish" not in doc and "Portuguese" not in doc:
            bb[doc][concept] = {idx: [] for idx in idxs[doc]}
            for donor in donors:
                for idxA, idxB in product(donors_concepts[donor], idxs[doc]):
                    wordA, wordB = wl[idxA, "tokens"], wl[idxB, "tokens"]
                    pair = Pairwise(wordA, wordB)
                    pair.align(distance=True, mode=mode)
                    d = pair.alignments[0][2]
                    bb[doc][concept][idxB] += [(donor, d)]

    return bb


def report_borrowing(wl, bb, thresholds, donors, donor_file_out):
    rdr = keypano().cldf_reader()
    families = {language["ID"]: language["Family"] for language in rdr['LanguageTable']}
    # print('***', wl.header)
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
                concept_tokens = wl.get_dict(row=concept, entry='tokens')
                tmp_prop = {donor: 0 for donor in donors}
                for idx, hits in idxs.items():
                    for donor_lang, dist in hits:
                        donor_tokens = concept_tokens[donor_lang]
                        if dist <= threshold:
                            tmp_prop[donor_lang] += 1
                            if donor_file_out:
                                # Report words which hit - both donor and receiver languages.
                                word = wl[idx, 'tokens']
                                words += [[language_, concept_, word, donor_lang,
                                           donor_tokens[0],
                                           donor_tokens[1] if len(donor_tokens) > 1 else '',
                                           donor_tokens[2] if len(donor_tokens) > 2 else '']]
                                language_ = ''
                                concept_ = ''

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

        if donor_file_out:
            headers = ["Language", "Concept", "Word", "Donor",
                       "Donor words (0)", "Donor words (1)", "Donor words (2)"]
            words_table = tabulate(words, headers=headers, tablefmt="simple")
            with open(donor_file_out+'.txt', "w") as f:
                print(words_table, file=f)

        print(f"\nPairwise alignment with threshold {threshold:0.2f}.")
        headers = ["Language", "Family", "Concepts"] + [
            donor for donor in donors] + [
            donor+'P' for donor in donors]

        print(tabulate(
            sorted(props, key=lambda x: (x[1], x[0])),
            headers=headers, tablefmt="pip", floatfmt=".2f"))


def register(parser):
    parser.add_argument(
        "--threshold",
        nargs="*",
        type=float,
        default=[0.45],
        help='Threshold(s) to use with pairwise alignment method.',
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
        "--donor_file_out",
        type=str,
        default="output/pano_donor_words",
    )


def run(args):
    wl = compose_wl()
    bb = construct_alignments(wl, mode=args.mode, donors=args.donor)
    report_borrowing(wl, bb, thresholds=args.threshold,
                     donors=args.donor, donor_file_out=args.donor_file_out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    register(parser)
    run(parser.parse_args())
