"""
    Prototype ways to do cognate matching for key_pano project.

    John E. Miller, Sep 6, 2021
"""

import argparse
# from lingpy import *
from lingpy.compare.partial import Partial
# from lingpy.evaluate.acd import bcubes
# from clldutils.clilib import Table, add_format
import keypanocommands.util as util


def analyze_partial(method='lexstat',
                    thresholds=None,
                    runs=2000,
                    mode='overlap',
                    cluster_method='infomap',
                    idtype='loose',
                    file_out="output/pano_analysis_partial"):
    # method: sca, lexstat, edit-dist, turchin
    # mode: global, local, overlap, dialign
    # cluster_method:

    # table = []
    dataset = util.compose_wl()
    part = Partial(dataset, check=True)
    if method == "lexstat":
        # part.get_scorer(runs=10000, ratio=(3, 2), smooth=2)
        # get_partial_scorer
        part.get_scorer(method=method, runs=runs, ratio=(3, 2))

    for i, t in enumerate(thresholds):
        # args.log.info("loaded data")
        print(f"Processing for threshold {t:.3f}")
        # John: Cluster using specified method and threshold
        # John: Cluster id list stored in wordlist as variable scallids_{i}.
        sca_ids = "scallids_{0}".format(i)
        part.partial_cluster(method=method, threshold=t, mode=mode,
                             cluster_method=cluster_method,
                             ref=sca_ids)
        # John: Construct single cognate id from list.
        sca_id = "scallid_{0}".format(i)
        part.add_cognate_ids(sca_ids, sca_id, idtype=idtype)  # or 'strict'

        # John: Could align partial cognates for output.
        # alms = Alignments(part, ref='cogids', fuzzy=True)
        # alms.align()
        # alms.output('tsv', filename=filename + '-aligned', ignore='all', subset=True,
        #             cols=['doculect', 'concept', 'ipa', 'tokens', 'cogid',
        #                   'cogids', 'alignment', 'donor'], prettify=False)

        # John: Add entries for cluster id combined with language family.
        # John: Formatting provided by lambda expression. Not obvious!
        part.add_entries("sca_{0}".format(i), sca_id+",language_family",
                        lambda x, y: str(x[y[0]]) + "-" + x[y[1]])
        # John: Renumber cluster, family ids.  Stored as int in SCA_{i}ID.
        part.renumber("sca_{0}".format(i))
        # John: Get dictionary representations of cluster ids.
        # John: Seems to be dictionary for each row.
        etd = part.get_etymdict(ref=sca_id)
        # nulls = {}

        # John: Zero out cluster ids (cognate ids) that do not cross families.
        for cogid, values in etd.items():
            # John: Construct list of row indices for this cognate id.
            idxs = []
            for v in values:
                if v:
                    idxs += v
            # John: Form list of language families.
            families = [part[idx, 'language_family'] for idx in idxs]
            # John: If set of 1 family then local cognate.
            if len(set(families)) == 1:
                for idx in idxs:
                    # John: Set cognate id to 0.
                    part[idx, sca_id] = 0

        # p1, r1, f1 = bcubes(lex, "ucogid", "sca_{0}id".format(i), pprint=False)
        # p2, r2, f2 = bcubes(lex, "uborid", "scallid_{0}".format(i), pprint=False)
        # table += [[t, p1, r1, f1, p2, r2, f2]]
    # with Table(args, "Threshold", "P1", "R1", "F1", "P2", "R2", "F2") as tab:
    #     for row in table:
    #         tab.append(row)

    # file_path = Path(output).joinpath(filename).as_posix()
    part.output('tsv', filename=file_out, ignore='all', prettify=False)
    part.output('qlc', filename=file_out, ignore=['scorer'], prettify=False)


def register(parser):
    parser.add_argument(
        "--method",
        type=str,
        choices=["sca", "lexstat", "edit-dist", "turchin"],
        default="lexstat",
        help='Scoring method (default: "lexstat").',
    )
    parser.add_argument(
        "--threshold",
        nargs="*",
        type=float,
        default=[0.6],
        help='Threshold(s) to use with partial clustering.',
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="overlap",
        choices=["global", "local", "overlap", "dialign"],
        help='Alignment mode.',
    )
    parser.add_argument(
        "--cluster_method",
        type=str,
        choices=["upgma", "infomap"],
        default="infomap",
        help='Method to use in clustering.',
    )
    parser.add_argument(
        "--idtype",
        type=str,
        choices=["loose", "strict"],
        default="strict",
        help="Manner of unifying multiple cognate ids."
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=2000,
        help='Number of runs for lexstat scorer.',
    )
    parser.add_argument(
        "--file_out",
        type=str,
        default="output/pano_analysis_partial",
    )


def run(args):

    analyze_partial(method=args.method, thresholds=args.threshold,
                    mode=args.mode, cluster_method=args.cluster_method,
                    idtype=args.idtype,
                    runs=args.runs, file_out=args.file_out)


if __name__ == "__main__":
    parser_ = argparse.ArgumentParser()
    register(parser_)
    run(parser_.parse_args())
