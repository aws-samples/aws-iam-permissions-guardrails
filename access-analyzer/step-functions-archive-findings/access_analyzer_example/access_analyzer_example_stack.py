import os, subprocess

from aws_cdk import (
  core,
  aws_accessanalyzer as accessanalyzer,
  aws_iam as iam,
  aws_events,
  aws_events_targets,
  aws_lambda,
  aws_stepfunctions as sfn,
  aws_stepfunctions_tasks as sfn_tasks,
  aws_sns as sns,
  aws_sns_subscriptions as subscriptions,
  aws_kms as kms
)
                   


class AccessAnalyzerExampleStack(core.Stack):

  def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
    super().__init__(scope, id, **kwargs)

    email_subscription_parameter=core.CfnParameter(self,
      "EmailSubscriptionParameter",
      description="Email Address for Notification Subscription",
      allowed_pattern='^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$',
      min_length=1,
      constraint_description="Must be a valid email."
    )
    email_subscription=email_subscription_parameter.value_as_string

    """
    ar1=accessanalyzer.CfnAnalyzer.ArchiveRuleProperty(
      rule_name="test",
      filter=[accessanalyzer.CfnAnalyzer.FilterProperty(property="principal.AWS",eq=["123456789123"])]
    )
    analyzer=accessanalyzer.CfnAnalyzer(
      self,
      id="accessanalyzer",
      type="ACCOUNT",
      tags=[core.CfnTag(key="AccessAnalyzerType",value="ACCOUNT")],
      archive_rules=[ar1]
    )
    """

    runtime=aws_lambda.Runtime.PYTHON_3_8

    boto3_lambda_layer = self.create_dependencies_layer(
        id="boto3layer", requirements_path="./layers/boto3/requirements.txt", output_dir="./layers/boto3"
    )

    """
    boto3_lambda_layer=aws_lambda.LayerVersion(
      self,
      "Boto3LambdaLayer",
      code=aws_lambda.AssetCode("./layers/boto3"),
      compatible_runtimes=[runtime],
      description="Boto3 Lambda Layer"
    )
    """

    context_enrichment=aws_lambda.Function(
      self,
      "context_enrichment",
      runtime=runtime,
      handler="app.handler",
      code=aws_lambda.AssetCode("./functions/context-enrichment"),
      layers=[boto3_lambda_layer]
    )
    handler_statement = iam.PolicyStatement(
      actions=[
        "iam:ListRoleTags",
        "s3:GetBucketTagging",
        "lambda:ListTags",
        "sqs:ListQueueTags",
        "kms:ListAliases",
        "kms:ListResourceTags"
      ],
      effect=iam.Effect.ALLOW,
      resources=["*"]
    )
    context_enrichment.add_to_role_policy(handler_statement)

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

    notification=aws_lambda.Function(
      self,
      "notification",
      runtime=runtime,
      handler="app.handler",
      code=aws_lambda.AssetCode("./functions/notification"),
      layers=[boto3_lambda_layer],
      environment={"SNS_TOPIC_ARN":email_topic.topic_arn}
    )
    notification_statement=iam.PolicyStatement(
      actions=[
        "sns:Publish",
      ],
      effect=iam.Effect.ALLOW,
      resources=["*"]
    )
    notification.add_to_role_policy(notification_statement)
    cmk_key.grant_encrypt_decrypt(notification)

    archive_access_analyzer_finding=aws_lambda.Function(
      self,
      "archive-access-analyzer-finding",
      runtime=runtime,
      handler="app.handler",
      code=aws_lambda.AssetCode("./functions/archive-access-analyzer-finding"),
      layers=[boto3_lambda_layer]
    )
    archive_statement=iam.PolicyStatement(
      actions=[
        "access-analyzer:UpdateFindings",
      ],
      effect=iam.Effect.ALLOW,
      resources=["*"]
    )
    archive_access_analyzer_finding.add_to_role_policy(archive_statement)

    evaluate_access_analyzer_finding=aws_lambda.Function(
      self,
      "evaluate-access-analyzer-finding",
      runtime=runtime,
      handler="app.handler",
      code=aws_lambda.AssetCode("./functions/evaluate-access-analyzer-finding"),
      layers=[boto3_lambda_layer]
    )

    #https://docs.aws.amazon.com/cdk/api/latest/docs/aws-stepfunctions-readme.html
    access_analyzer_handler_task=sfn.Task(
      self,
      "Context Enrichment",
      task=sfn_tasks.InvokeFunction(context_enrichment),
      result_path="$.guid",
    )

    notification_task=sfn.Task(
      self,
      "Send Notification",
      task=sfn_tasks.InvokeFunction(notification),
      result_path="$.guid",
    )
   
    archive_task=sfn.Task(
      self,
      "Archive Finding",
      task=sfn_tasks.InvokeFunction(archive_access_analyzer_finding),
      result_path="$.guid",
    )

    evaluate_task=sfn.Task(
      self,
      "Evaluate Risk Level",
      task=sfn_tasks.InvokeFunction(evaluate_access_analyzer_finding),
      result_path="$.guid",
    ) 

    definition=access_analyzer_handler_task. \
      next(evaluate_task). \
      next(sfn.Choice(self, "Archive?"). \
        when(sfn.Condition.string_equals("$.guid.status", "ARCHIVE"), archive_task). \
        when(sfn.Condition.string_equals("$.guid.status", "NOTIFY"), notification_task) \
      )            

    state_machine=sfn.StateMachine(
      self,
      "Access-Analyzer-Automatic-Finding-Archive-State-Machine",
      definition=definition,
      timeout=core.Duration.minutes(5),
    )


    #https://docs.aws.amazon.com/step-functions/latest/dg/tutorial-cloudwatch-events-s3.html
    access_analyzer_finding_rule=aws_events.Rule(
      self,
      "AccessAnalzyerFindingActiveEventRule",
      description="Access Analyzer Finding Event Active",
      enabled=True,
      event_pattern=aws_events.EventPattern(
        source=["aws.access-analyzer"],
        detail_type=["Access Analyzer Finding"],
        detail={"status":["ACTIVE"]}
      ),
      targets=[
        aws_events_targets.SfnStateMachine(state_machine),
        aws_events_targets.LambdaFunction(context_enrichment)
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
