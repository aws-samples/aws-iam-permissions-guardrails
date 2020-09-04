#!/usr/bin/env python3

from aws_cdk import core

from access_analyzer_example.access_analyzer_example_stack import AccessAnalyzerExampleStack

app = core.App()
AccessAnalyzerExampleStack(app, "access-analyzer-example")
app.synth()
