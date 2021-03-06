#!/usr/bin/env python3
from aws_cdk import core

from pipeline.pipeline_stack import PipelineStack
from pipeline.test_stack import TestStack
from pipeline.batch_stack import BatchStack
# from pipeline.launchstack import MyProjectStack
from pipeline.vpc_stack import VpcStack

CODECOMMIT_REPO_NAME = "pipeline"
STATE_MACHINE = "my_state_machine"
APPROVAL_EMAIL = ['telkarv@amazon.com', 'antcorne@amazon.com']

app = core.App()

# lambda_stack = LambdaStack(app, "LambdaStack")

# PipelineStack(app, "PipelineDeployingLambdaStack",
#     # lambda_code=lambda_stack.lambda_code,
#     repo_name=CODECOMMIT_REPO_NAME)
vpc_stack = VpcStack(app, "VpcStack")
pipeline_stack = PipelineStack(
    app, "PipelineCustomAMIStack", repo_name=CODECOMMIT_REPO_NAME, state_machine=STATE_MACHINE, approval_email=APPROVAL_EMAIL)
test_stack = TestStack(app, "TestStack", vpc=vpc_stack.vpc, state_machine=STATE_MACHINE)
batch_stack = BatchStack(app, "BatchStack", vpc=vpc_stack.vpc)
core.Tag.add(app, key="Project", value="Batch Custom AMI Resource")
# launch_stack = MyProjectStack(app, "MyProjectStack")

app.synth()
