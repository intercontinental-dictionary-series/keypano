import pathlib
import regex as re
import attr
# from clldutils.misc import slug
from pylexibank import progressbar as pb
from pylexibank import Language
from pylexibank import FormSpec
import pycldf

from lingpy import Wordlist

try:
    from idspy import IDSDataset
except ImportError:
    from pylexibank import Dataset as IDSDataset


@attr.s
class CustomLanguage(Language):
    Location = attr.ib(default=None)
    Remark = attr.ib(default=None)


def add_form_(args, ids, wl, idx):
    args.writer.add_form(
        ID=wl[idx, "form_id"],
        Language_ID=ids[wl[idx, "doculect_id"]],
        Parameter_ID=wl[idx, "concept_id"],
        Form=wl[idx, "form"].replace(" ", "_"),
        Value=wl[idx, "value"],
        Loan=True if wl[idx, "borrowing"] else False,
        Source="ids-" + wl[idx, "doculect_id"]
        )


class Dataset(IDSDataset):
    dir = pathlib.Path(__file__).parent
    id = "keypano"
    language_class = CustomLanguage
    form_spec = FormSpec(
            replacements=[(" ", "_")],
            separators="~;,/", missing_data=["∅"], first_form_only=True)

    def cmd_download(self, _):
        ids_data = pycldf.Dataset.from_metadata(
                self.raw_dir.joinpath('ids', 'cldf', 'cldf-metadata.json')
                )
        ids = set([row["IDS_ID"] for row in self.languages])

        bex = re.compile(r"\[(.+?)\]")

        def test_borrowed(word, value):
            if '[' not in value:
                return ""
            # Need to be sure it is this form.
            # Test to see if loan substring of value in form.
            # Use regex to get all borrowed substrings from value.
            # Test for whether any of borrowed substrings in form.
            loans = bex.findall(value)
            for loan in loans:
                if loan in word:
                    return "1"
            # Not this form.
            return ""

        # SOURCES HERE
        with open(self.raw_dir.joinpath("sources.bib"), "w") as f:
            for language in ids_data.objects("LanguageTable"):
                if language.id in ids:
                    f.write("@incollection{ids-" + language.id + ",\n")
                    f.write("  address = {Leipzig},\n")
                    f.write("  author={" + " and ".join(language.data["Authors"]) + "},\n")
                    f.write("  booktitle = {The Intercontinental Dictionary Series},\n")
                    f.write("  publisher = {Max Planck Institute for Evolutionary Anthropology},\n")
                    f.write("  editor = {Mary Ritchie Key and Bernard Comrie},\n")
                    f.write("  title = {" + language.name + "},\n"),
                    f.write("  url = {https://ids.clld.org/contributions/" + language.id + "},\n")
                    f.write("  year = {2023}\n}\n\n")

        with open(self.raw_dir.joinpath("ids-data.tsv").as_posix(), "w", encoding='utf8') as f:
            f.write("\t".join([
                "ID", "FORM_ID", "DOCULECT", "DOCULECT_ID", "CONCEPT", "CONCEPT_ID",
                "VALUE", "FORM", "BORROWING"])+"\n") 
            for i, form in pb(enumerate(ids_data.objects("FormTable")), desc="adding forms"):
                if form.language.id in ids:
                    f.write("\t".join([
                        str(i + 1),
                        form.id,
                        form.language.name,
                        form.language.id,
                        form.parameter.name,
                        form.parameter.id,
                        form.data["Value"],
                        form.data["Form"],
                        test_borrowed(word=form.data["Form"], value=form.data["Value"])
                        ])+"\n")

    def cmd_makecldf(self, args):
        # add bib
        args.writer.add_sources()
        args.log.info("added sources")

        ids_data = pycldf.Dataset.from_metadata(
                self.raw_dir.joinpath('ids', 'cldf', 'cldf-metadata.json')
                )
        ids = {row["IDS_ID"]: row["ID"] for row in self.languages}

        for concept in ids_data.objects('ParameterTable'):
            args.writer.add_concept(
                    **concept.data)

        def add_language_(lang):
            cols = ["ID", "Name", "Glottocode", "ISO639P3code", "Latitude", "Longitude"]
            args.writer.add_language(**{k: lang.data[k] for k in cols})

        for language in ids_data.objects("LanguageTable"):
            if language.id in ids:
                if language.name == "Spanish":
                    language.data["ID"] = "Spanish"
                    add_language_(language)
                elif language.name == "Portuguese":
                    language.data["ID"] = "Portuguese"
                    add_language_(language)
                else:
                    language.data["ID"] = ids[language.id]
                    add_language_(language)
        args.log.info("added languages")

        wl = Wordlist(self.raw_dir.joinpath("ids-data.tsv").as_posix())
        for idx in pb(wl, desc="adding forms"):
            add_form_(args, ids, wl, idx)
