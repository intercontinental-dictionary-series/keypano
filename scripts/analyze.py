from lingpy import *
from lingpy.evaluate.acd import bcubes
from clldutils.clilib import Table, add_format

def make_analyze_pano():
    lex = LexStat.from_cldf("cldf/cldf-metadata.json", 
        columns=("language_id", "concept_name", "value", "form", 
            "segments", "language_subgroup", "language_family"))
        # namespace=(("language_family", "family")))

    lex.output('tsv', filename='analyze.pano', ignore='all', prettify=False)

def run_analyze(use_lexstat):
    table = []
    lex = LexStat("analyze.pano.tsv")
    if use_lexstat:  # args.lexstat:
        method = "lexstat"
        lex.get_scorer(method="lexstat", runs=1000)
    else:
        method = "sca"

    # for i, t in enumerate([0.5, 0.55, 0.6, 0.65, 0.7]):
    for i, t in enumerate([0.5, 0.7]):  # Test extremes.
        # args.log.info("loaded data")
        print("loaded data")
        lex.cluster(method=method, threshold=t, ref="scallid_{0}".format(i))
        lex.add_entries("sca_{0}".format(i), "scallid_{0},language_family".format(i), lambda x, y:
                str(x[y[0]])+"-"+x[y[1]])
        lex.renumber("sca_{0}".format(i))
        etd = lex.get_etymdict(ref="scallid_{0}".format(i))
        nulls = {}
        for cogid, vals in etd.items():
            idxs = []
            for v in vals:
                if v:
                    idxs += v
            famis = [lex[idx, 'language_family'] for idx in idxs]
            if len(set(famis)) == 1:
                for idx in idxs:
                    lex[idx, 'scallid_{0}'.format(i)] = 0

        # p1, r1, f1 = bcubes(lex, "ucogid", "sca_{0}id".format(i), pprint=False)
        # p2, r2, f2 = bcubes(lex, "uborid", "scallid_{0}".format(i), pprint=False)
        # table += [[t, p1, r1, f1, p2, r2, f2]]
    # with Table(args, "Threshold", "P1", "R1", "F1", "P2", "R2", "F2") as tab:
    #     for row in table:
    #         tab.append(row)

    lex.output('tsv', filename='analyze.pano.result', ignore='all', prettify=False)

# make_analyze_pano()

run_analyze(use_lexstat=True)
