# from pipeline.pipeline_stack import PipelineStack
from aws_cdk import core, aws_batch as _batch, aws_ec2 as _ec2


class BatchStack(core.Stack):
    def __init__(self, app: core.App, id: str, vpc, **kwargs):
        super().__init__(app, id, **kwargs)
        # Parameters
        ImageId = core.CfnParameter(self, "ImageId", type="String",
                                    description="This is Custom AMI ID")
        MainEnv = core.CfnParameter(self, "MainEnv", type="String",
                                    description="Batch Compute Environment name")
        # Read userdata script in a file.
        with open("packer/user_data.txt", "r") as myfile:
            userdata = myfile.read()
        # Create launch template data using image id and userdata script.
        my_launch_data = _ec2.CfnLaunchTemplate.LaunchTemplateDataProperty(
            image_id=ImageId.value_as_string,
            user_data=core.Fn.base64(userdata))
        my_launch_template = _ec2.CfnLaunchTemplate(self, "BatchLaunchTemplate",
                                                    launch_template_name="batch-main-template",
                                                    launch_template_data=my_launch_data)
        # default is managed
        my_compute_environment = _batch.ComputeEnvironment(self, "AWS-Managed-Compute-Env",
                                                           compute_resources={
                                                               "launch_template": {"launch_template_name": my_launch_template.launch_template_name, "version": "$Latest"},
                                                               "vpc": vpc
                                                           },
                                                           compute_environment_name=MainEnv.value_as_string
                                                           )
        # Example automatically generated without compilation. See https://github.com/aws/jsii/issues/826
        self.batch_queue = _batch.JobQueue(self, "JobQueue",
                                           compute_environments=[
                                               _batch.JobQueueComputeEnvironment(
                                                   compute_environment=my_compute_environment,
                                                   order=1
                                               )
                                           ])
