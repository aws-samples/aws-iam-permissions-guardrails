"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0
"""
import os
from pathlib import Path
import json
import pandas
import csv

prefix="../docs/guardrails"
iam_roles_filename=f"{prefix}/iam-role-checks.md"

layout_header="""---
layout: default
---

"""

template_header=layout_header+"""

## {name}

"""

iam_roles_header="""


## {name}

"""


names = {}
with open("names.csv") as f:
  names_file=csv.DictReader(f)
  for row in names_file:
    names[row['servicekey']]=row

def convert_string_to_list(value):
    if isinstance(value, str):
        if not value: return []
        return [value]
    else:
        return value

def generate_markdown_from_files(foldername):
  frames=[]
  iam_actions_frames=[]
  files=os.listdir(foldername)
  files.sort()
  for filename in files:
    #print(filename)
    with open(f"{foldername}/{filename}") as json_file:
      #print(f"{json_file}")
      data=json.load(json_file)
      if "SCP-Type" in data:
        continue

      if "Identifier" in data:
        identifier=data["Identifier"]
        identifier_link=f'<a id="{identifier}" href="#{identifier}" >{identifier}</a>'
        data["Identifier"]=identifier_link
      if "Authorized Principals" in data:
        del data["Authorized Principals"]
      #print(len(data))
      if "References" in data:
        references=convert_string_to_list(data["References"])
        link_references=""
        for ref in references: 
          link_references+=f"[{ref}]({ref})<br><br>"
        data["References"]=link_references

      if "IAM Actions" in data:
        iam_actions=convert_string_to_list(data["IAM Actions"])
        link_iam_actions=""
        is_actions=False
        for action in iam_actions:
          if not action:
            continue
          service=action.split(":")[0]
          #print(iam_actions,data)
          if action!="*":
            api=action.split(":")[1]
          api=api.strip()
          if "*" not in api and service in names and "docname" in names[service] and names[service]["docname"]:
            docname=names[service]["docname"]
            if "s3"==service:
              link_iam_actions+=f"[{service}:{api}](https://docs.aws.amazon.com/{docname}/latest/API/API_{api}.html)<br>"
            else:
              link_iam_actions+=f"[{service}:{api}](https://docs.aws.amazon.com/{docname}/latest/APIReference/API_{api}.html)<br>"
          else:
            link_iam_actions+=f"{action}<br>"
        data["IAM Actions"]=link_iam_actions
        if len(iam_actions)>0:
          print(iam_actions)
          iam_actions_data=dict(data)
          if "Policy" in data:
            del data["Policy"]
          iam_actions_frames.append(data)
      frames.append(data)

  if not iam_actions_frames:
    return ""  

  recommendations=pandas.DataFrame(frames)
  #print(result.shape)
  #print(result.columns)
  recommendations_markdown=recommendations.to_markdown(showindex=False)
  folder=f"{prefix}/{foldername}"
  Path(folder).mkdir(parents=True,exist_ok=True) 
  md_filename=f"{prefix}/{foldername}/guardrails.md"
  #print(md_filename)
  print(foldername)
  service_name=names[foldername]["servicename"]
  with open(md_filename,'w') as out:
    out.write(template_header.format(name=service_name))
    out.write(recommendations_markdown)

  if iam_actions_frames:
    iam_role_recommendations=pandas.DataFrame(iam_actions_frames)
    iam_role_recommendations_markdown=iam_role_recommendations.to_markdown(showindex=False)
    with open(iam_roles_filename,'a') as out:
      out.write(iam_roles_header.format(name=service_name))
      out.write(iam_role_recommendations_markdown)
      out.write("\n\n\n")

  index=f"[{service_name}](./guardrails/{foldername}/guardrails.html)"
  return index

if __name__ == "__main__":
  #os.remove(iam_roles_filename)
  with open(iam_roles_filename,'w') as out:
    out.write(layout_header)
    out.write("\n\n\n")

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
