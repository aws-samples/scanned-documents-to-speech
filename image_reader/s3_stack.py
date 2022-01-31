# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk.core import Construct, CfnOutput, PhysicalName, Stack
from aws_cdk.aws_s3 import Bucket


TAG_NAME = 'app'


class S3Stack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        app_name = self.node.try_get_context('app-name')

        self.s3_bucket = Bucket(
            scope=self,
            id=f'{app_name}-S3-BUCKET',
            bucket_name=PhysicalName.GENERATE_IF_NEEDED,
        )

        CfnOutput(
            scope=self,
            id=f'{app_name}-S3-BUCKET-NAME',
            value=self.s3_bucket.bucket_name,
        )

        # tag all resources with app_name
        self.tags.set_tag(TAG_NAME, app_name, apply_to_launched_instances=True)
