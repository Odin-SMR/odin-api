## Development Environment

For detailed setup and development instructions, please refer to our [README](../README.md).

### User Interaction

- Users are students and researchers who want to access and analyze atmospheric data.
- The application is a RESTful API that serves atmospheric data to clients.
- Ensure the API endpoints are well-documented and easy to use.


## Program architecture

- The API uses Python and Flask.
- Level1 data is stored in a postgresql database
- Level2 data is stored in a mongodb database.
- Apriori data is stored in S3.

## Style Guidelines
- Run black and mypy on all code before committing.
- Prefer simple and clear code over clever or complex solutions.
- Use already existing third-party libraries when possible instead of writing custom code.
- Write unit tests for all new features and bug fixes.
- Run tests before committing code.

## Runtime Environment
- The Docker image runs on AWS ECS Fargate.
- Ensure image is compliant with the task definition below.

### ECS Fargate Task Definition
```json
{
    "compatibilities": [
        "EC2",
        "FARGATE"
    ],
    "containerDefinitions": [
        {
            "command": [],
            "cpu": 0,
            "credentialSpecs": [],
            "dnsSearchDomains": [],
            "dnsServers": [],
            "dockerLabels": {},
            "dockerSecurityOptions": [],
            "entryPoint": [],
            "environment": [
                {
                    "name": "ODINAPI_MONGODB_HOST",
                    "value": "10.0.2.124"
                },
                {
                    "name": "ODINAPI_MONGODB_USERNAME",
                    "value": "odin"
                },
                {
                    "name": "ODIN_API_PRODUCTION",
                    "value": "1"
                },
                {
                    "name": "PGHOST",
                    "value": "vulcan.rss.chalmers.se"
                },
                {
                    "name": "ODINAPI_MONGODB_PASSWORD",
                    "value": "xxxx"
                },
                {
                    "name": "PGUSER",
                    "value": "odin"
                },
                {
                    "name": "PGDBNAME",
                    "value": "odin"
                },
                {
                    "name": "PGPASS",
                    "value": "xxxxx"
                },
                {
                    "name": "SECRET_KEY",
                    "value": "xxxxx"
                }
            ],
            "environmentFiles": [],
            "essential": true,
            "extraHosts": [],
            "healthCheck": {
                "command": [
                    "CMD-SHELL",
                    "curl -f http://localhost:8000/rest_api/health_check || exit 1"
                ],
                "interval": 120,
                "retries": 5,
                "timeout": 20
            },
            "image": "991049544436.dkr.ecr.eu-north-1.amazonaws.com/odin-api:latest",
            "links": [],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/Odin/OdinApi",
                    "awslogs-region": "eu-north-1",
                    "awslogs-stream-prefix": "OdinAPI"
                },
                "secretOptions": []
            },
            "mountPoints": [],
            "name": "OdinAPIContainer",
            "portMappings": [
                {
                    "appProtocol": "http2",
                    "containerPort": 8000,
                    "hostPort": 8000,
                    "name": "odinapi",
                    "protocol": "tcp"
                }
            ],
            "secrets": [],
            "systemControls": [],
            "ulimits": [],
            "volumesFrom": []
        }
    ],
    "cpu": "2048",
    "executionRoleArn": "arn:aws:iam::991049544436:role/OdinAPIStack-OdinAPITaskDefinitionExecutionRole9757-u0B2WAziDsL1",
    "family": "OdinAPIStackOdinAPITaskDefinitionC45B4FAA",
    "memory": "4096",
    "networkMode": "awsvpc",
    "placementConstraints": [],
    "registeredAt": "2025-06-05T19:14:10.436Z",
    "registeredBy": "arn:aws:sts::991049544436:assumed-role/cdk-hnb659fds-cfn-exec-role-991049544436-eu-north-1/AWSCloudFormation",
    "requiresAttributes": [
        {
            "name": "com.amazonaws.ecs.capability.logging-driver.awslogs"
        },
        {
            "name": "com.amazonaws.ecs.capability.docker-remote-api.1.24"
        },
        {
            "name": "ecs.capability.execution-role-awslogs"
        },
        {
            "name": "com.amazonaws.ecs.capability.ecr-auth"
        },
        {
            "name": "com.amazonaws.ecs.capability.docker-remote-api.1.19"
        },
        {
            "name": "com.amazonaws.ecs.capability.docker-remote-api.1.17"
        },
        {
            "name": "com.amazonaws.ecs.capability.task-iam-role"
        },
        {
            "name": "ecs.capability.container-health-check"
        },
        {
            "name": "ecs.capability.execution-role-ecr-pull"
        },
        {
            "name": "com.amazonaws.ecs.capability.docker-remote-api.1.18"
        },
        {
            "name": "ecs.capability.task-eni"
        }
    ],
    "requiresCompatibilities": [
        "FARGATE"
    ],
    "revision": 53,
    "status": "ACTIVE",
    "taskDefinitionArn": "arn:aws:ecs:eu-north-1:991049544436:task-definition/OdinAPIStackOdinAPITaskDefinitionC45B4FAA:53",
    "taskRoleArn": "arn:aws:iam::991049544436:role/OdinAPIStack-OdinAPITaskDefinitionTaskRole9E81737C-jYkL5MnU3MVg",
    "volumes": [],
    "tags": []
}
```