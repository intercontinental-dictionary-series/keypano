import pathlib
import attr
from clldutils.misc import slug
from pylexibank import progressbar as pb
from pylexibank import Language
from pylexibank import FormSpec
import pycldf
from idspy import IDSDataset
from lingpy import Wordlist


@attr.s
class CustomLanguage(Language):
    Location = attr.ib(default=None)
    Remark = attr.ib(default=None)


class Dataset(IDSDataset):
    dir = pathlib.Path(__file__).parent
    id = "keypano"
    language_class = CustomLanguage
    form_spec = FormSpec(
            replacements=[(" ", "_")], 
            separators="~;,/", missing_data=["∅"], first_form_only=True)

    def cmd_download(self, args):
        ids_data = pycldf.Dataset.from_metadata(
                self.raw_dir.joinpath('ids', 'cldf', 'cldf-metadata.json')
                )
        ids = set([row["IDS_ID"] for row in self.languages])
        with open(self.raw_dir.joinpath("ids-data.tsv").as_posix(), "w") as f:
            f.write("\t".join([
                "ID", "FORM_ID", "DOCULECT", "DOCULECT_ID", "CONCEPT", "CONCEPT_ID",
                "VALUE", "FORM", "BORROWING"])+"\n") 
            for i, form in pb(enumerate(ids_data.objects("FormTable")), desc="adding forms"):
                if form.language.id in ids:
                    f.write("\t".join([
                        str(i+1),
                        form.id,
                        form.language.name,
                        form.language.id,
                        form.parameter.name,
                        form.parameter.id,
                        form.data["Value"],
                        form.data["Form"],
                        "1" if "[" in form.data["Value"] else ""
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
            args.writer.add_language(
                **{k: lang.data[k] for k in ["ID", "Name", "Glottocode", 
                                        "ISO639P3code", "Latitude",
                                        "Longitude"
                ]})
                
        for language in ids_data.objects("LanguageTable"):
            if language.id in ids:
                if language.name == "Spanish":
                    for lid in ["SpanishEU", "SpanishLA"]:
                        language.data["ID"] = lid
                        add_language_(language)
                elif language.name == "Portuguese":
                    for lid in ["PortugueseEU", "PortugueseBR"]:
                        language.data["ID"] = lid
                        add_language_(language)

                language.data["ID"] = ids[language.id]
                add_language_(language)
        args.log.info("added languages")
        
        def add_form_(wl, idx, docid=None):
            args.writer.add_form(
                ID=wl[idx, "form_id"],
                Language_ID=docid or ids[wl[idx, "doculect_id"]],
                Parameter_ID=wl[idx, "concept_id"],
                Form=wl[idx, "form"].replace(" ", "_"),
                Value=wl[idx, "value"],
                Loan=True if wl[idx, "borrowing"] else None)
                
        wl = Wordlist(self.raw_dir.joinpath("ids-data.tsv").as_posix())
        for idx in pb(wl, desc="adding forms"):
            if ids[wl[idx, "doculect_id"]] == "Spanish":
                for lid in ["SpanishEU", "SpanishLA"]:
                    add_form_(wl, idx, lid)
            elif ids[wl[idx, "doculect_id"]] == "Portuguese":
                for lid in ["PortugueseEU", "PortugueseBR"]:
                    add_form_(wl, idx, lid)

            add_form_(wl, idx)

