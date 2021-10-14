# Creating the TSV/SQLITE Data for EDICTOR Processing

This is done with the script `raw/preprocessing.py` and the command:

```shell
edictor wordlist --preprocessing=raw/preprocessing.py --addon=language_family:family --sqlite --name=keypano
```

The `PyEDICTOR` package then loads the data from CLDF in the form of a wordlist, analyzes this wordlist with the help of the code given in the function `run` in `raw/preprocessing.py` and outputs the data in the form of an SQLITE database which can be accessed by EDICTOR's web application. Without `--sqlite`, the output will be in the form of a LingPy wordlist.
