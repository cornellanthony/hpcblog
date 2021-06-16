from aws_cdk import (core, aws_codebuild as codebuild,
                     aws_codecommit as codecommit,
                     aws_codepipeline as codepipeline,
                     aws_codepipeline_actions as codepipeline_actions,

                     aws_ec2 as ec2, 
                     aws_lambda as lambda_,
                     aws_iam as _iam)
import json
class PipelineStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, *, repo_name: str=None, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        
        # Example automatically generated without compilation. See https://github.com/aws/jsii/issues/826
        vpc = ec2.Vpc(self, "VPC")
        self.vpc = vpc

        core.CfnOutput(self, "MyBatchVPC", value=vpc.vpc_id, export_name="mybatchamivpc")

        code = codecommit.Repository.from_repository_name(self, "ImportedRepo",
                  repo_name)
        # Read CodeBuild buildspec.yaml file. 
        with open ("packer/buildspec.yml", "r") as myfile:
            build_spec=myfile.read()
        
        # Policy Document.
        with open ("packer/policy_doc.json", "r") as policydoc:
            packer_policy=policydoc.read()
        
        codebuild_packer_policy = json.loads(packer_policy)
        antcorn = _iam.PolicyDocument.from_json(codebuild_packer_policy)
        # custom_policy_document = _iam.PolicyDocument.from_json(json.dumps(json.dumps(packer_policy))
        # my_policy = _iam.PolicyDocument(self, "PolicyDocument", statements=packer_policy)
        codebuild_managed_policy = _iam.ManagedPolicy(self, "CodeBuildManagedPolicy",document=antcorn,managed_policy_name="CodeBuildPolicy")
        #Instance for packer tool 
        instance_role = _iam.Role(self, "PackerInstanceRole",
                        assumed_by=_iam.ServicePrincipal("ec2.amazonaws.com"),
                        managed_policies=[_iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3ReadOnlyAccess")])
        #CodeBuild Role with packer policy.
        codebuild_role = _iam.Role(self,"CodeBuildRole",
                            assumed_by=_iam.ServicePrincipal("codebuild.amazonaws.com"),
                            managed_policies=[_iam.ManagedPolicy.from_aws_managed_policy_name("AWSCodeBuildAdminAccess"),
                                              _iam.ManagedPolicy.from_managed_policy_name(self, "ManagedPolicyCodeBuild", managed_policy_name="CodeBuildPolicy")
                                               ])
     
        #CodeBuild Project to build custom AMI using packer tool. 
        custom_ami_build = codebuild.PipelineProject(self, "CustomAMIBuild",
                        build_spec=codebuild.BuildSpec.from_source_filename(build_spec),
                        environment_variables={"NAMETAG": codebuild.BuildEnvironmentVariable(value="Ver1"),
                                                "VPCID": codebuild.BuildEnvironmentVariable(value=vpc.vpc_id),
                                                "SubnetIds":codebuild.BuildEnvironmentVariable(value=vpc.private_subnets.pop()),
                                                "InstanceIAMRole":codebuild.BuildEnvironmentVariable(value=instance_role)},
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
                                    "ls -l dist/BatchStack.template.json"])),
                            artifacts={
                                "base-directory": "dist",
                                "files": [
                                    "BatchStack.template.json",
                                    "TestStack.template.json"]},
                            environment=dict(buildImage=
                                codebuild.LinuxBuildImage.STANDARD_2_0))))


        source_output = codepipeline.Artifact()
        batch_build_output = codepipeline.Artifact("BatchBuildOutput")
        custom_ami_build_output = codepipeline.Artifact("CustomAMIBuildOutput")

        codepipeline.Pipeline(self, "Pipeline",
            stages=[
                codepipeline.StageProps(stage_name="Source",
                    actions=[
                        codepipeline_actions.CodeCommitSourceAction(
                            action_name="CodeCommit_Source",
                            branch="antcorne",
                            repository=code,
                            output=source_output)]),
                codepipeline.StageProps(stage_name="Build",
                    actions=[
                        codepipeline_actions.CodeBuildAction(
                            action_name="Batch_Build",
                            project=batch_build,
                            input=source_output,
                            run_order=2,
                            outputs=[batch_build_output])
                        # codepipeline_actions.CodeBuildAction(
                        #     action_name="CustomAMI_Build",
                        #     project=custom_ami_build,
                        #     run_order=1,
                        #     input=source_output,
                        #     outputs=[custom_ami_build_output])
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
                              admin_permissions=True,
                              extra_inputs=[batch_build_output]
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
                              admin_permissions=True,
                              extra_inputs=[batch_build_output]
                              )]
                            )  
                ]
            )

        # core.Tag.add(vpc, "Project", "Batch Custom AMI VPC")
        # core.Tag.add(code,"Project", "Batch Custom AMI Code")
        # core.Tag.add(batch_build, "Project", "Batch Custom ami build")
