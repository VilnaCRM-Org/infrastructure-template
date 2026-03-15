from __future__ import annotations

"""Pulumi component that provisions the template EC2 instance."""

from typing import Optional

import pulumi
from pulumi_aws import ec2


class ExampleServer(pulumi.ComponentResource):
    """Provision a single EC2 instance from Pulumi config or explicit arguments."""

    def __init__(
        self,
        name: str,
        *,
        ami_id: Optional[str] = None,
        instance_type: Optional[str] = None,
        name_tag: Optional[str] = None,
        opts: Optional[pulumi.ResourceOptions] = None,
    ) -> None:
        super().__init__(
            "infrastructure-template:compute:ExampleServer", name, None, opts
        )

        config = pulumi.Config()

        resolved_ami_id = ami_id or config.require("amiId")
        resolved_instance_type = (
            instance_type or config.get("instanceType") or "t2.micro"
        )
        resolved_name_tag = (
            name_tag or config.get("nameTag") or "ExampleAppServerInstance"
        )
        resolved_tags = {"Name": resolved_name_tag}

        self.instance = ec2.Instance(
            "app-server",
            ami=resolved_ami_id,
            instance_type=resolved_instance_type,
            tags=resolved_tags,
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.ami_id = pulumi.Output.from_input(resolved_ami_id)
        self.instance_type = pulumi.Output.from_input(resolved_instance_type)
        self.tags = pulumi.Output.from_input(resolved_tags)
        self.instance_id = self.instance.id
        self.instance_public_ip = self.instance.public_ip
        self.instance_private_ip = self.instance.private_ip

        self.register_outputs(
            {
                "amiId": self.ami_id,
                "instanceId": self.instance_id,
                "instanceType": self.instance_type,
                "instancePublicIp": self.instance_public_ip,
                "instancePrivateIp": self.instance_private_ip,
                "tags": self.tags,
            }
        )
