from aws_cdk import (core, 
                     aws_ec2 as ec2, 
                     )

class VpcStack(core.Stack):

    def __init__(self, app: core.App, id: str, **kwargs):
        super().__init__(app, id, **kwargs)

        # Example automatically generated without compilation. See https://github.com/aws/jsii/issues/826
        vpc = ec2.Vpc(self, "VPC")
        self.vpc = vpc