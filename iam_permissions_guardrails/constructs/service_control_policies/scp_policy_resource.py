from aws_cdk import core, aws_iam as iam, aws_lambda as _lambda

from aws_cdk.core import CustomResource

import aws_cdk.aws_logs as logs

import aws_cdk.custom_resources as cr

import uuid
import json


class ScpPolicyResource(core.Construct):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        service_control_policy_string: str,
        description: str,
        name: str,
    ) -> None:
        super().__init__(scope, id)

        POLICY_ID_LOOKUP = "Policy.PolicySummary.Id"

        self.service_control_policy_string = service_control_policy_string
        
        # https://docs.aws.amazon.com/AWSJavaScriptSDK/latest/AWS/Organizations.html
        # https://docs.aws.amazon.com/cdk/api/latest/docs/custom-resources-readme.html#physical-resource-id-parameter
        on_create_policy = cr.AwsSdkCall(
            action="createPolicy",
            service="Organizations",
            physical_resource_id=cr.PhysicalResourceId.from_response(POLICY_ID_LOOKUP),
            parameters={
                "Content": service_control_policy_string,
                "Description": description,
                "Name": name,
                "Type": "SERVICE_CONTROL_POLICY",
            },
            output_path=POLICY_ID_LOOKUP,
        )

        on_update_policy = cr.AwsSdkCall(
            action="updatePolicy",
            service="Organizations",
            physical_resource_id=cr.PhysicalResourceId.from_response(POLICY_ID_LOOKUP),
            parameters={
                "Content": service_control_policy_string,
                "Description": description,
                "Name": name,
                "PolicyId": cr.PhysicalResourceIdReference(),
            },
            output_path=POLICY_ID_LOOKUP,
        )

        on_delete_policy = cr.AwsSdkCall(
            action="deletePolicy",
            service="Organizations",
            parameters={
                "PolicyId": cr.PhysicalResourceIdReference(),
            },
        )

        policy = cr.AwsCustomResourcePolicy.from_sdk_calls(
            resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE
        )
        scp_create = cr.AwsCustomResource(
            self,
            "ServiceControlPolicyCreate",
            install_latest_aws_sdk=True,
            policy=policy,
            on_create=on_create_policy,
            on_update=on_update_policy,
            on_delete=on_delete_policy,
            resource_type="Custom::ServiceControlPolicy",
        )

        self.policy_id = scp_create.get_response_field(POLICY_ID_LOOKUP)

