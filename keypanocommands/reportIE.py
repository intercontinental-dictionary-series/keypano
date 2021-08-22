"""
    Report on pairwise alignments with Spanish and Portugues languages.

    Johann-Mattis List, Aug 22, 2021
"""
import argparse
from csvw.dsv import UnicodeDictReader
from lingpy import *
from lexibank_keypano import Dataset as keypano
# from collections import defaultdict
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


def construct_alignments(wl):
    # Construct borrowing-bookkeeping structure
    bb = {doc: {} for doc in wl.cols
          if 'Spanish' not in doc and 'Portuguese' not in doc}
    for concept in progressbar(wl.rows, desc="pairwise SCA"):
        idxs = wl.get_dict(row=concept)
        spanish = idxs.get("Spanish", [])
        portuguese = idxs.get("Portuguese", [])
        for doc in idxs:
            if "Spanish" not in doc and "Portuguese" not in doc:
                bb[doc][concept] = {idx: [] for idx in idxs[doc]}
                for idxA, idxB in product(spanish, idxs[doc]):
                    wordA, wordB = wl[idxA, "tokens"], wl[idxB, "tokens"]
                    pair = Pairwise(wordA, wordB)
                    pair.align(distance=True)
                    d = pair.alignments[0][2]
                    bb[doc][concept][idxB] += [("Spanish", d)]
                for idxA, idxB in product(portuguese, idxs[doc]):
                    wordA, wordB = wl[idxA, "tokens"], wl[idxB, "tokens"]
                    pair = Pairwise(wordA, wordB)
                    pair.align(distance=True)
                    d = pair.alignments[0][2]
                    bb[doc][concept][idxB] += [("Portuguese", d)]
    return bb


def report_borrowing(bb, thresholds):
    # threshold = 0.45

    for threshold in thresholds:
        props = []
        families = []
        # Access to languages direct from keypano() pulls from etc_dir.
        # Should be better way to get directly from cldf_dir/languages!
        with UnicodeDictReader(keypano().cldf_dir / "languages.csv") as rdr:
            for row in rdr:
                families.append(row)
        families = {
            language["ID"]: language["Family"] for language in families}
        for language, concepts in bb.items():
            # determine proportion of borrowed words
            prop = {"Spanish": [], "Portuguese": [], "None": []}
            concept_count = 0
            for concept, idxs in concepts.items():
                tmp_prop = {"Spanish": 0, "Portuguese": 0}
                for idx, hits in idxs.items():
                    for lng, d in hits:
                        if d <= threshold:
                            tmp_prop[lng] += 1
                if idxs:
                    for lng, score in tmp_prop.items():
                        prop[lng] += [score/len(idxs)]
                    concept_count += 1
            props += [[
                language,
                families[language],
                concept_count,
                sum(prop["Spanish"]),
                sum(prop["Portuguese"]),
                    sum(prop["Spanish"])/concept_count,
                    sum(prop["Portuguese"])/concept_count,
                    ]]
        print(f"\nPairwise alignment with threshold {threshold:0.2f}.")
        print(tabulate(
            sorted(props, key=lambda x: (x[1], x[0])),
            headers=["Language", "Family", "Concepts", "Spanish", "Portuguese",
                     "SpanishP", "PortugueseP", ], tablefmt="pip", floatfmt=".2f"))


def register(parser):
    parser.add_argument(
        "--thresholds",
        nargs="*",
        type=float,
        default=[0.45],
        help='Thresholds to use with pairwise alignment method.',
    )


def run(args):
    wl = compose_wl()
    bb = construct_alignments(wl)
    report_borrowing(bb, thresholds=args.thresholds)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    register(parser)
    run(parser.parse_args())
