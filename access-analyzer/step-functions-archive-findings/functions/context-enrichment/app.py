import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

from collections import ChainMap
import boto3

def lookup_s3_tags(resource_arn):
  s3_client = boto3.client("s3")
  bucket_tags = s3_client.get_bucket_tagging(Bucket=resource_arn)["TagSet"]

  for tags in bucket_tags:
    tags[tags.pop("Key")]=tags.pop("Value")

  return dict(ChainMap(*tags))

def lookup_kms_tags(resource_arn):
  kms_client = boto3.client("kms")
  kms_tags=kms_client.list_resource_tags(KeyId=resource_arn)["Tags"] 

  for tags in kms_tags:
    tags[tags.pop("TagKey")]=tags.pop("TagValue")

  return dict(ChainMap(*kms_tags))
 
def lookup_tags(resource_type,resource_arn):
  if resource_type=="AWS::KMS::Key": 
    return lookup_kms_tags(resource_arn)
  elif resource_type=="AWS::S3::Bucket":
    return lookup_s3_tags(resource_arn)
  else:
    logger.info(f"{resource_type} needs to be added to lookup tags")
    return {}

def additional_enrichment(resource_type, resource_arn):
  additional_context = {}

  if resource_type == "AWS::KMS::Key":
    kms_client = boto3.client("kms")
    aliases = kms_client.list_aliases(KeyId=resource_arn)["Aliases"]
    additional_context["key_aliases"] = [alias["AliasName"] for alias in aliases]

  return additional_context

def handler(event,context):
  analyzer_arn=event["resources"][0]

  detail=event["detail"]
  finding_id=detail["id"]
  resource_type=detail["resourceType"]
  resource_arn=detail["resource"]
  is_public=detail["isPublic"]
  actions=detail["action"]
  condition=detail["condition"]
  principal=detail["principal"]

  #logger.info(f"finding id={finding_id} analyzer arn={analyzer_arn} is public={is_public} resource type={resource_type} principal={principal} actions={actions} condition={condition}")

  tags=lookup_tags(resource_type,resource_arn) 
  additional_context=additional_enrichment(resource_type,resource_arn)
  
  results={"tags":tags,"additional_context":additional_context}
  return results 
