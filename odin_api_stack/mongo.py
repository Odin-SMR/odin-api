from odin_api_stack.config import (
    ODIN_AVAILABILITY_ZONE,
    ODIN_KEY_PAIR,
    ODIN_MONGO_DATA_VOLUME,
    ODIN_MONGO_IP,
    ODIN_PRIVATE_SUBNET,
    ODIN_VPC,
)


from aws_cdk import aws_ec2 as ec2, aws_iam as iam
from constructs import Construct


class MongoInstance(ec2.Instance):
    def __init__(self, scope: Construct, id: str) -> None:
        vpc = ec2.Vpc.from_lookup(scope, "OdinMongoVPC", vpc_id=ODIN_VPC)
        subnet = ec2.Subnet.from_subnet_attributes(
            scope,
            "OdinMongoPrivateSubnet",
            subnet_id=ODIN_PRIVATE_SUBNET,
            availability_zone=ODIN_AVAILABILITY_ZONE,
        )
        security_group = ec2.SecurityGroup(
            scope, "OdinMongoSecurityGroup", vpc=vpc
        )
        security_group.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(22))

        # Create IAM role for EC2 instances
        role = iam.Role(
            scope,
            "OdinMongoInstanceRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
        )
        mongodb_repo = """
            [mongodb-org-6.0]
            name=MongoDB Repository
            baseurl=https://repo.mongodb.org/yum/amazon/2/mongodb-org/6.0/x86_64/
            gpgcheck=1
            enabled=1
            gpgkey=https://www.mongodb.org/static/pgp/server-6.0.asc
        """
        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            f"echo '{mongodb_repo}' > /etc/yum.repos.d/mongodb-org-6.0.repo",
            "yum update -y",
            "yum install -y mongodb",
            "service mongod stop",
            "mkdir -p /data/mongodb",
            "mount /dev/sdf /data/mongodb",
            "chown mongod:mongod /data/mongodb",
            'sed -i "s|/var/lib/mongo|/data/mongodb|g" /etc/mongod.conf',
            "service mongod start",
        )
        super().__init__(
            scope,
            id,
            instance_type=ec2.InstanceType("t3.large"),
            machine_image=ec2.MachineImage.generic_linux(
                {
                    "eu-north-1": "ami-08fdff97845b0d82e",
                }
            ),
            vpc=vpc,
            instance_name=id,
            key_name=ODIN_KEY_PAIR,
            private_ip_address=ODIN_MONGO_IP,
            role=role,
            security_group=security_group,
            user_data=user_data,
            vpc_subnets=ec2.SubnetSelection(subnets=[subnet]),
        )
        # Attach existing EBS volume to MongoDB EC2 instance
        volume = ec2.Volume.from_volume_attributes(
            scope,
            "OdinMongoDBVolume",
            volume_id=ODIN_MONGO_DATA_VOLUME,
            availability_zone=ODIN_AVAILABILITY_ZONE,
        )

        volume.grant_attach_volume(
            iam.ServicePrincipal("ec2.amazonaws.com"), [self]
        )
        # attach large ebs volume
        ec2.CfnVolumeAttachment(
            scope,
            "OdinMongoVolumeAttachment",
            device="/dev/sdf",
            instance_id=self.instance_id,
            volume_id=ODIN_MONGO_DATA_VOLUME,
        )
