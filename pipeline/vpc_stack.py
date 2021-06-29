from aws_cdk import (core, 
                     aws_ec2 as _ec2, 
                     aws_codecommit as _codecommit
                     )

class VpcStack(core.Stack):

    def __init__(self, app: core.App, id: str, repo_name: str = None, **kwargs):
        super().__init__(app, id, **kwargs)

        # Example automatically generated without compilation. See https://github.com/aws/jsii/issues/826
        vpc = _ec2.Vpc(self, "VPC")
        self.vpc = vpc

        my_repo = _codecommit.Repository(self, "PipelineRepo", repository_name=repo_name, description='Batch Custom AMI codepipeline repository')

        print("Use CodeCommit http URL to clone \n")
        core.CfnOutput(self, "CodeCommitRepo", value=my_repo.repository_clone_url_http, description='CodeCommit http URL')