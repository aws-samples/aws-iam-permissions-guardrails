# Copyright 2017-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may
# not use this file except in compliance with the License. A copy of the License is located at
#
#        http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for
# the specific language governing permissions and limitations under the License.
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

PERMISSION = 'kms:ScheduleKeyDeletion'

class SCHEDULE_KEY_DELETION_ACCESS_RULE(ConfigRule):
    def evaluate_change(self, event, client_factory, configuration_item, valid_rule_parameters):
        kms_client = client_factory.build_client('kms')
        iam_client = client_factory.build_client('iam')
        evaluations = []
        whitelisted_principles = valid_rule_parameters['WhitelistedPrincipalArns']
        
        logger.info(f"event is {json.dumps(event)}")
        invoking_event=json.loads(event['invokingEvent'])
        logger.info(f"invokingEvent is {json.dumps(invoking_event)}")
        configuration_item=invoking_event['configurationItem']
        configuration=configuration_item['configuration']
        key_id=configuration['keyId']
        key_arn=configuration['arn'] 
        key_state=configuration['keyState']
        key_policy=json.loads(configuration_item["supplementaryConfiguration"]['Policy'])['Statement']
        logger.info(f"key policy is {json.dumps(key_policy)}")

        evaluation=evaluate_key(iam_client,key_state,key_policy,key_id,whitelisted_principles)
        return[evaluation]        

    def evaluate_periodic(self, event, client_factory, valid_rule_parameters):
        kms_client = client_factory.build_client('kms')
        iam_client = client_factory.build_client('iam')
        evaluations = []
        whitelisted_principles = valid_rule_parameters['WhitelistedPrincipalArns']
        all_kms_key_list = get_all_kms_keys(kms_client)

        if not all_kms_key_list:
            return [Evaluation(ComplianceType.NOT_APPLICABLE)]

        for key_id in all_kms_key_list:
            kms_key_details = kms_client.describe_key(KeyId=key_id)

            key_state = kms_key_details['KeyMetadata']['KeyState']
            get_key_policy = kms_client.get_key_policy(KeyId=key_id, PolicyName='default')
            key_policy = json.loads(get_key_policy['Policy'])['Statement']
            evaluation=evaluate_key(iam_client,key_state,key_policy,key_id,whitelisted_principles)
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
            if not all(key in ['WhitelistedPrincipalArns', 'ExecutionRoleName']  for key in rule_parameters.keys()):
                raise ValueError('WhitelistedPrincipalArns not in rule parameters.')

            arn_list = []
            regex_pattern = re.compile("^arn:[a-zA-Z-]+:iam::[0-9]+:.+$")
            for arn in rule_parameters['WhitelistedPrincipalArns']:
                if not regex_pattern.match(arn):
                    raise ValueError('The KMS whitelisted Principle Arns should be '
                        'in the right format.')
                if re.compile(':group/').match(arn):
                    raise ValueError('The KMS whitelisted Principle Arns should be '
                        'users or roles, not group.')
                arn_list.append(arn.replace(" ",""))
            rule_parameters['WhitelistedPrincipalArns'] = arn_list
        else:
            rule_parameters['WhitelistedPrincipalArns'] = []

        return rule_parameters

def get_all_kms_keys(kms_client):
    all_kms_key_list = []
    paginator=kms_client.get_paginator('list_keys')
    for page in paginator.paginate(PaginationConfig={'PageSize': 50}):
        for key in page['Keys']:
            all_kms_key_list.append(key['KeyId'])
    return all_kms_key_list

def evaluate_key(iam_client,key_state,key_policy,key_id,whitelisted_principles):
  denied_principles = []
  allowed_principles = []

  for statement in key_policy:
      evaluationresult=evaluate_key_policy(iam_client,statement)
      if "explicitDeny" == evaluationresult:
          if "AWS" in statement['Principal']:
              principles = convert_string_to_list(
                  statement['Principal']['AWS'])
              denied_principles.extend(principles)
          denied_principles = list(set(denied_principles))
      elif "allowed" == evaluationresult:
          if "AWS" in statement['Principal']:
              principles = convert_string_to_list(
                  statement['Principal']['AWS'])
              allowed_principles.extend(principles)
          allowed_principles = list(set(allowed_principles))

  for allowed_principle in allowed_principles:
      if any(re.compile(principle).match(allowed_principle)
             for principle
             in (denied_principles + whitelisted_principles)):
          allowed_principles.remove(allowed_principle)

  if key_state == 'Enabled':
      return Evaluation(
         compliant_state(len(allowed_principles)),
         key_id,
         DEFAULT_RESOURCE_TYPE
      )
  else:
      return Evaluation(
         compliant_state(len(allowed_principles)),
         key_id,
         DEFAULT_RESOURCE_TYPE,
         annotation="The KMS Key is in state {}.".format(key_state)
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

def compliant_state(length):
    if length > 0:
        return 'NON_COMPLIANT'
    else:
        return 'COMPLIANT'

 ################################
 # DO NOT MODIFY ANYTHING BELOW #
 ################################
def lambda_handler(event, context):
    my_rule = SCHEDULE_KEY_DELETION_ACCESS_RULE()
    evaluator = Evaluator(my_rule)
    return evaluator.handle(event, context)
