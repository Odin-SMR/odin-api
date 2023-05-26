from aws_cdk import App, Environment

from odin_api_stack.odin_api import OdinAPIStack
from odin_api_stack.config import ODIN_AWS_ACCOUNT, ODIN_AWS_REGION


env = Environment(account=ODIN_AWS_ACCOUNT, region=ODIN_AWS_REGION)
app = App()
OdinAPIStack(app, "OdinAPIStack", env=env)
app.synth()
