from aws_cdk import App, Environment, Stack
from constructs import Construct

from FlaskInstance import FlaskInstance
from MongoInstance import MongoInstance
from odin_config import ODIN_AWS_ACCOUNT, ODIN_AWS_REGION


class OdinAPIInstanceStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        MongoInstance(self, "OdinMongo")
        FlaskInstance(self, "OdinFlask")


env = Environment(account=ODIN_AWS_ACCOUNT, region=ODIN_AWS_REGION)
app = App()
OdinAPIInstanceStack(app, "OdinStack", env=env)
app.synth()
