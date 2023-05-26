from odin_api_stack.api import APIInstance
from odin_api_stack.mongo import MongoInstance


from aws_cdk import Stack
from constructs import Construct


class OdinAPIStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        MongoInstance(self, "OdinMongo")
        APIInstance(self, "OdinAPI")
