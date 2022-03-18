from pathlib import Path
import argparse
import csv
from lingpy import *

import keypanocommands.util as util


def get_filepath(filename):
    return Path("foreign-tables").joinpath(filename).as_posix()


def load_concepts(filename):
    concepts = dict()
    with open(filename, newline='') as fl:
        rdr = csv.reader(fl)
        print("Hdr:", next(rdr))
        for row in rdr:
            # print(row[0], row[1:])
            id = row[2] if row[2] else row[0]
            concepts[id] = row[3].lower()
    return concepts


def make_donors_table(filename):

    wl = util.compose_wl()
    language = ['SpanishLA', 'PortugueseBR']
    wl = util.select_languages(wl, languages=language, donors=None)

    print(len(wl), wl.cols, wl.width, wl.height)

    file_path = (
        Path("foreign-tables").joinpath(filename).as_posix()
    )
    wl.output('tsv', filename=file_path, ignore='all', prettify=False)

    concepts = load_concepts("cldf/parameters.csv")

    # Now process this a flat file and update concepts.
    entries = list()
    with open(file_path+'.tsv', newline='') as fl:
        rdr = csv.reader(fl, delimiter='\t')
        hdr = next(rdr)
        print("Hdr:", hdr)
        for row in rdr:
            row[3] = concepts[row[4]] if row[4] in concepts else row[3]
            entries.append(row)

    with open(file_path+'1.tsv', 'w', newline='') as fl:
        wrt = csv.writer(fl, delimiter='\t')
        wrt.writerow(hdr)
        for row in entries:
            wrt.writerow(row)


def combine_wold_donors_table(foreign_fn, donors_fn, filename):
    # Get wold and donors tables.
    # Make sure columns correspond and have same formats.

    # Open fl_out for output.
    filepath = get_filepath(filename+'.tsv')
    with open(filepath, 'wt') as fl_out:
        wrt = csv.writer(fl_out, delimiter='\t')
        # Write out header
        wrt.writerow(["language", "language_family",
                      "concept", "concept_id",
                      "value", "form", "tokens",
                      "borrowed", "borrowed_score",
                      "donor_language", "donor_value"])

        # Get wold file.
        filepath = get_filepath(foreign_fn+".tsv")
        with open(filepath) as file:
            rdr = csv.reader(file, delimiter="\t")
            header = next(rdr)
            print("foreign file header:", header)
            for row in rdr:
                # fixup possible empty concept id.
                if not row[4]: row[4] = row[3]
                row[3] = row[3].lower()
                # Drop - from tokens. Could drop + as well if needed.
                tokens = row[7]
                tokens = tokens.replace("- ", "")
                tokens = tokens.replace(" -", "")
                row[7] = tokens
                # add to output file.
                new_row = row[1:8]
                new_row.extend([bool(int(row[8]))])
                new_row.extend(row[9:])
                wrt.writerow(new_row)

        filepath = get_filepath(donors_fn+".tsv")
        with open(filepath) as file:
            rdr = csv.reader(file, delimiter="\t")
            header = next(rdr)
            print("donor file header:", header)
            for row in rdr:
                # fixup possible empty concept id.
                if not row[4]: row[4] = row[3]
                # add to output file.
                new_row = row[1:]
                wrt.writerow(new_row)

    filepath = get_filepath(filename+'.tsv')
    wl = Wordlist(filepath)

    print(len(wl), wl.cols, wl.height, wl.width)
    # print(wl.rows[:2])

    filepath = get_filepath(filename)
    wl.output('tsv', filename=filepath, ignore='all', prettify=False)


if __name__ == "__main__":
    # parser_ = argparse.ArgumentParser()
    # register(parser_)
    # run(parser_.parse_args())
    # print(load_concepts("cldf/parameters.csv"))
    # make_donors_table('donors-wordlist')
    combine_wold_donors_table(
        foreign_fn='test-wold-wordlist',
        donors_fn='donors-wordlist',
        filename='wold-with-donors-table')
