from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3_assets as s3_assets
from constructs import Construct

from odin_config import (
    ODIN_AVAILABILITY_ZONE,
    ODIN_FLASK_EIP,
    ODIN_FLASK_IP,
    ODIN_KEY_PAIR,
    ODIN_PUBLIC_SUBNET,
    ODIN_VPC,
)


class FlaskInstance(ec2.Instance):
    def __init__(self, scope: Construct, id: str) -> None:
        vpc = ec2.Vpc.from_lookup(scope, "OdinFlaskVPC", vpc_id=ODIN_VPC)
        subnet = ec2.Subnet.from_subnet_attributes(
            scope,
            "OdinFlaskPublicSubnet",
            subnet_id=ODIN_PUBLIC_SUBNET,
            availability_zone=ODIN_AVAILABILITY_ZONE,
        )
        security_group = ec2.SecurityGroup(
            scope, "OdinFlaskSecurityGroup", vpc=vpc
        )
        security_group.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(22))
        security_group.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80))

        # Create IAM role for EC2 instances
        role = iam.Role(
            scope,
            "OdinFlaskInstanceRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
        )
        role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AmazonS3ReadOnlyAccess"
            )
        )
        code_asset = s3_assets.Asset(
            scope,
            "FlaskCodeAsset",
            path="./",
            exclude=["**/.git/*", "**/cdk.out/*"],
        )
        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            "amazon-linux-extras install epel -y",
            "yum update -y",
            "yum install -y python3 python3-pip s3fs-fuse",
            "pip3 install gunicorn flask",
            "mkdir /mnt/odin-zpt",
            "mkdir /mnt/odin-vds-data",
            "mkdir /mnt/odin-apriori",
            "s3fs odin-zpt /mnt/odin-zpt -o allow_other,iam_role",
            "s3fs odin-vds-data /mnt/odin-vds-data -o allow_other,iam_role",
            "s3fs odin-apriori /mnt/odin-apriori -o allow_other,iam_role",
            f"aws s3 cp {code_asset.s3_object_url} "
            f"/home/ec2-user/flask_app.zip",
            "unzip flask_app.zip -d app",
            'echo "from flask import Flask; app = Flask(__name__)" '
            "> /home/ec2-user/application.py",
            'echo "from application import app" > /home/ec2-user/wsgi.py',
            'echo "gunicorn --bind 0.0.0.0:80 wsgi:app" > '
            "/home/ec2-user/start_server.sh",
            "chmod +x /home/ec2-user/start_server.sh",
            # "nohup /home/ec2-user/start_server.sh > /dev/null 2>&1 &",
        )
        super().__init__(
            scope,
            id,
            instance_type=ec2.InstanceType("t3.small"),
            machine_image=ec2.MachineImage.generic_linux(
                {
                    "eu-north-1": "ami-08fdff97845b0d82e",
                }
            ),
            vpc=vpc,
            instance_name=id,
            key_name=ODIN_KEY_PAIR,
            private_ip_address=ODIN_FLASK_IP,
            role=role,
            security_group=security_group,
            user_data=user_data,
            vpc_subnets=ec2.SubnetSelection(subnets=[subnet]),
        )
        ec2.CfnEIPAssociation(
            scope,
            "OdinFlaskEIPAssoc",
            allocation_id=ODIN_FLASK_EIP,
            instance_id=self.instance_id,
        )
