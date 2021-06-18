
import os, subprocess

from aws_cdk import (
  core,
  aws_accessanalyzer as accessanalyzer,
  aws_iam as iam,
  aws_events,
  aws_events_targets,
  aws_lambda,
  aws_sns as sns,
  aws_sns_subscriptions as subscriptions,
  aws_kms as kms
)


class IamAccessAnalyzerFindingsRemediationStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here
        email_subscription_parameter=core.CfnParameter(self,
            "NotificationEmail",
            description="Email Address for Notification",
            type="String"
            )
        email_subscription=email_subscription_parameter.value_as_string

        boto3_lambda_layer=None
        boto3_lambda_layer = self.create_dependencies_layer(
            id="boto3layer", requirements_path="./layers/boto3/requirements.txt", output_dir="./layers/boto3"
        )

        cmk_key=kms.Key(
            self,
            "SNSEncryptionAtRestKey",
            description="SNS Encryption at rest key",
            alias="sns-encryption-at-rest",
            enable_key_rotation=True,
        )

        email_topic=sns.Topic(
        self,
        "AccessAnalyzerNotificationTopic",
        display_name="Access Analyzer Finding Notification Topic",
        master_key=cmk_key
        )
        email_topic.add_subscription(subscriptions.EmailSubscription(email_subscription))
        
        access_analyzer_event_bridge_event_handler=aws_lambda.Function(
            self,
            "access_analyzer_event_bridge_event_handler",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            handler="access_analyzer_event_bridge_target.lambda_handler",
            code=aws_lambda.AssetCode("./functions/"),
            environment={'SNS_TOPIC_ARN' : email_topic.topic_arn},
            layers=[boto3_lambda_layer]
        )      

        handler_statement = iam.PolicyStatement(
        actions=[
            "iam:GetRole",
            "iam:UpdateAssumeRolePolicy"
        ],
        effect=iam.Effect.ALLOW,
        resources=["arn:aws:iam::{}:role/*".format(core.Stack.of(self).account)]
        )
        access_analyzer_event_bridge_event_handler.add_to_role_policy(handler_statement)
       
        notification_statement=iam.PolicyStatement(
        actions=[
            "sns:Publish",
        ],
        effect=iam.Effect.ALLOW,
        resources=[email_topic.topic_arn]
        )

        access_analyzer_event_bridge_event_handler.add_to_role_policy(notification_statement)
        cmk_key.grant_encrypt_decrypt(access_analyzer_event_bridge_event_handler)

        access_analyzer_finding_rule=aws_events.Rule(
        self,
        "AccessAnalzyerFindingActiveEventRule",
        description="Access Analyzer Finding Event Active",
        enabled=True,
        event_pattern=aws_events.EventPattern(
            source=["aws.access-analyzer"],
            detail_type=["Access Analyzer Finding"],
            detail={"status":["ACTIVE"], "resourceType": [ "AWS::IAM:Role" ]  }
        ),
        targets=[
            aws_events_targets.LambdaFunction(access_analyzer_event_bridge_event_handler)
        ]
        )

    #https://github.com/aws-samples/aws-cdk-examples/issues/130
    def create_dependencies_layer(
        self, id: str, requirements_path: str, output_dir: str
    ) -> aws_lambda.LayerVersion:
        # Install requirements for layer
        if not os.environ.get("SKIP_PIP"):
            subprocess.check_call(
                # Note: Pip will create the output dir if it does not exist
                f"pip install -r {requirements_path} -t {output_dir}/python".split()
            )
        return aws_lambda.LayerVersion(
            self, id, code=aws_lambda.Code.from_asset(output_dir)
        )