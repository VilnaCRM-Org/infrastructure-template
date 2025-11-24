"""An AWS Python Pulumi program"""

import pulumi
from pulumi_aws import ec2

config = pulumi.Config()
ami_id = config.require("amiId")

instance = ec2.Instance(
    "app-server",
    ami=ami_id,
    instance_type="t2.micro",
    tags={"Name": "ExampleAppServerInstance"},
)

# Export the instance details
pulumi.export("instance_id", instance.id)
pulumi.export("instance_public_ip", instance.public_ip)
pulumi.export("instance_private_ip", instance.private_ip)
