#!/usr/bin/env python3
from aws_cdk import core

from pipeline.pipeline_stack import PipelineStack
from pipeline.test_stack import TestStack
from pipeline.batch_stack import BatchStack

CODECOMMIT_REPO_NAME = "pipeline"
app = core.App()

# lambda_stack = LambdaStack(app, "LambdaStack")

# PipelineStack(app, "PipelineDeployingLambdaStack",
#     # lambda_code=lambda_stack.lambda_code,
#     repo_name=CODECOMMIT_REPO_NAME)

pipeline_stack = PipelineStack(
    app, "PipelineCustomAMIStack", repo_name=CODECOMMIT_REPO_NAME)

test_stack = TestStack(app, "TestStack", vpc=pipeline_stack.vpc)
batch_stack = BatchStack(app, "BatchStack", vpc=pipeline_stack.vpc)
core.Tag.add(app, key="Project", value="Batch Custom AMI Resource")

app.synth()
