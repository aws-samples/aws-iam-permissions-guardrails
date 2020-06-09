# Short Description


# Template parameter

WhitelistedPrincipalArns is a comma seperated list, it can not be a group, need to be either list of user and role arns, since you cannnot specify group as key policy principles.


# Deploy Steps
rdk deploy SCHEDULE_KEY_DELETION_ACCESS_RULE --rdklib-layer-arn YOUR_RDKLIB_LAYER_ARN

python3 create-key-evaluation-execution-role-stack-set.py 

python3 create-organizational-config-rule.py -r us-east-1

