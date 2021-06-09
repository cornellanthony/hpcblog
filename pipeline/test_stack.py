from pipeline.pipeline_stack import PipelineStack
from aws_cdk import core, aws_batch as batch, aws_ecr as ecr, aws_ecs as ecs


class TestStack(core.Stack):
  def __init__(self, app: core.App, id: str, vpc, **kwargs):
    super().__init__(app, id, **kwargs)
    

    # default is managed
    my_compute_environment = batch.ComputeEnvironment(self, "AWS-Managed-Compute-Env",
        compute_resources={
            "vpc": vpc
        }
    )
    
    # Example automatically generated without compilation. See https://github.com/aws/jsii/issues/826
    test_queue = batch.JobQueue(self, "JobQueue", 
        compute_environments=[
               batch.JobQueueComputeEnvironment(
                   compute_environment = my_compute_environment,
                    order = 1
                )
            ]
    )

    # Example automatically generated without compilation. See https://github.com/aws/jsii/issues/82
    test_jobDef = batch.JobDefinition(self, "MyJobDef",
        job_definition_name="MyCDKJobDefinition",
        container=batch.JobDefinitionContainer(image=ecs.ContainerImage.from_registry("amazon/amazonlinux2"),command=["sleep", "900"],memory_limit_mib=1024, vcpus=256),
    ) 