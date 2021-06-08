#!/usr/bin/env python3

CODECOMMIT_REPO_NAME = "pipeline"

from aws_cdk import core

from pipeline.pipeline_stack import PipelineStack
from pipeline.lambda_stack import LambdaStack

app = core.App()

lambda_stack = LambdaStack(app, "LambdaStack")

PipelineStack(app, "PipelineDeployingLambdaStack",
    lambda_code=lambda_stack.lambda_code,
    repo_name=CODECOMMIT_REPO_NAME)

app.synth()