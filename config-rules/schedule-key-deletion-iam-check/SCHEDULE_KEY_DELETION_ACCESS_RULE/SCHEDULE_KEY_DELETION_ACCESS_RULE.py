import logging
import sys
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

import re
import json
import copy
from rdklib import Evaluator, Evaluation, ConfigRule, ComplianceType


DEFAULT_RESOURCE_TYPE = 'AWS::KMS::Key'

APPLICABLE_RESOURCES = ['AWS::KMS::Key']

PERMISSION = 'kms:ScheduleKeyDeletion'

class SCHEDULE_KEY_DELETION_ACCESS_RULE(ConfigRule):

    def evaluate_change(self, event, client_factory, configuration_item, valid_rule_parameters):
        kms_client = client_factory.build_client('kms')
        iam_client = client_factory.build_client('iam')
        evaluations = []
        account_id=event['accountId']
        whitelisted_aws_principles=valid_rule_parameters["WhitelistedAWSPrincipalArns"]
        logger.info(f"Account Id {account_id} Whitelisted AWS Principals {whitelisted_aws_principles}")
 
        logger.info(f"event is {json.dumps(event)}")
        invoking_event=json.loads(event['invokingEvent'])
        logger.info(f"invokingEvent is {json.dumps(invoking_event)}")
        configuration_item=invoking_event['configurationItem']
        configuration=configuration_item['configuration']
        key_id=configuration['keyId']
        key_arn=configuration['arn'] 
        key_state=configuration['keyState']
        key_policy=json.loads(configuration_item["supplementaryConfiguration"]['Policy'])['Statement']
        logger.info(f"key arn is {key_arn} and key id is {key_id}")
        logger.info(f"key policy is {json.dumps(key_policy)}")

        evaluation=evaluate_key(iam_client,key_state,key_policy,key_id,whitelisted_aws_principles)
        return[evaluation]        

    def evaluate_periodic(self, event, client_factory, valid_rule_parameters):
        kms_client = client_factory.build_client('kms')
        iam_client = client_factory.build_client('iam')
        evaluations = []
        account_id=event['accountId']
        whitelisted_aws_principles=valid_rule_parameters["WhitelistedAWSPrincipalArns"]
        logger.info(f"Whitelisted AWS Principals {whitelisted_aws_principles}") 

        all_kms_key_list = get_all_kms_keys(kms_client)

        if not all_kms_key_list:
            return [Evaluation(ComplianceType.NOT_APPLICABLE, resourceId=account_id, resourceType=DEFAULT_RESOURCE_TYPE)]

        for key_id in all_kms_key_list:
            kms_key_details = kms_client.describe_key(KeyId=key_id)

            key_state = kms_key_details['KeyMetadata']['KeyState']
            get_key_policy = kms_client.get_key_policy(KeyId=key_id, PolicyName='default')
            key_policy = json.loads(get_key_policy['Policy'])['Statement']
            evaluation=evaluate_key(iam_client,key_state,key_policy,key_id,whitelisted_aws_principles)
            evaluations.append(evaluation)
        return evaluations

    def evaluate_parameters(self, rule_parameters):
        """Evaluate the rule parameters dictionary validity. Raise a ValueError for invalid parameters.

        Return:
        anything suitable for the evaluate_compliance()

        Keyword arguments:
        rule_parameters -- the Key/Value dictionary of the Config Rules parameters
        """
        if rule_parameters:
            if not all(key in ['WhitelistedAWSPrincipalArns', 'ExecutionRoleName']  for key in rule_parameters.keys()):
                raise ValueError('WhitelistedPrincipalArns not in rule parameters.')

            arn_list = []
            regex_pattern = re.compile("^arn:[a-zA-Z-]+:iam::[0-9]+:.+$")
            for arn in rule_parameters['WhitelistedAWSPrincipalArns']:
                logger.info(f"updated arn {arn}")
                if not regex_pattern.match(arn):
                    raise ValueError('The KMS whitelisted Principle Arns should be '
                        'in the right format.')
                if re.compile(':group/').match(arn):
                    raise ValueError('The KMS whitelisted Principle Arns should be '
                        'users or roles, not group.')
                arn_list.append(arn.replace(" ",""))
            rule_parameters['WhitelistedPrincipalArns'] = arn_list
        else:
            rule_parameters['WhitelistedAWSPrincipalArns']=[]

        return rule_parameters

def get_all_kms_keys(kms_client):
    all_kms_key_list = []
    paginator=kms_client.get_paginator('list_keys')
    for page in paginator.paginate(PaginationConfig={'PageSize': 50}):
        for key in page['Keys']:
            all_kms_key_list.append(key['KeyId'])
    return all_kms_key_list

def evaluate_key(iam_client,key_state,key_policy,key_id,whitelisted_aws_principles):
  denied_aws_principals = set()
  allowed_aws_principals = set()

  #Tracking Deny NotPrincipals, these are the not principals that are not expliclity denied
  global_denied_aws_principals = set()

  #Principal elements https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_principal.html
  for statement in key_policy:
      evaluationresult=evaluate_key_policy(iam_client,statement)
      #not compliant if key policy is using Allow with NotPrincipal
      #We strongly recommend that you do not use NotPrincipal in the same policy statement as "Effect": "Allow"
      #https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_notprincipal.html
      if "allowed"==evaluationresult and "NotPrincipal" in statement:
        logger.info("Statement has an Allow with NotPrincipal for ScheduleKeyDeletion. Flagging as non compliant")
        return create_compliance_evaluation(False,key_state,key_id,"Statement has an Allow with NotPrincipal")

      if "Federated" in statement['Principal']:
        logger.info("Federated Principal in KMS resource policy. Flagging as non compliant as only IAM Users or IAM Roles should be specified in the resource policy.")
        return create_compliance_evaluation(False,key_state,key_id,"Statement has Federated Principal")

      logger.info(f"Principal is {statement['Principal']}")
      aws_principals=[]
      if "*" in statement["Principal"]:
        aws_principals.append("*")
      else:
        aws_principals=convert_string_to_list(statement['Principal']['AWS'])

      #need to build the global denies entries
      if "explicitDeny"==evaluationresult and "NotPrincipal" in statement:
        logger.info("Statement has an Allow with NotPrincipal for ScheduleKeyDeletion.")
        global_denied_aws_principals.update(aws_principals)
      #principals that have explicit deny for ScheduleKeyDeletion
      elif "explicitDeny" == evaluationresult and "Principal" in statement:
        denied_aws_principals.update(aws_principals)
      #principals that have allow for ScheduleKeyDeletion       
      elif "allowed" == evaluationresult and "Principal" in statement:
        allowed_aws_principals.update(aws_principals)

  for allowed_principal in allowed_aws_principals:
    if "*"==allowed_principal:
      logger.info("Statement has wildcard Principal for ScheduleKeyDeletion. Flagging as non compliant.")
      return create_compliance_evaluation(False,key_state,key_id,"Statement has wildcard Principal.")

  found_principals=check_principals(allowed_aws_principals,global_denied_aws_principals,denied_aws_principals,whitelisted_aws_principles)
  if found_principals:
    logger.info(f"Failed Principal AWS Checks {found_principals}")
    return create_compliance_evaluation(False,key_state,key_id,f"{found_principals}")

  logger.info("Passed key policy checks.")  
  return create_compliance_evaluation(True,key_state,key_id,"")

def check_principals(allowed_principals, global_denied_principals, denied_principals, whitelisted_principals):
  logger.info(f"allowed principals {allowed_principals}, global denied principals {global_denied_principals} denied principals {denied_principals} whitelisted principals {whitelisted_principals}")
  found_principals=[]
  for allowed_principal in allowed_principals:
    #there was a Deny with NotPrincipal, this principal is not in that list, so it is effectively denied
    if global_denied_principals and allowed_principal not in global_denied_principals:
      logger.info(f"allowed_principal is effectively denied due to a Deny with NotPrincipal")
      continue
    #this principal is not explicitly denied and is not whitelisted
    if allowed_principal not in denied_principals and allowed_principal not in whitelisted_principals: 
      found_principals.append(allowed_principal)
  
  return found_principals

def create_compliance_evaluation(is_compliant,key_state,key_id,annotation):
  compliance_state="COMPLIANT" if is_compliant else "NON_COMPLIANT"

  if key_state == 'Enabled':
      return Evaluation(
         compliance_state,
         key_id,
         DEFAULT_RESOURCE_TYPE,
         annotation=f"{annotation}"         
      )
  else:
      return Evaluation(
         compliance_state,
         key_id,
         DEFAULT_RESOURCE_TYPE,
         annotation=f"{annotation} The KMS Key is in state {key_state}."
      )

def evaluate_key_policy(iam_client,statement):
    key_statement=copy.deepcopy(statement)
    #Should always be in the KMS Key Policy
    if 'Principal' in key_statement:
        del key_statement['Principal']
    #Optional to include
    if 'Condition' in key_statement:
        del key_statement['Condition']

    policy_json={}
    policy_json["Version"]="2012-10-17"
    policy_json['Statement']=list()
    policy_json['Statement'].append(key_statement)
    policy_str=json.dumps(policy_json)

    iam_evaluation_results=iam_client.simulate_custom_policy(
        PolicyInputList=[policy_str],
        ActionNames=[PERMISSION]
    )


    for iam_evaluation_result in iam_evaluation_results['EvaluationResults']:
        evaldecision=iam_evaluation_result['EvalDecision']
        evalactionname=iam_evaluation_result['EvalActionName']
        if PERMISSION == evalactionname:
            return evaldecision

    return "implicitDeny"

def convert_string_to_list(value):
    if isinstance(value, str):
        return [value]
    else:
        return value

 ################################
 # DO NOT MODIFY ANYTHING BELOW #
 ################################
def lambda_handler(event, context):
    my_rule = SCHEDULE_KEY_DELETION_ACCESS_RULE()
    evaluator = Evaluator(my_rule,APPLICABLE_RESOURCES)
    return evaluator.handle(event, context)
