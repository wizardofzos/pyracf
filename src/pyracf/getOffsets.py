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
      rdesc = rdesc.strip().lower().replace(" ","-")
      wtable = wtype.find_next_sibling().find("tbody")
      rfields = []
      for wrow in wtable.find_all("tr"):
        wfields = wrow.find_all("td")
        # some <td>s contain <svg> tags for changes, so the string is not the only descendant of <td> and we have to resort to strings
        wf = [re.sub("\W","",str(list(wfields[i].strings)[0])) for i in range(4)]  # remove strash that could crash parsing
        wf.append(re.sub("[\s\u00ae]"," ",str(list(wfields[4].strings)[0])))  # remove newlines and (R) in long description
        rfields.append({
            "field-name": wf[0] if wf[0]!="" else "RESERVED",
            "type": wf[1],
            "start": wf[2],
            "end": wf[3],
            "field-desc": wf[4]
        })
      model.update({
        rdesc: {
          "record-type": rtype.upper(),  # 05k0 is in fact 05K0
          "ref-url": url,
          "offsets": rfields
      }})

with open('offsets.json', 'w') as f:
    json.dump(model, f, indent=4)
