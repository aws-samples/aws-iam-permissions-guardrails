import boto3
from botocore.waiter import SingleWaiterConfig, Waiter

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
lambda_client=boto3.client('lambda')

cfn=None
with open('key_evaluation_execution_role.yaml', 'r') as myfile:
  cfn = myfile.read()

StackSetName="KeyEvaluationExecutionRoleStackSet"

response=lambda_client.get_function(FunctionName="RDK-Rule-Function-SCHEDULE_KEY_DELETION_ACCESS_RULE")['Configuration']
lambda_execution_role_arn=response['Role']

response=cloudformation_client.create_stack_set(
  StackSetName=StackSetName,
  Description="The key evaluation IAM Role needed in the member accounts",
  TemplateBody=cfn,
  Parameters=[
        {
            'ParameterKey': 'MasterLambdaFunctionRoleArn',
            'ParameterValue': lambda_execution_role_arn
        },    
  ],
  Capabilities=["CAPABILITY_IAM","CAPABILITY_NAMED_IAM"],
  PermissionModel='SERVICE_MANAGED',
  AutoDeployment={
    'Enabled':True,
    'RetainStacksOnAccountRemoval': False
  }
)
stack_set_id=response['StackSetId']
print("Stack Set Id is {}".format((stack_set_id)))

organizations_client=boto3.client('organizations')
root_id = organizations_client.list_roots()['Roots'][0]['Id']

waiter = Waiter('StackSetOperationComplete', waiter_config, cloudformation_client.describe_stack_set_operation)

response=cloudformation_client.create_stack_instances(
  StackSetName=StackSetName,
  DeploymentTargets={
    'OrganizationalUnitIds':[root_id]
  },
  Regions=["us-east-1"]
)

operation_id=response['OperationId']
print("Create Stack Instances Operation Id is {}".format((operation_id)))

waiter.wait(
    StackSetName=StackSetName,
    OperationId=operation_id
)
