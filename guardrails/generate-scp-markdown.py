import os
from pathlib import Path
import json
import pandas

import jinja2
from jinja2 import Template

prefix="../docs/guardrails"
scp_filename=f"{prefix}/scp-guardrails.md"

layout_header="""---
layout: default
---


# Table of Contents
"""

def to_pretty_json(value):
    return json.dumps(value, sort_keys=True,
                      indent=4, separators=(',', ': '))

def get_template():
  templateLoader = jinja2.FileSystemLoader(searchpath="./")
  templateEnv = jinja2.Environment(loader=templateLoader)
  templateEnv.filters['tojson_pretty']=to_pretty_json
  TEMPLATE_FILE = "scp-template.md"
  template = templateEnv.get_template(TEMPLATE_FILE)
  return template


def generate_markdown_from_files(foldername):
  scp_frames=[]
  scp_guardrails=[]

  #print("folder",foldername)
  files=os.listdir(foldername)
  files.sort()
  for filename in files:
    #print(filename)
    with open(f"{foldername}/{filename}") as json_file:
      data=json.load(json_file)
      if "Policy-Type" in data and data["Policy-Type"]=="SCP":
        conditions={}
        if "Condition" in data:
          for condition in data["Condition"]:
            for key,value in condition.items():
              conditions[key]=value
          conditions=json.dumps(conditions,indent=4,sort_keys=True)
          data["conditions"]=conditions
          print(conditions)
        scp_frames.append(data)
        identifier=data['Identifier'].lower()
        scp_guardrails.append(f"* [{data['Guardrail']}](#{identifier})")

  scp_template=get_template()
  outputtext=scp_template.render(scps=scp_frames)
  print(outputtext)
  print(scp_guardrails)
  with open(scp_filename,'a') as out:
    out.write(outputtext)
    out.write("\n\n\n\n\n\n")

  return scp_guardrails

if __name__ == "__main__":
  with open(scp_filename,'w') as out:
    out.write(layout_header)
    out.write("\n\n\n")

  indexes=[]
  files = os.listdir(os.curdir)
  files.sort()
  for filename in files:
    if os.path.isdir(filename):
      index=generate_markdown_from_files(filename)
      if index: indexes.append(index)

  for index in indexes:
    for i in index:
      print(i) 
