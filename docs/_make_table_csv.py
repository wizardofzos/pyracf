"""create a csv for DataFrames.rst by reading the _recordtype_info table"""
import sys
import csv
import os
import importlib

new_path = os.path.dirname(os.path.abspath(__file__))+'/../src'
sys.path.append(new_path)

from pyracf import RACF

r = RACF()

hardcoded_publisher = {
    'GRSIGN':'SSIGNON'
}
hardcoded_desc = {
    'GRST':'STARTED Class',
    'GRSV':'Systemview'
}

record_type_table = []
fields =  ['Type','Name','DataFrame','Description']
for type,item in r._recordtype_info.items():
    name = item['name']
    df = item['df']
    publisher = item['publisher'] if 'publisher' in item else item['df'].lstrip('_')
    if not publisher:  # if publisher was not declared False
	    if name in hardcoded_publisher:
	        publisher = hardcoded_publisher[name]
	    else: publisher = ''
        
    if name in hardcoded_desc:
        desc = hardcoded_desc[name]
    else:
        desc = item['offsets'][0]['field-desc']
        desc = desc.replace('Record type of the','')
        desc = desc.replace('Record Type of the','')
        desc = desc.replace(' record','')
        desc = desc.replace(' Record','')
        desc = desc.split('(')[0].strip()
    record_type_table.append([type,name,publisher,desc])

filename = "record_type_table.csv"
with open(filename, 'w') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerows(record_type_table)

