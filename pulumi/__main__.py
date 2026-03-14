"""Pulumi entrypoint that exports baseline EC2 instance details."""

import pulumi

from app.server import ExampleServer


server = ExampleServer("example-server")

pulumi.export("instance_id", server.instance_id)
pulumi.export("instance_public_ip", server.instance_public_ip)
pulumi.export("instance_private_ip", server.instance_private_ip)
pulumi.export("instance_type", server.instance_type)
pulumi.export("instance_tags", server.tags)
