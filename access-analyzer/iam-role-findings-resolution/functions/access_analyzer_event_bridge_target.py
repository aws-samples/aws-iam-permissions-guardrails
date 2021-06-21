import boto3
import json
import logging
import os
from arnparse import arnparse

logger = logging.getLogger()
logger.setLevel(logging.INFO)

iam = boto3.client('iam')


def disable_iam_access(resource_name, ext_arn, finding_id):
    try:
        ext_arn = ext_arn.strip()
        policy = {
            "Sid": finding_id,
            "Effect": "Deny",
            "Principal": {
                "AWS": ext_arn},
            "Action": "sts:AssumeRole"
        }
        response = iam.get_role(RoleName=resource_name)
        current_policy = response['Role']['AssumeRolePolicyDocument']
        current_policy = current_policy['Statement'].append(policy)
        new_policy = json.dumps(response['Role']['AssumeRolePolicyDocument'])
        logger.debug(new_policy)
        response = iam.update_assume_role_policy(
            PolicyDocument=new_policy,
            RoleName=resource_name)
        logger.info(response)
    except Exception as e:
        logger.error(e)
        logger.error('Unable to update IAM Policy')


def send_notifications(sns_topic, principal, resource_arn, finding_id, resource_name, region):
    sns_client = boto3.client("sns")
    console_deep_link = "https://console.aws.amazon.com/iam/home?region={}#/roles/{}".format(
        region, resource_name)
    message = "The IAM Role resource {} ({}) allows access to the principal {}. Trust policy for the role has been updated to deny the external access. Please review the IAM Role and its trust policy. If this access is intended, update the IAM Role trust policy to remove a statement with SID matching with the finding id {} and mark the finding as archived or create an archive rule. If this access is not intended then delete the IAM Role.".format(
        resource_arn, console_deep_link, principal, finding_id)

    subject = "Access Analyzer finding {} was automatically resolved".format(
        finding_id)
    sns_response = sns_client.publish(
        TopicArn=sns_topic,
        Message=message,
        Subject=subject
    )
    logger.debug(sns_response)


def lambda_handler(event, context):
    logger.info("event: {}".format(event))
    sns_topic = os.environ["SNS_TOPIC_ARN"]
    analyzer_arn = event['resources'][0]
    external_principal = event['detail']['principal']['AWS']
    logger.info("External Principal:{}".format(external_principal))
    finding_id = event['detail']['id'].replace("-", "")
    resource_arn = event['detail']['resource']
    resource_name = resource_arn.split("/")[1]
    resource_type = event['detail']['resourceType']
    arn = arnparse(analyzer_arn)
    if external_principal:
        if "arn:{}".format(arn.partition) in external_principal:
            ext_arn = external_principal
        else:
            ext_arn = "arn:{}:iam::{}:root".format(
                arn.partition, external_principal)
        logger.debug(ext_arn)
        if resource_type == 'AWS::IAM::Role':
            logger.debug("Deny access in the trust policy")
            disable_iam_access(resource_name, ext_arn, finding_id)
            logger.debug("send message")
            send_notifications(
                sns_topic, external_principal, resource_arn, finding_id, resource_name, arn.region)
