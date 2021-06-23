# from pipeline.pipeline_stack import PipelineStack
# from aws_cdk import core, aws_batch as batch,
from aws_cdk import (
    aws_stepfunctions as _sfn,
    aws_batch as _batch,
    aws_stepfunctions_tasks as _sfn_tasks,
    aws_sns as sns,
    aws_ec2 as ec2,
    # aws_ecr as ecr,
    aws_ecs as ecs,
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
        my_launch_data = ec2.CfnLaunchTemplate.LaunchTemplateDataProperty(
            image_id=ImageId.value_as_string,
            user_data=core.Fn.base64(userdata))
        my_launch_template = ec2.CfnLaunchTemplate(self, "BatchLaunchTemplate", launch_template_name="batch-template",
                                                   launch_template_data=my_launch_data)
        # default is managed
        my_compute_environment = _batch.ComputeEnvironment(self, "AWS-Managed-Compute-Env",
                                                           compute_resources={
                                                               "launch_template": {"launch_template_name": my_launch_template.launch_template_name, "version": "$Latest"},
                                                               "vpc": vpc
                                                           },
                                                           compute_environment_name=TestEnv.value_as_string
                                                           )
        # Example automatically generated without compilation. See https://github.com/aws/jsii/issues/826
        test_queue = _batch.JobQueue(self, "JobQueue",
                                     compute_environments=[
                                         _batch.JobQueueComputeEnvironment(
                                             compute_environment=my_compute_environment,
                                             order=1
                                         )
                                     ]
                                     )
        # Example automatically generated without compilation. See https://github.com/aws/jsii/issues/82
        test_jobDef = _batch.JobDefinition(self, "MyJobDef",
                                           job_definition_name="MyCDKJobDef",
                                           container=_batch.JobDefinitionContainer(image=ecs.ContainerImage.from_registry(
                                               "public.ecr.aws/amazonlinux/amazonlinux:latest"), command=["sleep", "60"], memory_limit_mib=256, vcpus=2),
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
                                           message=_sfn.TaskInput.from_data_at(
                                               "$.message")
                                           )
        self.task2 = _sfn_tasks.SnsPublish(self, "Publish_failed",
                                           topic=topic,
                                           message=_sfn.TaskInput.from_data_at(
                                               "$.message")
                                           )
        self.statemachine = _sfn.StateMachine(
            self, "StateMachine",
            state_machine_name=state_machine,
            definition=self.task_job.next(self.task1),
            # catch_props={
            #     "ErrorEquals": [ "States.ALL" ],
            #     "Next": self.task2
            # },    

            timeout=core.Duration.hours(1),
        )
        # self.machinename = self.statemachine.state_machine_name
        # core.CfnOutput(self, "MyStepFunction", value=self.statemachine.state_machine_name,
        #                export_name="mysfunction")