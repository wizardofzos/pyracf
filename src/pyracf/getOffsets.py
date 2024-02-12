#!/usr/bin/env python3

import re
import requests
import json
from bs4 import BeautifulSoup

urls = [
"https://www.ibm.com/docs/en/SSLTBW_3.1.0/com.ibm.zos.v3r1.icha300/format.htm",
"https://www.ibm.com/docs/en/SSLTBW_3.1.0/com.ibm.zos.v3r1.icha300/usr.htm",
"https://www.ibm.com/docs/en/SSLTBW_3.1.0/com.ibm.zos.v3r1.icha300/dsr.htm",
"https://www.ibm.com/docs/en/SSLTBW_3.1.0/com.ibm.zos.v3r1.icha300/grr.htm"
]

model = {}

for url in urls:
  w_html = requests.get(url)
  w = BeautifulSoup(w_html.text, "html.parser")

  for wtype in w.find_all(["h2","h3"]):
    try:
      [rdesc,rtype,*_] = re.split("[\(\)]",wtype.string)
    except:
      print("Funny header:",wtype.string)
    else:
      rdesc = re.sub("\s"," ",rdesc)  # newlines in description...
      print(rtype,":",rdesc)
      wtable = wtype.find_next_sibling().find("tbody")
      rfields = []
      for wrow in wtable.find_all("tr"):
        wfields = wrow.find_all("td")
        rfields.append({
          "field-name": wfields[0].string,
          "type": wfields[1].string,
          "start": wfields[2].string,
          "end": wfields[3].string,
          "field-desc": wfields[4].string
        })
      model.update({
        rdesc: {
          "record-type": rtype,
          "ref-url": url,
          "offsets": rfields
      }})

with open('offsets.json', 'w') as f:
    json.dump(model, f, indent=4)
