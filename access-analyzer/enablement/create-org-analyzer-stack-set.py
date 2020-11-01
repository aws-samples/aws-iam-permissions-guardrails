import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

import argparse

import boto3
from botocore.waiter import SingleWaiterConfig, Waiter

delegated_account=""
excluded_regions=[]
parser = argparse.ArgumentParser()
parser.add_argument("--delegated_account", "-delegate", help="Delegated Account, typically your audit or security account number", required=True)
parser.add_argument("--excluded_regions","-excluded_regions",help="Regions to exclude as comma separated list, such as those not activate by your organization and unable to deploy",required=False)
args = parser.parse_args()
logger.info(f"args {args}")

if args.delegated_account:
  logger.info(f"Delegated account number is: {args.delegated_account}")
  delegated_account = args.delegated_account
if args.excluded_regions:
  logger.info(f"Excluded regions are: {args.excluded_regions}")
  excluded_regions=args.excluded_regions.split(",")

waiter_config = SingleWaiterConfig({
  'delay': 10,
  'operation': 'DescribeStackSetOperation',
  'maxAttempts': 360,
  'acceptors': [
    {
      'argument': 'StackSetOperation.Status',
      'expected': 'SUCCEEDED',
      'matcher': 'path',
      'state': 'success'
    },
    {
      'argument': 'StackSetOperation.Status',
      'expected': 'FAILED',
      'matcher': 'path',
      'state': 'failure'
    },
    {
      'argument': 'StackSetOperation.Status',
      'expected': 'STOPPED',
      'matcher': 'path',
      'state': 'failure'
    },
    {
      'expected': 'ValidationError',
      'matcher': 'error',
      'state': 'failure'
    }
  ]
})

cloudformation_client=boto3.client("cloudformation")

cfn=None
with open('org-analyzer.yaml', 'r') as myfile:
  cfn = myfile.read()

StackSetName="access-analyzer-organization"

sts_client=boto3.client("sts")
primary_account_id=sts_client.get_caller_identity()['Account']

response=cloudformation_client.create_stack_set(
  StackSetName=StackSetName,
  Description="Access Analyzer Organizations",
  TemplateBody=cfn,
  Capabilities=["CAPABILITY_IAM","CAPABILITY_NAMED_IAM"],
  PermissionModel='SELF_MANAGED',
  AdministrationRoleARN=f'arn:aws:iam::{primary_account_id}:role/service-role/AWSControlTowerStackSetRole',
  ExecutionRoleName='AWSControlTowerExecution',
)
stack_set_id=response['StackSetId']
print("Stack Set Id is {}".format((stack_set_id)))

waiter = Waiter('StackSetOperationComplete', waiter_config, cloudformation_client.describe_stack_set_operation)

ec2_client = boto3.client('ec2')
all_regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]
for region in excluded_regions:
  all_regions.remove(region)  

response=cloudformation_client.create_stack_instances(
  StackSetName=StackSetName,
  DeploymentTargets={
    'Accounts':[delegated_account]
  },
  Regions=all_regions,
   OperationPreferences={
     'FailureToleranceCount': 1,
     'MaxConcurrentCount': 10
   }
)

operation_id=response['OperationId']
print("Create Stack Instances Operation Id is {}".format((operation_id)))

waiter.wait(
    StackSetName=StackSetName,
    OperationId=operation_id
)

