import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

import os

import boto3

sns_topic_arn=os.environ["SNS_TOPIC_ARN"]

def handler(event,context):
  resource_type=event["detail"]["resourceType"]
  resource_arn=event["detail"]["resource"]

  sns_client=boto3.client('sns')
  sns_client.publish(
      TopicArn=sns_topic_arn,
      Message=f"Alert {resource_type} {resource_arn} exceeds risk level.",
      Subject="Alert Access Analyzer Finding"
  )
