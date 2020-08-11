#!/usr/bin/env python3

from aws_cdk import core

from access_analyzer_example.access_analyzer_example_stack import AccessAnalyzerExampleStack
from test_resources.test_resources_stack import TestResourcesStack

app = core.App()
AccessAnalyzerExampleStack(app, "access-analyzer-example")
TestResourcesStack(app, "test-resources")
app.synth()
