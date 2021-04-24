from re import findall, DOTALL, sub
import urllib
from urllib.request import urlopen, Request
from lingpy import *

def html2uni(word):
    
    outs = findall(r'&#(.*?);',word)
    neword = word
    for out in outs:
        neword = neword.replace('&#'+out+';',unichr(int(out)))
    return neword

def getPons(word, lang1='spanisch', lang2='deutsch'):
    
    # [i] make the headers and data for urllib2 
    user_agent = 'Mozilla/5.0 (compatible; MSIE 7.7; Windows NT)'
    values = {}
    data = urllib.parse.urlencode(values)
    headers = {b'User-Agent': bytes(user_agent, "utf-8")}

    word = urllib.parse.quote(word)

    url = 'http://de.pons.eu/'+lang1+'-'+lang2+'/'+word
    print(url)
    try:
        html = urlopen(url).read().decode("utf-8")
    except UnicodeEncodeError:
        print("[!] ", word)
        return False
    ipa = findall(word+r'.*<span class=.phonetics.>\[(.*?)\]</span>',html)

    if len(ipa) == 0:
        return False
    else:
        return html2uni(ipa[0])

wl = Wordlist('ids-data.tsv')
parsed = [x.split("\t")[0] for x in open('spanish.tsv', 'r')]
print(parsed)
out = open('spanish.tsv', 'a')
for idx in wl:
    if wl[idx, 'doculect'] == 'Spanish':
        print(wl[idx, 'form'])
        if wl[idx, "form"] not in parsed:
            ipa = getPons(wl[idx, 'form'].replace("ɲ", "ñ"))
            if ipa:
                out.write(wl[idx, 'form']+'\t'+ipa+'\n')
            else:
                out.write(wl[idx, 'form']+'\t\n')
out.close()
