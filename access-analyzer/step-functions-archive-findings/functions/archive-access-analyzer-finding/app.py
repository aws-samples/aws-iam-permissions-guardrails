import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

import boto3

def archive_finding(finding_id, analyzer_arn):
  access_analyzer_client=boto3.client("accessanalyzer")
  access_analyzer_client.update_findings(
    analyzerArn=analyzer_arn,
    ids=[finding_id],
    status="ARCHIVED"
  ) 

def handler(event,context):
  finding_id=event["detail"]["id"]
  analyzer_arn=analyzer_arn=event["resources"][0]
  archive_finding(finding_id, analyzer_arn)

