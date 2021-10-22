from lingpy import *
from lingpy.compare.partial import Partial
from lingrex.borrowing import internal_cognates, external_cognates
from lingrex.cognates import common_morpheme_cognates

def run(wordlist):
    
    internal_cognates(wordlist, ref="autocogids", cluster_method="infomap")
    common_morpheme_cognates(wordlist, cognates="autocogids", ref="autocogid")
    external_cognates(wordlist, ref="autoborid", cognates="autocogid")

    wordlist.add_entries("cogids", "autocogids", lambda x: x)
    wordlist.add_entries("cogid", "autocogid", lambda x: x)
    wordlist.add_entries("borid", "autoborid", lambda x: x)
    wordlist.add_entries("subgroup", "family", lambda x: x)

    alms = Alignments(wordlist, ref="cogids", transcription="form")
    alms.align()

    D = {0: [
        "doculect",
        "concept",
        "family",
        "subgroup",
        "value", 
        "form",
        "tokens",
        "morphemes",
        "autocogids",
        "autocogid",
        "cogids",
        "cogid",
        "autoborid",
        "borid",
        "alignment",
        "loan",
        "note"
        ]}
    for idx in alms:
        D[idx] = [alms[idx, h] or '' for h in D[0]]
    return D
