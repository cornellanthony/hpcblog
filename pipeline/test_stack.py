# from pipeline.pipeline_stack import PipelineStack
# from aws_cdk import core, aws_batch as batch,
from aws_cdk import (
    aws_stepfunctions as _sfn,
    aws_batch as _batch,
    aws_stepfunctions_tasks as _sfn_tasks,
    aws_sns as _sns,
    aws_ec2 as _ec2,
    # aws_ecr as ecr,
    aws_ecs as _ecs,
    core
)


class TestStack(core.Stack):
    def __init__(self, app: core.App, id: str, vpc, state_machine: str = None, **kwargs):
        super().__init__(app, id, **kwargs)

        # Parameters
        ImageId = core.CfnParameter(self, "ImageId", type="String",
                                    description="This is Custom AMI ID")
        TestEnv = core.CfnParameter(self, "TestEnv", type="String",
                                    description="Batch Compute Environment name")
        # Read UserData in file.
        with open("packer/user_data.txt", "r") as myfile:
            userdata = myfile.read()
        # Create Launch template data using AMI ID and userdata script.
        my_launch_data = _ec2.CfnLaunchTemplate.LaunchTemplateDataProperty(
            image_id=ImageId.value_as_string,
            user_data=core.Fn.base64(userdata))
        my_launch_template = _ec2.CfnLaunchTemplate(self, "BatchLaunchTemplate", launch_template_name="batch-template",
                                                   launch_template_data=my_launch_data)
        # Create Batch ComputeEnvironment using latest AMI version in Launch Template. 
        my_compute_environment = _batch.ComputeEnvironment(self, "AWS-Managed-Compute-Env",
                                                           compute_resources={
                                                               "launch_template": {"launch_template_name": my_launch_template.launch_template_name, "version": "$Latest"},
                                                               "vpc": vpc
                                                           },
                                                           compute_environment_name=TestEnv.value_as_string
                                                           )
        # Create AWS Batch JobQueue and associate it with Test Compute Environment. 
        test_queue = _batch.JobQueue(self, "JobQueue",
                                     compute_environments=[
                                         _batch.JobQueueComputeEnvironment(
                                             compute_environment=my_compute_environment,
                                             order=1
                                         )
                                     ]
                                     )
        # Create Job Definition to submit job in test job queue. 
        test_jobDef = _batch.JobDefinition(self, "MyJobDef",
                                           job_definition_name="MyCDKJobDef",
                                           container=_batch.JobDefinitionContainer(image=_ecs.ContainerImage.from_registry(
                                               "public.ecr.aws/amazonlinux/amazonlinux:latest"), command=["sleep", "60"], memory_limit_mib=256, vcpus=2),
                                           )
        # Create Stepfunction submit job task.
        self.task_job = _sfn_tasks.BatchSubmitJob(self, "Submit Job",
                                                  job_definition_arn=test_jobDef.job_definition_arn,
                                                  job_name="MyJob",
                                                  job_queue_arn=test_queue.job_queue_arn
                                                  )

        topic = _sns.Topic(self, "Topic")
        self.task1 = _sfn_tasks.SnsPublish(self, "Publish_suceeded",
                                           topic=topic,
                                           message=_sfn.TaskInput.from_data_at(
                                               "$.StatusReason")
                                           )
        self.task2 = _sfn_tasks.SnsPublish(self, "Publish_failed",
                                           topic=topic,
                                           message=_sfn.TaskInput.from_data_at(
                                               "$.StatusReason")
                                           )
        definition = self.task_job.next(_sfn.Choice(self, "Job Complete?").when(_sfn.Condition.string_equals("$.Status", "FAILED"), self.task2).when(_sfn.Condition.string_equals("$.Status", "SUCCEEDED"), self.task1))
        self.statemachine = _sfn.StateMachine(
            self, "StateMachine",
            state_machine_name=state_machine,
            definition=definition,
            # catch_props={
            #     "ErrorEquals": [ "States.ALL" ],
            #     "Next": self.task2
            # },

            timeout=core.Duration.hours(1),
        )