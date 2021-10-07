"""
Analysis output -- some variable interpretations:
scalllid_{i} - cognate id for cognates that cross families.
sca_{i} - cognate id and language family for cognates whether or not they cross families.
sca_{i}ID - cognate id and family combination renumbered as integer.

"""
from pathlib import Path
import argparse
from lingpy import *
from lingpy.compare.partial import Partial
import keypanocommands.util as util


# See lingrex/borrowing for use of different modules.
def analyze_lexstat(module=None,
                    method='lexstat',
                    model='sca',
                    thresholds=None,
                    runs=1000,
                    mode='overlap',
                    cluster_method='infomap',
                    idtype='loose',
                    store='store',
                    series='analysis',
                    label=""):

    # method: sca, lexstat, edit-dist, turchin
    # mode: global, local, overlap, dialign
    # cluster_method: upgma, infomap

    dataset = util.compose_wl()
    if module == 'cluster':
        wl = LexStat(dataset)
        if method == "lexstat":
            wl.get_scorer(runs=runs, ratio=(3, 2))
    elif module == 'partial':
        wl = Partial(dataset, check=True)
        if method == "lexstat":
            # partial scorer errors.
            wl.get_scorer(runs=runs, ratio=(3, 2))
    else:
        raise NameError(f"{module} not a known cluster module.")

    for i, t in enumerate(thresholds):
        print(f"Processing for threshold {t:.3f}")
        # Cluster using specified method and threshold
        # Cluster id stored in wordlist as variable scallid_{i}.
        sca_id = "scallid_{0}".format(i)
        if module == 'cluster':
            wl.cluster(method=method,
                       model=model,
                       threshold=t,
                       mode=mode,
                       cluster_method=cluster_method,
                       ref=sca_id)
        elif module == 'partial':
            sca_ids = "scallids_{0}".format(i)
            wl.partial_cluster(method=method,
                               model=model,
                               threshold=t,
                               mode=mode,
                               cluster_method=cluster_method,
                               ref=sca_ids)
            # Construct single cognate ids from lists of ids.
            wl.add_cognate_ids(sca_ids, sca_id, idtype=idtype)  # or 'strict'
            # Could also align partial cognates for output.
        else:
            raise NameError(f"{module} not a known cluster module.")

        # Add entries for cluster id combined with language family.
        # Formatting provided by lambda expression. Not obvious!
        wl.add_entries("sca_{0}".format(i), sca_id+",language_family",
                       lambda x, y: str(x[y[0]]) + "-" + x[y[1]])
        # Renumber combination of cluster_id, family as integer.
        # Store in sca_{0}ID by default.
        wl.renumber("sca_{0}".format(i))
        # Get dictionary representations of cluster ids.
        # Seems to be dictionary for each row.
        etd = wl.get_etymdict(ref=sca_id)

        # Zero out cluster ids (cognate ids) that do not cross families.
        for cogid, values in etd.items():
            # John: Construct list of row indices for this cognate id.
            idxs = []
            for v in values:
                if v:
                    idxs += v
            # Form list of language families.
            families = [wl[idx, 'language_family'] for idx in idxs]
            # If set of just 1 family then local cognate.
            if len(set(families)) == 1:
                for idx in idxs:
                    # Set cognate id to 0 since just 1 family.
                    wl[idx, sca_id] = 0

    filename = f"{module}{'-' if series else ''}{series}{'-' if label else ''}{label}"
    file_path = Path(store).joinpath(filename).as_posix()
    wl.output('tsv', filename=file_path, ignore='all', prettify=False)
    wl.output('qlc', filename=file_path, ignore=['scorer'], prettify=False)


def register(parser):
    parser.add_argument(
        "module",
        type=str,
        choices=["cluster", "partial"],
        help='Which clustering module to use.',
    )
    parser.add_argument(
        "--method",
        type=str,
        choices=["sca", "lexstat", "edit-dist", "turchin"],
        default="lexstat",
        help='Scoring method (default: "lexstat").',
    )
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
        default=[0.5],
        help='Threshold(s) to use for clustering.',
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["global", "local", "overlap", "dialign"],
        default="overlap",
        help='Mode used for alignment.',
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
        default="loose",
        help="Manner of unifying multiple cognate ids."
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1000,
        help='Number of runs for lexstat scorer.',
    )
    parser.add_argument(
        "--store",
        type=str,
        default="store",
        help='Directory to store analysis wordlist.'
    )
    parser.add_argument(
        "--series",
        type=str,
        default=""
    )
    parser.add_argument(
        "--label",
        type=str,
        default=""
    )


def run(args):
    analyze_lexstat(module=args.module,
                    method=args.method,
                    model=args.model,
                    thresholds=args.threshold,
                    mode=args.mode,
                    cluster_method=args.cluster_method,
                    idtype=args.idtype,
                    runs=args.runs,
                    store=args.store,
                    series=args.series,
                    label=args.label)


if __name__ == "__main__":
    parser_ = argparse.ArgumentParser()
    register(parser_)
    run(parser_.parse_args())
