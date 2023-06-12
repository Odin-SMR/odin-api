import textwrap

from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3_assets as s3_assets
from constructs import Construct

from odin_api_stack.config import ODIN_KEY_PAIR


def install_packages():
    return (
        "amazon-linux-extras install epel -y",
        "amazon-linux-extras enable postgresql14 -y",
        "amazon-linux-extras enable python3.8 -y",
        "yum update -y",
        "yum groupinstall -y 'Development Tools'",
        "yum install -y python38 python38-devel python38-pip s3fs-fuse libgfortran hdf5-devel hdf-devel libpq-devel",
    )


def setup_s3_mountpoints():
    return (
        "mkdir -p /ecmwf-data",
        "s3fs odin-ecmwf /ecmwf-data -o allow_other,iam_role",
        "mkdir -p /var/lib/odindata/ECMWF",
        "s3fs odin-ecmwf /var/lib/odindata/ECMWF -o allow_other,iam_role",
        "mkdir -p /vds-data",
        "s3fs odin-vds-data /vds-data -o allow_other,iam_role",
        "mkdir -p /var/lib/odindata/zpt",
        "s3fs odin-zpt /var/lib/odindata/zpt -o allow_other,iam_role",
        "mkdir -p /var/lib/odindata/ZPT",
        "s3fs odin-zpt /var/lib/odindata/ZPT -o allow_other,iam_role",
        "mkdir -p /var/lib/odindata/apriori",
        "s3fs odin-apriori /var/lib/odindata/apriori -o allow_other,iam_role",
        "mkdir -p /osiris-data",
        "s3fs odin-osiris /osiris-data -o allow_other,iam_role",
        "mkdir -p /odin-smr-2-0-data",
        "s3fs odin-smr:/Data/SMRl2/SMRhdf/Qsmr-2-0 /odin-smr-2-0-data -o allow_other,iam_role",
        "mkdir -p /odin-smr-2-1-data",
        "s3fs odin-smr:/Data/SMRl2/SMRhdf/Qsmr-2-1 /odin-smr-2-1-data -o allow_other,iam_role",
        "mkdir -p /odin-smr-2-3-data",
        "s3fs odin-smr:/Data/SMRl2/SMRhdf/Qsmr-2-3 /odin-smr-2-3-data -o allow_other,iam_role",
        "mkdir -p /odin-smr-2-4-data",
        "s3fs odin-smr:/Data/SMRl2/SMRhdf/Qsmr-2-4 /odin-smr-2-4-data -o allow_other,iam_role",
        "mkdir -p /data/odin-l2-data",
        "s3fs odin-l2netcdf /data/odin-l2-data -o allow_other,iam_role",
        "mkdir -p /data/MesosphEO",
        "s3fs odin-mesospheo /data/MesosphEO -o allow_other,iam_role",
    )


def odin_api(asset: s3_assets.Asset):
    unit_file = textwrap.dedent(
        """
            [Unit]
            Description=Odin-API
            After=network.target

            [Service]
            User=ec2-user
            WorkingDirectory=/home/ec2-user/odin-api/src
            ExecStart=/usr/local/bin/gunicorn -w 4 -b 0.0.0.0 -k gevent --timeout 540 odinapi.api:app
            Restart=always

            [Install]
            WantedBy=multi-user.target
        """
    )
    return (
        f"aws s3 cp {asset.s3_object_url} " f"/home/ec2-user/flask_app.zip",
        "unzip /home/ec2-user/flask_app.zip -d /home/ec2-user/odin-api",
        "curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | bash",
        ". ~/.bashrc"
        "nvm install 16",
        "LD_LIBRARY_PATH=/usr/lib64/hdf pip3.8 install -r /home/ec2-user/odin-api/requirements.txt",
        f"echo '{unit_file}' > /etc/systemd/system/odinapi.service",
        "cd /home/ec2-user/odin-api",
        "./scripts/compile_nrlmsis.sh",
        "npm install",
        "npm run build",
        "systemctl enable odinapi.service",
        "systemctl start odinapi.service",
    )


class APIInstance(ec2.Instance):
    def __init__(self, scope: Construct, id: str, vpc: ec2.Vpc) -> None:
        vpc_subnets = ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)
        security_group = ec2.SecurityGroup(scope, "OdinAPISecurityGroup", vpc=vpc)
        security_group.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(22))
        security_group.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(8000))

        # Create IAM role for EC2 instances
        role = iam.Role(
            scope,
            "OdinAPIInstanceRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
        )
        role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3ReadOnlyAccess")
        )
        code_asset = s3_assets.Asset(
            scope,
            "OdinAPICodeAsset",
            path="./",
            exclude=["**/.git/*", "**/cdk.out/*"],
        )
        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            *install_packages(),
            *setup_s3_mountpoints(),
            *odin_api(code_asset),
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
            vpc_subnets=vpc_subnets,
            instance_name=id,
            key_name=ODIN_KEY_PAIR,
            role=role,
            security_group=security_group,
            user_data=user_data,
        )
