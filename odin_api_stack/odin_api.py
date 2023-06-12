from aws_cdk import Stack, Duration
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ecs_patterns as ecs_patterns
from aws_cdk import aws_logs as logs
from aws_cdk import aws_ssm as ssm
from constructs import Construct

from odin_api_stack.api import APIInstance
from odin_api_stack.config import ODIN_API_EIP
from odin_api_stack.mongo import MongoInstance


class OdinAPIStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        vpc = ec2.Vpc(
            self,
            "OdinVPC",
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="OdinPublicSubnet",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="OdinPrivateNATSubnet",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="OdinPrivateSubnet",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                ),
            ],
        )

        ec2.CfnNatGateway(
            self,
            "OdinNatGateway",
            allocation_id=ODIN_API_EIP,
            subnet_id=vpc.public_subnets[0].subnet_id,
        )
        mongo: ec2.Instance = MongoInstance(self, "OdinMongo", vpc=vpc)
        #        odin_api = APIInstance(self, "OdinAPI", vpc=vpc)
        logging = ecs.AwsLogDriver(
            stream_prefix="Odin/OdinAPI", log_retention=logs.RetentionDays.ONE_MONTH
        )

        odin_cluster = ecs.Cluster(self, "OdinCluster", vpc=vpc)

        odinapi_task: ecs.FargateTaskDefinition = ecs.FargateTaskDefinition(
            self,
            "OdinAPITaskDefinition",
        )
        odin_secret_key = ssm.StringParameter.from_string_parameter_name(
            self, "OdinSecretKey", "/odin-api/secret-key"
        ).string_value
        odin_mongo_user = ssm.StringParameter.from_string_parameter_name(
            self, "OdinMongoUser", "/odin/mongo/user"
        ).string_value
        odin_mongo_password = ssm.StringParameter.from_string_parameter_name(
            self, "OdinMongoPassword", "/odin/mongo/password"
        ).string_value
        odin_pghost = ssm.StringParameter.from_string_parameter_name(
            self, "OdinPGHOST", "/odin/psql/host"
        ).string_value
        odin_pguser = ssm.StringParameter.from_string_parameter_name(
            self, "OdinPGUSER", "/odin/psql/user"
        ).string_value
        odin_pgdbname = ssm.StringParameter.from_string_parameter_name(
            self, "OdinPGDBNAME", "/odin/psql/db"
        ).string_value
        odin_pgpass = ssm.StringParameter.from_string_parameter_name(
            self, "OdinPGPASS", "/odin/psql/password"
        ).string_value

        odinapi_task.add_container(
            "OdinAPIContainer",
            image=ecs.ContainerImage.from_asset("./"),
            memory_limit_mib=1024,
            cpu=512,
            port_mappings=[
                ecs.PortMapping(container_port=8000, protocol=ecs.Protocol.TCP),
            ],
            environment={
                "SECRET_KEY": odin_secret_key,
                "ODIN_API_PRODUCTION": "1",
                "ODINAPI_MONGODB_USERNAME": odin_mongo_user,
                "ODINAPI_MONGODB_PASSWORD": odin_mongo_password,
                "ODINAPI_MONGODB_HOST": mongo.instance_private_ip,
                "PGHOST": odin_pghost,
                "PGDBNAME": odin_pgdbname,
                "PGUSER": odin_pguser,
                "PGPASS": odin_pgpass,
                "GUNICORN_CMD_ARGS": "-w 4 -b 0.0.0.0 -k gevent --timeout 60 --log-level debug",
            },
            health_check=ecs.HealthCheck(
                command=["CMD-SHELL", "curl -f http://localhost:8000/ || exit 1"],
                interval=Duration.seconds(60),
                start_period=Duration.seconds(10),
            ),
            logging=logging,
        )

        odin_service: ecs_patterns.ApplicationLoadBalancedFargateService = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "OdinAPIFargateService",
            task_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            cluster=odin_cluster,
            cpu=1024,
            desired_count=1,
            task_definition=odinapi_task,
            memory_limit_mib=4096,
            public_load_balancer=True,
            listener_port=80,
            health_check_grace_period=Duration.seconds(20),
        )
        odin_service.target_group.configure_health_check(path="/", port="8000")