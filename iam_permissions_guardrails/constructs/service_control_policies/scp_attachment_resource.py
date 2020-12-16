import os.path
dirname = os.path.dirname(__file__)

from aws_cdk import core, aws_iam as iam, aws_lambda as _lambda

from aws_cdk.core import CustomResource

import aws_cdk.custom_resources as cr



class ScpAttachmentResource(core.Construct):
    def __init__(
        self,
        scope: core.Construct,
        id: str,
        policy_id: str,
        account_targets: list[str] = None,
        organization_unit_targets: list[str] = None,
    ) -> None:
        super().__init__(scope, id)

        on_event = _lambda.Function(
            self,
            "ON-SCP-ATTACHMENT-EVENT",
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="app.on_event",
            timeout=core.Duration.seconds(600),
            memory_size=128,
            code=_lambda.Code.asset(os.path.join(dirname,"attachment_lambda")),
            description="Service control policy attachment resource",
        )

        on_event.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "organizations:CreatePolicy",
                    "organizations:DeletePolicy",
                    "organizations:AttachPolicy",
                    "organizations:DetachPolicy",
                ],
                resources=["*"],
            )
        )

        attachment_provider = cr.Provider(
            self,
            "ON_EVENT_CUSTOM_RESOURCE_PROVIDER",
            on_event_handler=on_event,
        )

        CustomResource(
            self,
            "scp-attachment-custom-resource",
            service_token=attachment_provider.service_token,
            properties={
                "PolicyId": policy_id,
                "AccountTargets": account_targets,
                "OrganizationUnitTargets": organization_unit_targets,
            },
        )

