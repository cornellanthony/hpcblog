# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
from aws_cdk import core, aws_ec2 as ec2
class MyProjectStack(core.Stack):
    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        ImageID = core.CfnParameter(self, "AMIID", type="String", default="ami-089fedbcd30e5108e")
        custom_ami = ec2.MachineImage.generic_linux({"us-east-1": ImageID.value_as_string})
        print(custom_ami)
        # abc_template = ec2.CfnLaunchTemplate(self, "ABCTemplate", 
        #                                     launch_template_data={
        #                                     "block_device_mappings": [{
        #                                         "device_name": "/dev/xvdcz",
        #                                         "ebs": {
        #                                             "encrypted": True,
        #                                             "volume_size": 100,
        #                                             "volume_type": "gp2"
        #                                         }
        #                                     }
        #                                     ]
        #                                         # "image_id": [custom_ami]
        #                                     })
        # my_launch_template = ec2.CfnLaunchTemplate(self, "LaunchTemplate",
        #     launch_template_name="extra-storage-template",
        #     launch_template_data={
        #         "block_device_mappings": [{
        #             "device_name": "/dev/xvdcz",
        #             "ebs": {
        #                 "encrypted": True,
        #                 "volume_size": 100,
        #                 "volume_type": "gp2"
        #             }
        #         }
        #         ]
        #     }
        # )
        launch_template_data = ec2.CfnLaunchTemplate.LaunchTemplateDataProperty(
            image_id='ami-3ecc8f46',
                block_device_mappings=[{
                "device_name": "/dev/xvda",
                "ebs": {
                    "encrypted": True,
                    "volume_size": 100,
                    "iops": 5000,
                    "volume_type": "GP2",
                }
            }]
        )

        launch_template = ec2.CfnLaunchTemplate(
            self, f"LaunchTemplate", launch_template_data=launch_template_data,
        )