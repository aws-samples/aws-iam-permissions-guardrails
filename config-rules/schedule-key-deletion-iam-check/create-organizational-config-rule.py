#!/usr/bin/python3
import logging
import sys
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

import distutils
import boto3
import argparse
import sys

import json

lambda_function_arn=""
execution_role_name = "key-evaluation-execution-role"
whitelisted_aws_principal_arns=""
excluded_accts=""
region=""

parser = argparse.ArgumentParser()
parser.add_argument("--region", "-r", help="Set deployment region", required=True)
parser.add_argument("--functionarn", "-f", help="Lambda function arn that backs up organization config rule")
parser.add_argument("--rolename", "-n", help="Key evaluation execution role name")
parser.add_argument("--whitelistedawsprincipalarns", "-waws", help="Comma separated whitelisted AWS principals arns")
parser.add_argument("--excludedaccts", "-a", help="Comma seperated accounts ids to exclude from the organization config rule deployment")

# read arguments from the command line
args = parser.parse_args()
logger.info(f"args {args}")

if args.region:
    logger.info("Deployment region is:  %s" % args.region)
    region = args.region
if args.functionarn:
    logger.info("Lambda function arn is: %s" % args.functionarn)
    lambda_function_arn = args.functionarn
if args.rolename:
    logger.info("Key evaluation execution role name is: %s" % args.rolename)
    execution_role_name = args.rolename
if args.whitelistedawsprincipalarns:
    logger.info("Whitelisted AWS principals arns are: %s" % args.whitelistedawsprincipalarns)
    whitelisted_aws_principal_arns = args.whitelistedawsprincipalarns
if args.excludedaccts:
    logger.info("Excluded accounts ids are : %s" % args.excludedaccts)
    excluded_accts = args.excludedaccts

try:
    client = boto3.client('config', region)

    if not lambda_function_arn:
      account_id=boto3.client('sts').get_caller_identity().get('Account')
      lambda_function_arn="arn:aws:lambda:{}:{}:function:RDK-Rule-Function-SCHEDULE_KEY_DELETION_ACCESS_RULE".format((region), (account_id))
      logger.info("Lambda Function Arn {}".format((lambda_function_arn)))

    logger.info(f"whitelisted_aws_principal_arns {whitelisted_aws_principal_arns}")
    whitelisted_aws_principal_arns=whitelisted_aws_principal_arns.split(",") if whitelisted_aws_principal_arns else []

    logger.info(f"Execution Role Name {execution_role_name} Whitelisted AWS Principal Arns {whitelisted_aws_principal_arns}") 
    rule_input_parameters = {
        "ExecutionRoleName":execution_role_name,
        "WhitelistedAWSPrincipalArns":whitelisted_aws_principal_arns
    }

    response = client.put_organization_config_rule(
            OrganizationConfigRuleName='ScheduleKeyDeletionAccess7',
            OrganizationCustomRuleMetadata={
                "Description": "Organization config rule checking if allows scheduling key deletion.",
                "LambdaFunctionArn": lambda_function_arn,
                "OrganizationConfigRuleTriggerTypes": [
                    "ConfigurationItemChangeNotification",
                    "ScheduledNotification"
                ],
                "InputParameters": json.dumps(rule_input_parameters),
                "ResourceTypesScope": ["AWS::KMS::Key"],
            },
            ExcludedAccounts=excluded_accts.split(",") if excluded_accts else []
    )
    OrganizationConfigRuleArn=response['OrganizationConfigRuleArn']
    logger.info("OrganizationConfigRuleArn is {}".format((OrganizationConfigRuleArn)))
except Exception as e:
    logger.exception("Error creationg Organizational Config Rule")
    logger.info(e.__dict__)
    e = sys.exc_info()[0]
    if e.response != None:
        logger.info("Detailed error: ",e.response )
