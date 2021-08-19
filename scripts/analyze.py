"""
Analysis output -- some variable interpretations:
scalllid_{i} - cognate id for cognates that cross families.
sca_{i} - cognate id and language family for cognates whether or not they cross families.
sca_{i}ID - cognate id within family.

"""

# from pathlib import Path
import argparse

from lingpy import *
from lingpy.compare.util import mutual_coverage_check
from lingpy.compare.sanity import average_coverage

# from lingpy.evaluate.acd import bcubes
# from clldutils.clilib import Table, add_format

# Service functions.


def check_coverage(wl=None):
    print(f"Wordlist has {wl.width} languages, and {wl.height} concepts in {len(wl)} words.")
    for i in range(200, 0, -1):
        if mutual_coverage_check(wl, i):
            print(f"Minimum mutual coverage is at {i} concept pairs.")
            break
    print(f"Average coverage is at {average_coverage(wl):.2f}")


def compose_pano(dataset="pano_data"):
    lex = LexStat.from_cldf("cldf/cldf-metadata.json",
                            columns=("language_id", "concept_name", "value", "form",
                                     "segments", "language_subgroup", "language_family"))
    lex.output('tsv', filename=dataset, ignore='all', prettify=False)

    check_coverage(lex)


def analyze(method='sca', thresholds=[0.6], dataset="pano_data", filename_out="output/pano_analysis"):
    # table = []
    lex = LexStat(dataset+".tsv")
    if method == "lexstat":
        lex.get_scorer(method="lexstat", runs=1000)

    # for i, t in enumerate([0.5, 0.55, 0.6, 0.65, 0.7]):
    for i, t in enumerate(thresholds):
        # args.log.info("loaded data")
        print(f"Processing for threshold {t:.3f}")
        # John: Cluster using specified method and threshold
        # John: Cluster id stored in wordlist as variable scallid_{i}.
        lex.cluster(method=method, threshold=t, ref="scallid_{0}".format(i))
        # John: Add entries for cluster id combined with language family.
        # John: Formatting provided by lambda expression. Not obvious!
        lex.add_entries("sca_{0}".format(i), "scallid_{0},language_family".format(i),
                        lambda x, y: str(x[y[0]]) + "-" + x[y[1]])
        # John: Replace cluster ids with numbers.  I don't understand this.
        lex.renumber("sca_{0}".format(i))
        # John: Get dictionary representations of cluster ids.
        # John: Seems to be dictionary for each row.
        etd = lex.get_etymdict(ref="scallid_{0}".format(i))
        # nulls = {}

        # John: Zero out cluster ids (cognate ids) that do not cross families.
        for cogid, vals in etd.items():
            # John: Construct list of row indices for this cognate id.
            idxs = []
            for v in vals:
                if v:
                    idxs += v
            # John: Form list of language families.
            famis = [lex[idx, 'language_family'] for idx in idxs]
            # John: If set of 1 family then local cognate.
            if len(set(famis)) == 1:
                for idx in idxs:
                    # John: Set cognate id to 0.
                    lex[idx, 'scallid_{0}'.format(i)] = 0

        # p1, r1, f1 = bcubes(lex, "ucogid", "sca_{0}id".format(i), pprint=False)
        # p2, r2, f2 = bcubes(lex, "uborid", "scallid_{0}".format(i), pprint=False)
        # table += [[t, p1, r1, f1, p2, r2, f2]]
    # with Table(args, "Threshold", "P1", "R1", "F1", "P2", "R2", "F2") as tab:
    #     for row in table:
    #         tab.append(row)

    # file_path = Path(output).joinpath(filename).as_posix()
    lex.output('tsv', filename=filename_out, ignore='all', prettify=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "module",
        type=str,
        choices=["compose", "analyze"],
        help="Compose or analyze dataset",
    )
    parser.add_argument(
        "--method",
        type=str,
        choices=["sca", "lexstat"],
        default="lexstat",
        help='Scoring method (default: "lexstat")',
    )
    parser.add_argument(
        "--thresholds",
        nargs="*",
        type=float,
        default=0.6,
        help='Thresholds to use for cluster method.',
    )

    parser.add_argument(
        "--dataset",
        type=str,
        default="pano_data",
    )

    parser.add_argument(
        "--file_out",
        type=str,
        default="output/pano_analysis",
    )

    args = parser.parse_args()

    if args.module == "compose":
        compose_pano(dataset=args.dataset)
    elif args.module == "analyze":
        analyze(method=args.method, thresholds=args.thresholds,
                dataset=args.dataset, filename_out=args.file_out)
