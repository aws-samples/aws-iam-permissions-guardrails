import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

import boto3

#Evaluate Risk Level
#Return True to raise alert if risk level exceeds threshold
#Return False to Archive finding
def should_raise_alert(finding_details, tags, additional_context):
  if (
      finding_details["isPublic"]
      and not is_allowed_public(finding_details, tags, additional_context)
     ):
    return True
  elif (
        "IsAllowedToShare" in tags and tags["IsAllowedToShare"]=="true"
        and "Environment" in tags and tags["Environment"]=="development"
        and "key_aliases" in additional_context and "alias/DevelopmentKey" in additional_context["key_aliases"]
    ):
    return False

  return True

def is_allowed_public(finding_details, tags, additional_context):
  #customize logic
  #for example, Data Classification is Confidential, return False
  if "Data Classification" in tags and tags["Data Classification"]=="Confidential":
    return False 

  return True

def handler(event,context):
  finding_details=event["detail"]
  tags=event["guid"]["tags"]
  additional_context=event["guid"]["additional_context"]
  if should_raise_alert(finding_details,tags,additional_context):
    return {"status":"NOTIFY"}
  else:
    return {"status":"ARCHIVE"}
