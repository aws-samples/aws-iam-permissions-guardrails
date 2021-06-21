#!/usr/bin/env python3

from aws_cdk import core

from iam_access_analyzer_findings_remediation.iam_access_analyzer_findings_remediation_stack import IamAccessAnalyzerFindingsRemediationStack


app = core.App()
IamAccessAnalyzerFindingsRemediationStack(app, "iam-access-analyzer-findings-remediation")

app.synth()
