from aws_cdk import (core, 
                     aws_ec2 as _ec2, 
                     aws_codecommit as _codecommit
                     )

class VpcStack(core.Stack):

    def __init__(self, app: core.App, id: str, **kwargs):
        super().__init__(app, id, **kwargs)

        # Create custom VPC for final Batch compute environment.
        vpc = _ec2.Vpc(self, "VPC")
        self.vpc = vpc