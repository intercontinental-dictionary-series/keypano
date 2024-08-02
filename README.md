# CLDF dataset Prepared for a Study of Panoan Languages

## How to cite

If you use these data please cite
- the original source
  > +++
- the derived dataset using the DOI of the [particular released version](../../releases/) you were using

## Description


This dataset is licensed under a CC-BY-4.0 license

Available online at https://ids.clld.org

## Notes

# Creating the TSV/SQLITE Data for EDICTOR Processing

This is done with the script `raw/preprocessing.py` and the command:

```shell
edictor wordlist --preprocessing=raw/preprocessing.py --addon=language_family:family --sqlite --name=keypano
```

The `PyEDICTOR` package then loads the data from CLDF in the form of a wordlist, analyzes this wordlist with the help of the code given in the function `run` in `raw/preprocessing.py` and outputs the data in the form of an SQLITE database which can be accessed by EDICTOR's web application. Without `--sqlite`, the output will be in the form of a LingPy wordlist.



## Statistics


[![Build Status](https://travis-ci.org/intercontinental-dictionary-series/keypano.svg?branch=master)](https://travis-ci.org/intercontinental-dictionary-series/keypano)
![Glottolog: 100%](https://img.shields.io/badge/Glottolog-100%25-brightgreen.svg "Glottolog: 100%")
![Concepticon: 100%](https://img.shields.io/badge/Concepticon-100%25-brightgreen.svg "Concepticon: 100%")
![Source: 0%](https://img.shields.io/badge/Source-0%25-red.svg "Source: 0%")
![BIPA: 100%](https://img.shields.io/badge/BIPA-100%25-brightgreen.svg "BIPA: 100%")
![CLTS SoundClass: 100%](https://img.shields.io/badge/CLTS%20SoundClass-100%25-brightgreen.svg "CLTS SoundClass: 100%")

- **Varieties:** 22 (linked to 21 different Glottocodes)
- **Concepts:** 1,310 (linked to 1,308 different Concepticon concept sets)
- **Lexemes:** 23,232
- **Sources:** 0
- **Synonymy:** 1.24
- **Invalid lexemes:** 0
- **Tokens:** 146,061
- **Segments:** 120 (0 BIPA errors, 0 CLTS sound class errors, 120 CLTS modified)
- **Inventory size (avg):** 32.45

## Possible Improvements:



- Entries missing sources: 23232/23232 (100.00%)

# Contributors

Name | GitHub user | Description | Role |
--- | --- | --- | --- |
Uday Raj Aaley| |publication author, fieldwork | Author, RightsHolder, Distributor
Timotheus A. Bodt| | publication author, fieldwork, orthography profile | Author, RightsHolder, Distributor
Mei-Shin Wu | @macyl | patron, maintainer | Other
Johann-Mattis List | @LinguList| orthography profile, maintainer | Other




## CLDF Datasets

The following CLDF datasets are available in [cldf](cldf):

- CLDF [Wordlist](https://github.com/cldf/cldf/tree/master/modules/Wordlist) at [cldf/cldf-metadata.json](cldf/cldf-metadata.json)