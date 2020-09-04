
# How to automatically archive expected IAM Access Analyzer findings

## Prequisities

This code example utilizes the [AWS Cloud Development Kit](https://aws.amazon.com/cdk/).

This example also expects that AWS IAM Access Analyzer with the account analyzer is enabled in the target region. You can find the AWS CloudFormation template [in this repo here](https://github.com/aws-samples/aws-iam-permissions-guardrails/blob/master/access-analyzer/enablement/account-analyzer.yaml). If you wish to enable IAM Access Analyzer across your organization, there is a stack set creation script [in this repo here](https://github.com/aws-samples/aws-iam-permissions-guardrails/tree/master/access-analyzer/enablement) and there is a more detailed blost post [Enabling AWS IAM Access Analyzer on AWS Control Tower accounts](https://aws.amazon.com/blogs/mt/enabling-aws-identity-and-access-analyzer-on-aws-control-tower-accounts/).

## Deployment

```
cdk bootstrap

cdk deploy --parameters EmailSubscriptionParameter=jjjoy@amazon.com

```

