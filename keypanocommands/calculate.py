"""
    Calculate and display tree based on cognate data.
"""
import argparse

from lingpy import *


def make_tree(lex=None, ref=0):
    ref = f'scallid_{ref}'
    lex.calculate('tree', tree_calc='neighbor', ref=ref)
    print(lex.tree)
    print(lex.tree.asciiArt())


def register(parser):
    parser.add_argument(
        "--dataset",
        type=str,
        default="output/pano_analysis",
    )
    parser.add_argument(
        "--ref",
        type=int,
        default=0,
        help="Integer indicator of which threshold used in cognate analysis."
    )


def run(args):
    lex = LexStat(args.dataset+".qlc")
    make_tree(lex, ref=args.ref)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    register(parser)
    run(parser.parse_args())

