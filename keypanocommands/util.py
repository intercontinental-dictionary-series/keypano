"""
    Shared routines for keypano.

    John E. Miller, Sep 7, 2021
"""
import math
from enum import Enum
import regex as re

from lingpy import *
from lingpy.compare.util import mutual_coverage_check
from lingpy.compare.sanity import average_coverage
from lexibank_keypano import Dataset as keypano


def check_coverage(wl=None):
    print(f"Wordlist has {wl.width} languages, and {wl.height} concepts in {len(wl)} words.")
    for i in range(200, 0, -1):
        if mutual_coverage_check(wl, i):
            print(f"Minimum mutual coverage is at {i} concept pairs.")
            break
    print(f"Average coverage is at {average_coverage(wl):.2f}")


def compose_wl():
    wl = Wordlist.from_cldf(
        keypano().cldf_dir / "cldf-metadata.json",
        columns=["language_id",
                 "language_family",
                 "concept_name",
                 "concept_concepticon_id",
                 "value",
                 "form",
                 "segments",
                 "loan"])
    check_coverage(wl)
    return wl


def compose_lex():
    lex = LexStat.from_cldf(
        keypano().cldf_dir / "cldf-metadata.json",
        columns=["language_id",
                 "language_family",
                 "concept_name",
                 "concept_concepticon_id",
                 "value",
                 "form",
                 "segments",
                 "loan"])

    return lex


# Get list of thresholds from wordlist.
def get_thresholds(cluster_desc):
    tex = re.compile(r"_(\d\.\d+)")
    thresholds = tex.findall(cluster_desc)
    return [float(t) for t in thresholds]


# Enumeration of prediction versus truth for 0, 1 values.
class PredStatus(Enum):
    TN = 1
    TP = 2
    FP = 3
    FN = 4
    F = 5
    T = 6
    NTN = 7
    ALL = 0


#  Modules adapted from pybor.
def assess_pred(pred, gold):
    """
    Test 0, 1 prediction versus 0, 1 truth
    """
    if pred == gold:
        if gold == 0: return PredStatus.TN
        elif gold == 1: return PredStatus.TP
    else:
        if gold == 0: return PredStatus.FP
        elif gold == 1: return PredStatus.FN
    raise ValueError(f"Pred {pred}, gold {gold}.")


def pred_by_gold(pred, gold):
    """
    Simple stats on tn, tp, fn, fp.

    pred is list of 0, 1 predictions.
    gold is list of corresponding 0, 1 truths.
    """
    assert len(pred) == len(gold)

    tp, tn, fp, fn = 0, 0, 0, 0
    for pred_, gold_ in zip(pred, gold):
        if pred_ == gold_:
            if gold_ == 0:
                tn += 1
            elif gold_ == 1:
                tp += 1
        else:
            if gold_ == 0:
                fp += 1
            elif gold_ == 1:
                fn += 1
    if tn + tp + fn + fp != len(pred):
        print(f"Sum of scores {tn + tp + fn + fp} not equal len(pred) {len(pred)}.")
    return tp, tn, fp, fn


def prf_(tp, tn, fp, fn, return_nan=False):
    """
    Compute precision, recall, and f-score for tp, tn, fp, fn.
    """
    try:
        precision = tp / (tp + fp)
    except ZeroDivisionError:
        precision = math.nan if return_nan else 0
    try:
        recall = tp / (tp + fn)
    except ZeroDivisionError:
        recall = math.nan if return_nan else 0
    if math.isnan(precision) and math.isnan(recall):
        fs = math.nan
        # print("*** NAN ***")
    elif math.isnan(precision) or math.isnan(recall):
        # fs = 0.0
        fs = math.nan
        # print("*** Zero NAN ***")
    elif not precision and not recall:
        fs = 0.0
    else:
        fs = 2 * (precision * recall) / (precision + recall)

    total = tp + tn + fp + fn
    accuracy = (tp + tn) / total if total > 0 else 0

    return precision, recall, fs, accuracy


def prf(pred, gold, return_nan=False):
    """
    Compute precision, recall, and f-score for pred and gold.
    """
    tp, tn, fp, fn = pred_by_gold(pred, gold)
    p, r, f, a = prf_(tp, tn, fp, fn, return_nan=return_nan)
    return [tp, tn, fp, fn, p, r, f, a]


def run(args):
    ...
