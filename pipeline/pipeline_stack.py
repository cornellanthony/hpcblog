from aws_cdk import (core, aws_codebuild as codebuild,
                     aws_codecommit as codecommit,
                     aws_codepipeline as codepipeline,
                     aws_codepipeline_actions as codepipeline_actions,
                     aws_ec2 as ec2, 
                     aws_lambda as lambda_)

class PipelineStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, *, repo_name: str=None, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        
        # Example automatically generated without compilation. See https://github.com/aws/jsii/issues/826
        vpc = ec2.Vpc(self, "VPC")
        self.vpc = vpc

        core.CfnOutput(self, "MyBatchVPC", value=vpc.vpc_id, export_name="mybatchamivpc")

        code = codecommit.Repository.from_repository_name(self, "ImportedRepo",
                  repo_name)

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
                            outputs=[batch_build_output]),
                        ]),
                codepipeline.StageProps(stage_name="Test",
                    actions=[
                        codepipeline_actions.CloudFormationCreateUpdateStackAction(
                              action_name="Batch_CFN_Deploy",
                              template_path=batch_build_output.at_path(
                                  "TestStack.template.json"
                              ),
                              stack_name="TestDeployStack",
                              admin_permissions=True,
                              extra_inputs=[batch_build_output]
                              )]
                            ),
                codepipeline.StageProps(stage_name="FinalStack",
                    actions=[
                        codepipeline_actions.CloudFormationCreateUpdateStackAction(
                              action_name="Batch_CFN_Deploy",
                              template_path=batch_build_output.at_path(
                                  "BatchStack.template.json"
                              ),
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