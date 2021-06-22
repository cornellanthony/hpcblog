from aws_cdk import (core, aws_codebuild as codebuild,
                     aws_codecommit as codecommit,
                     aws_codepipeline as codepipeline,
                     aws_codepipeline_actions as codepipeline_actions,
                     aws_stepfunctions as _sfn,
                     aws_ec2 as ec2, 
                     aws_lambda as lambda_,
                     aws_iam as _iam)
import json

from aws_cdk.aws_servicediscovery import NamespaceType


class PipelineStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, *, repo_name: str = None, state_machine: str = None, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Example automatically generated without compilation. See https://github.com/aws/jsii/issues/826
        # vpc = ec2.Vpc(self, "VPC")
        # self.vpc = vpc
        # myprivate_subnet = vpc.select_subnets(subnet_type=ec2.SubnetType.PRIVATE)
        # print(myprivate_subnet.subnet_ids[0])
        # core.CfnOutput(self, "MyBatchVPC", value=vpc.vpc_id,
        #                export_name="mybatchamivpc")

        code = codecommit.Repository.from_repository_name(self, "ImportedRepo",
                                                          repo_name)

        my_statemc_arn = "arn:aws:states:*:*:stateMachine:" + state_machine
        print(my_statemc_arn)
        my_statemachine = _sfn.StateMachine.from_state_machine_arn(self, "MyStateMachine", state_machine_arn = my_statemc_arn)
        # Read CodeBuild buildspec.yaml file.
        with open("packer/buildspec.yml", "r") as myfile:
            build_spec = myfile.read()

        # Policy Document.
        with open("packer/policy_doc.json", "r") as policydoc:
            packer_policy = policydoc.read()

        # Convert policy into dictonary format.
        codebuild_packer_policy = json.loads(packer_policy)
        codebuild_policy_doc = _iam.PolicyDocument.from_json(
            codebuild_packer_policy)

        codebuild_managed_policy = _iam.ManagedPolicy(
            self, "CodeBuildManagedPolicy", document=codebuild_policy_doc, managed_policy_name="CodeBuildPolicy")
        # Instance for packer tool
        instance_role = _iam.Role(self, "PackerInstanceRole",
                                  assumed_by=_iam.ServicePrincipal(
                                      "ec2.amazonaws.com"),
                                  managed_policies=[_iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3ReadOnlyAccess")])

        # Create Instance Profile
        instance_profile = _iam.CfnInstanceProfile(self, "MyInstanceProfile", roles=[
                                                   instance_role.role_name], instance_profile_name="BatchInstanceProfile")
        # CodeBuild Role with packer policy.
        codebuild_role = _iam.Role(self, "CodeBuildRole",
                                   assumed_by=_iam.ServicePrincipal(
                                       "codebuild.amazonaws.com"),
                                   managed_policies=[_iam.ManagedPolicy.from_aws_managed_policy_name("AWSCodeBuildAdminAccess"),
                                                     #   _iam.ManagedPolicy.from_managed_policy_name(self, "ManagedPolicyCodeBuild", managed_policy_name="CodeBuildPolicy"),
                                                     _iam.ManagedPolicy.from_managed_policy_arn(
                                       self, "MyCustomPolicy", managed_policy_arn=codebuild_managed_policy.managed_policy_arn)
                                   ])

        # CodeBuild Project to build custom AMI using packer tool.
        custom_ami_build = codebuild.PipelineProject(self, "CustomAMIBuild",
                                                     role=codebuild_role,
                                                     build_spec=codebuild.BuildSpec.from_source_filename(
                                                         build_spec),
                                                     environment_variables={"NAMETAG": codebuild.BuildEnvironmentVariable(value="BatchAMI1"),
                                                                            "InstanceIAMRole": codebuild.BuildEnvironmentVariable(value=instance_profile.instance_profile_name)},
                                                     environment=dict(build_image=codebuild.LinuxBuildImage.from_code_build_image_id("aws/codebuild/standard:5.0")))

        batch_build = codebuild.PipelineProject(self, "BatchBuild",
                                                build_spec=codebuild.BuildSpec.from_object(dict(
                                                    version="0.2",
                                                    phases=dict(
                                                        install=dict(
                                                            commands=[
                                                                "npm install aws-cdk",
                                                                "npm update",
                                                                "python -m pip install -r requirements.txt"
                                                            ]),
                                                        build=dict(commands=[
                                                            "npx cdk synth -o dist",
                                                            "npx cdk deploy VpcStack --require-approval never"
                                                            ])),
                                                    artifacts={
                                                        "base-directory": "dist",
                                                        "files": [
                                                            "BatchStack.template.json",
                                                            "TestStack.template.json"]},
                                                    environment=dict(buildImage=codebuild.LinuxBuildImage.STANDARD_2_0))))
        
     

        source_output = codepipeline.Artifact()
        batch_build_output = codepipeline.Artifact("BatchBuildOutput")
        custom_ami_build_output = codepipeline.Artifact("CustomAMIBuildOutput")

        codepipeline.Pipeline(self, "Pipeline",
            stages=[
                codepipeline.StageProps(stage_name="Source",
                    actions=[
                        codepipeline_actions.CodeCommitSourceAction(
                            action_name="CodeCommit_Source",
                            branch="main",
                            repository=code,
                            output=source_output)]),
                codepipeline.StageProps(stage_name="Build",
                    actions=[
                        codepipeline_actions.CodeBuildAction(
                            action_name="Batch_Build",
                            project=batch_build,
                            input=source_output,
                            run_order=2,
                            outputs=[batch_build_output]),
                        codepipeline_actions.CodeBuildAction(
                            action_name="CustomAMI_Build",
                            variables_namespace="BuildVariables",
                            project=custom_ami_build,
                            run_order=1,
                            input=source_output,
                            outputs=[custom_ami_build_output])
                        ]),
                codepipeline.StageProps(stage_name="Test",
                    actions=[
                        
                        codepipeline_actions.CloudFormationCreateUpdateStackAction(
                              action_name="Batch_CFN_Deploy",
                              template_path=batch_build_output.at_path(
                                  "TestStack.template.json"
                              ),
                              run_order=1,
                              stack_name="TestDeployStack",
                              parameter_overrides={"ImageId":"#{BuildVariables.AMIID}","TestEnv":"#{BuildVariables.TestEnv}"},
                              admin_permissions=True,
                              extra_inputs=[custom_ami_build_output,batch_build_output]
                              )]
                            ),
                codepipeline.StageProps(stage_name="Step",
                    actions=[
                        codepipeline_actions.StepFunctionInvokeAction(
                            action_name="Invoke",
                            state_machine=my_statemachine,
                            # input=source_output,
                            # state_machine_input=source_output
                            # state_machine_input=codepipeline_actions.StateMachineInput.literal(IsHelloWorldExample=True)
                            )]
                            ),
                codepipeline.StageProps(stage_name="FinalStack",
                    actions=[
                        codepipeline_actions.ManualApprovalAction(
                                action_name="ApproveChanges",
                                run_order=1),
                        codepipeline_actions.CloudFormationCreateUpdateStackAction(
                              action_name="Batch_CFN_Deploy",
                              template_path=batch_build_output.at_path(
                                  "BatchStack.template.json"
                              ),
                              run_order=2,
                              stack_name="BatchDeployStack",
                              parameter_overrides={"ImageId":"#{BuildVariables.AMIID}","MainEnv":"#{BuildVariables.MainEnv}"},
                              admin_permissions=True,
                              extra_inputs=[custom_ami_build_output,batch_build_output]
                              )]
                            )  
                ]
            )
