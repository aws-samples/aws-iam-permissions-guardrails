"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0
"""
import os
from pathlib import Path
import json
import pandas

template_header="""---
layout: default
---

## {name}

"""


names = {}
with open("names.csv") as f:
    for line in f:
       (key, val) = line.split("=")
       names[key] = val.strip()

def generate_markdown_from_files(foldername):
  frames=[]
  files=os.listdir(foldername)
  files.sort()
  for filename in files:
    print(filename)
    with open(f"{foldername}/{filename}") as json_file:
      data=json.load(json_file)
      del data["Authorized Principals"]
      print(len(data))
      frames.append(data)

  result=pandas.DataFrame(frames)
  print(result.shape)
  print(result.columns)
  md=result.to_markdown(showindex=False)
  prefix="../docs/guardrails"
  folder=f"{prefix}/{foldername}"
  Path(folder).mkdir(parents=True,exist_ok=True) 
  md_filename=f"{prefix}/{foldername}/guardrails.md"
  print(md_filename)
  service_name=names[foldername]
  with open(md_filename,'w') as out:
    out.write(template_header.format(name=service_name))
    out.write(md)

  index=f"[{service_name}](./guardrails/{foldername}/guardrails.html)"
  return index

if __name__ == "__main__":
  indexes=[]
  files = os.listdir(os.curdir)
  files.sort()
  for filename in files:
    if os.path.isdir(filename):
      index=generate_markdown_from_files(filename)
      indexes.append(index)

  for index in indexes:
    print(index)
    print("")
