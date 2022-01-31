# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk.aws_sns import Topic
from aws_cdk.aws_sns_subscriptions import LambdaSubscription
from aws_cdk.core import Construct, Stack


TAG_NAME = 'app'


class SnsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        app_name = self.node.try_get_context('app-name')

        self.textract_topic = self._create_textract_sns_topic(app_name)
        self.polly_topic = self._create_polly_sns_topic(app_name)

        # tag all resources with app_name
        self.tags.set_tag(TAG_NAME, app_name, apply_to_launched_instances=True)

    def _create_textract_sns_topic(self, app_name):
        topic = Topic(
            self,
            id=f'{app_name}-SNS-TOPIC-TEXTRACT',
            topic_name=f'AmazonTextract-{app_name}',
        )

        return topic

    def _create_polly_sns_topic(self, app_name):
        topic = Topic(
            self,
            id=f'{app_name}-SNS-TOPIC-POLLY',
            topic_name=f'AmazonPolly-{app_name}',
        )

        return topic

    def add_textract_topic_subscription(self, on_textract_ready_func):
        self.textract_topic.add_subscription(LambdaSubscription(on_textract_ready_func))

    def add_polly_topic_subscription(self, on_polly_ready_func):
        self.polly_topic.add_subscription(LambdaSubscription(on_polly_ready_func))
