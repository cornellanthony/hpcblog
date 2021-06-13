from pipeline.pipeline_stack import PipelineStack
from aws_cdk import core, aws_batch as batch, aws_ecr as ecr, aws_ecs as ecs
from aws_cdk import (
    aws_stepfunctions as _sfn,
    aws_batch as _batch,
    aws_stepfunctions_tasks as _sfn_tasks,
    aws_sns as sns,
    aws_ec2 as ec2,
    core,
)

class TestStack(core.Stack):
  def __init__(self, app: core.App, id: str, vpc, **kwargs):
    super().__init__(app, id, **kwargs)
    
    #Parameters
    ImageId = core.CfnParameter(self, "AMIID", type="String", 
                          description="This is Custom AMI ID")

    Environment = core.CfnParameter(self, "MyEnvironment", type="String", 
                          description="This is Custom AMI ID")

    VersionTag = core.CfnParameter(self, "VersionTag", type="String", 
                          description="This is Custom AMI ID")

    with open ("packer/user_data.txt", "r") as myfile:
            userdata=myfile.read()

    my_custom_ami=ec2.MachineImage.generic_linux({"us-east-2":ImageId.value_as_string})
    my_launch_template = ec2.CfnLaunchTemplate(self, "BatchLaunchTemplate", launch_template_name="batch-template",
                                               launch_template_data={
                                                   "image_id": my_custom_ami,
                                                   "user_data": ec2.UserData.custom(userdata)
                                               })
    # my_launch_template = ec2.LaunchTemplate(self, "MyLaunchTemplate", user_data=ec2.UserData.custom(userdata), machine_image=my_custom_ami)
    print(my_launch_template.launch_template_name)
    # default is managed
    my_compute_environment = batch.ComputeEnvironment(self, "AWS-Managed-Compute-Env",
        compute_resources={
            # "lauch_template": { "lauch_template"}
            # "launch_template": { "launch_template_id" : my_launch_template.launch_template_id },
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
        job_definition_name="MyCDKJobDef",
        container=batch.JobDefinitionContainer(image=ecs.ContainerImage.from_registry("amazon/amazonlinux2"),command=["sleep", "900"],memory_limit_mib=1024, vcpus=256),
    ) 
    self.task_job = _sfn_tasks.BatchSubmitJob(self, "Submit Job",
        job_definition_arn=test_jobDef.job_definition_arn,
        job_name="MyJob",
        job_queue_arn=test_queue.job_queue_arn
    )
    
    # self.Job_String_Split = _sfn.Task(
    #         self,"String_Split",
    #         # input_path = "$.TaskInfo",
    #         # result_path = "$.JobDetail.String_Split",
    #         # output_path = "$",
    #         task = _sfn_tasks.RunBatchJob(
    #             job_name = "String_Split",
    #             job_definition = test_jobDef,
    #             job_queue = test_queue,
    #         )
    #     )
    topic = sns.Topic(self, "Topic")
    self.task1 = _sfn_tasks.SnsPublish(self, "Publish_suceeded",
            topic=topic,
            message=_sfn.TaskInput.from_data_at("$.message")
        )

    self.task2 = _sfn_tasks.SnsPublish(self, "Publish_failed",
            topic=topic,
            message=_sfn.TaskInput.from_data_at("$.message")
        )

    self.statemachine = _sfn.StateMachine(
            self, "StateMachine",
            definition = self.task_job.next(self.task1),
        # catch_props={
        #     "ErrorEquals": [ "States.ALL" ],
        #     "Next": self.task2
        # },
              
            timeout = core.Duration.hours(1),
        ) 