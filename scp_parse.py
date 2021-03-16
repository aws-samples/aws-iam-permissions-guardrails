# © 2021 Amazon Web Services, Inc. or its affiliates. All Rights Reserved.
#
# This AWS Content is provided subject to the terms of the AWS Customer Agreement
# available at http://aws.amazon.com/agreement or other written agreement between
# Customer and either Amazon Web Services, Inc. or Amazon Web Services EMEA SARL or both.

import json
import re
import sys
import os

# function to append SCPs to policy document
def appendSCP(policy_doc, scp_json):
    statement = {
        "Sid": scp_json["Guardrail"],
        "Effect": "Deny",
        "Action": scp_json["IAM Actions"],
        "Resource": scp_json["Resource"],
    }
    if "Condition" in scp_json:
        statement["Condition"] = scp_json["Condition"][0]

    policy_doc["Statement"].extend([statement])

# function to replace parameters throughout SCPs
def formatSCP(service_control_policy_string, input_json, list_scps=["Mandatory"]):
    # replacing mandatory parameters
    for param in input_json["Mandatory"]:
    	replace_var = f"[{param}]"
    	service_control_policy_string = service_control_policy_string.replace(
	        replace_var,
	        input_json["Mandatory"][param])

    # wildcard Region and Account
    replace_vars = ["${Region}", "${Account}"]
    regex = re.compile('|'.join(map(re.escape, replace_vars)))
    service_control_policy_string = regex.sub("*", service_control_policy_string)

    # handling additionally specified SCPs
    if list_scps[0] != "Mandatory":
    	for scp in list_scps:
    		for param in input_json["Additional"][scp]:
    			replace_var = f"[{param}]"
    			service_control_policy_string = service_control_policy_string.replace(
			        replace_var,
			        input_json["Additional"][scp][param])

    # removing spaces and periods
    trimmed_json = re.sub("\s+", "", service_control_policy_string)
    trimmed_json = re.sub("\.", "", trimmed_json)
    return trimmed_json

def main():
    policy_doc = {"Version": "2012-10-17", "Statement": []}
    additional_doc = {"Version": "2012-10-17", "Statement": []}

    # reading input json parameter file
    input_file = open("scp_parse_input.json")
    input_json = json.load(input_file)
    input_file.close()
    list_scps = input_json["Additional"]["SCPs"]

    # walking through guardrail files
    for root, dirs, files in os.walk("guardrails"):
        for name in files:
            if "SCP-" in name:
                # reading file
                # validate json file?
                scp_file = open(os.path.join(root, name),)
                scp_json = json.load(scp_file)
                scp_file.close()

                # appending mandatory guardrails
                if scp_json["Category"] == "Mandatory":
                    appendSCP(policy_doc,scp_json)
                # handling additionally specified guardrails
                elif scp_json["Identifier"] in list_scps:
                    appendSCP(additional_doc,scp_json)

    # final policy document for mandatory SCPs
    mandatory_scps = formatSCP(json.dumps(policy_doc), input_json)
    with open('mandatory_scps.json', 'w') as outfile:
        json.dump(json.loads(mandatory_scps), outfile)
    print("Mandatory SCP document below:")
    print(mandatory_scps)
    print("----")

    # final policy document for specified SCPs, if valid
    if additional_doc["Statement"]:
        additional_scps = formatSCP(json.dumps(additional_doc), input_json, list_scps)
        with open('additional_scps.json', 'w') as outfile:
            json.dump(json.loads(additional_scps), outfile)
        print("Additional SCP document below:")
        print(additional_scps)
        print("----")

if __name__ == "__main__":
    main()