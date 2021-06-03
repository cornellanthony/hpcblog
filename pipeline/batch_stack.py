from aws_cdk import core, aws_batch as batch, aws_ec2 as ec2, aws_ecr as ecr, aws_ecs as ecs


class BatchStack(core.Stack):
  def __init__(self, app: core.App, id: str, **kwargs):
    super().__init__(app, id, **kwargs)

    # Example automatically generated without compilation. See https://github.com/aws/jsii/issues/826
    myvpc = ec2.Vpc(self, "VPC")

    # Example automatically generated without compilation. See https://github.com/aws/jsii/issues/826
    # my_launch_template = ec2.CfnLaunchTemplate(self, "LaunchTemplate",
    #     launch_template_name="extra-storage-template",
    #     launch_template_data={
    #             "block_device_mappings": [{
    #                 "device_name": "/dev/xvdcz",
    #                 "ebs": {
    #                     "encrypted": True,
    #                     "volume_size": 10,
    #                     "volume_type": "gp2"
    #                 }
    #             }
    #             ]
    #         }
    #     )

    # default is managed
    my_compute_environment = batch.ComputeEnvironment(self, "AWS-Managed-Compute-Env",
        compute_resources={
            # "launch_template": {
            # "launch_template_name": my_launch_template.launch_template_name
            # },
            "vpc": myvpc
        }
    )

    # customer_managed_environment = batch.ComputeEnvironment(self, "Customer-Managed-Compute-Env",
    #     managed=False
    # )

    # Example automatically generated without compilation. See https://github.com/aws/jsii/issues/826
    test_queue = batch.JobQueue(self, "JobQueue", 
        compute_environments=[
               batch.JobQueueComputeEnvironment(
                   compute_environment = my_compute_environment,
                    order = 1
                )
            ]
    )
    # my_job_queue = batch.JobQueue(self, "JobQueue", compute_environments=[{"compute_environment": my_compute_environment, "order": 1 }], priority=1 )
    

    # Example automatically generated without compilation. See https://github.com/aws/jsii/issues/826
    repo = ecr.Repository.from_repository_name(self, "batch-job-repo", "todo-list")

    batch.JobDefinition(self, "batch-job-def-from-ecr",
        container={
            "image": ecs.EcrImage(repo, "latest")
        }
    )