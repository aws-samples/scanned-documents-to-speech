# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import pathlib

from aws_cdk.aws_apigatewayv2 import CfnApi
from aws_cdk.aws_iam import ManagedPolicy, Role, ServicePrincipal
from aws_cdk.aws_lambda import Code, Function, LayerVersion, Runtime
from aws_cdk.aws_s3 import Bucket
from aws_cdk.aws_sns import Topic
from aws_cdk.core import Aws, Construct, Stack


TAG_NAME = 'app'


class LambdaStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, s3_bucket: Bucket, conversion_api: CfnApi, textract_sns_topic: Topic, polly_sns_topic: Topic, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        app_name = self.node.try_get_context('app-name')

        self.on_polly_ready_func = Function(
            self,
            id=f'{app_name}-LAMBDA-ON-POLLY-READY',
            function_name=f'{app_name}-on-polly-ready',
            handler='on_polly_ready.lambda_handler',
            runtime=Runtime.PYTHON_3_7,
            code=Code.from_asset(str(pathlib.PurePath(__file__).parent / 'lambda_on_polly_ready')),
            environment={
                'APP_NAME': app_name,
                'CONVERSION_API_ENDPOINT': conversion_api.ref,
                'CONVERSION_API_REGION': Aws.REGION,
            },
            role=Role(
                self,
                id=f'{app_name}-ON-POLLY-READY-FUNC-ROLE',
                assumed_by=ServicePrincipal('lambda.amazonaws.com'),
                managed_policies=[
                    ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole'),
                    ManagedPolicy.from_aws_managed_policy_name('AmazonAPIGatewayInvokeFullAccess'),
                    ManagedPolicy.from_aws_managed_policy_name('AmazonDynamoDBReadOnlyAccess'),
                ]
            ),
        )

        self.convert_images_to_text_func = Function(
            self,
            id=f'{app_name}-LAMBDA-CONVERT-IMAGES-TO-TEXT',
            function_name=f'{app_name}-convert-images-to-text',
            handler='convert_images_to_text.lambda_handler',
            runtime=Runtime.PYTHON_3_7,
            code=Code.from_asset(str(pathlib.PurePath(__file__).parent / 'lambda_convert_images_to_text')),
            environment={
                'APP_NAME': app_name,
                'CONVERSION_API_ENDPOINT': conversion_api.ref,
                'CONVERSION_API_REGION': Aws.REGION,
                'TEXTRACT_SERVICE_ROLE': Role(
                    self,
                    id=f'{app_name}-TEXTRACT-SERVICE-ROLE',
                    assumed_by=ServicePrincipal('textract.amazonaws.com'),
                    managed_policies=[
                        ManagedPolicy.from_aws_managed_policy_name('service-role/AmazonTextractServiceRole'),
                    ],
                ).role_arn,
                f'{app_name}_TEXTRACT_SNS_TOPIC_ARN': textract_sns_topic.topic_arn,
            },
            layers=[
                LayerVersion(
                    self,
                    id=f'{app_name}-LAMBDA-LAYER-CONVERT-IMAGES-TO-TEXT',
                    code=Code.from_asset(str(pathlib.PurePath(__file__).parent / 'lambda_convert_images_to_text_layer/img2pdf.zip')),
                ),
            ],
            role=Role(
                self,
                id=f'{app_name}-CONVERT-IMAGES-TO-TEXT-FUNC-ROLE',
                assumed_by=ServicePrincipal('lambda.amazonaws.com'),
                managed_policies=[
                    ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole'),
                    ManagedPolicy.from_aws_managed_policy_name('AmazonAPIGatewayInvokeFullAccess'),
                    ManagedPolicy.from_aws_managed_policy_name('AmazonDynamoDBFullAccess'),
                    ManagedPolicy.from_aws_managed_policy_name('AmazonTextractFullAccess'),
                    ManagedPolicy.from_aws_managed_policy_name('AmazonS3FullAccess'),
                    ManagedPolicy.from_aws_managed_policy_name('AmazonSNSFullAccess'),
                ]
            ),
        )

        self.retrieve_text_func = Function(
            self,
            id=f'{app_name}-LAMBDA-RETRIEVE-TEXT',
            function_name=f'{app_name}-retrieve-text',
            handler='retrieve_text.lambda_handler',
            runtime=Runtime.PYTHON_3_7,
            code=Code.from_asset(str(pathlib.PurePath(__file__).parent / 'lambda_retrieve_text')),
            environment={
                'APP_NAME': app_name,
                'CONVERSION_API_ENDPOINT': conversion_api.ref,
                'CONVERSION_API_REGION': Aws.REGION,
            },
            role=Role(
                self,
                id=f'{app_name}-RETRIEVE-TEXT-FUNC-ROLE',
                assumed_by=ServicePrincipal('lambda.amazonaws.com'),
                managed_policies=[
                    ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole'),
                    ManagedPolicy.from_aws_managed_policy_name('AmazonAPIGatewayInvokeFullAccess'),
                    ManagedPolicy.from_aws_managed_policy_name('AmazonTextractFullAccess'),
                ]
            ),
        )

        self.store_text_func = Function(
            self,
            id=f'{app_name}-LAMBDA-STORE-TEXT',
            function_name=f'{app_name}-store-text',
            handler='store_text.lambda_handler',
            runtime=Runtime.PYTHON_3_7,
            code=Code.from_asset(str(pathlib.PurePath(__file__).parent / 'lambda_store_text')),
            environment={
                'APP_NAME': app_name,
                'CONVERSION_API_ENDPOINT': conversion_api.ref,
                'CONVERSION_API_REGION': Aws.REGION,
                'S3_BUCKET': s3_bucket.bucket_name,
            },
            role=Role(
                self,
                id=f'{app_name}-STORE-TEXT-FUNC-ROLE',
                assumed_by=ServicePrincipal('lambda.amazonaws.com'),
                managed_policies=[
                    ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole'),
                    ManagedPolicy.from_aws_managed_policy_name('AmazonAPIGatewayInvokeFullAccess'),
                    ManagedPolicy.from_aws_managed_policy_name('AmazonS3FullAccess'),
                ]
            ),

        )

        self.moderate_text_func = Function(
            self,
            id=f'{app_name}-LAMBDA-MODERATE-TEXT',
            function_name=f'{app_name}-moderate-text',
            handler='moderate_text.lambda_handler',
            runtime=Runtime.PYTHON_3_7,
            code=Code.from_asset(str(pathlib.PurePath(__file__).parent / 'lambda_moderate_text')),
            environment={
                'CONVERSION_API_ENDPOINT': conversion_api.ref,
                'CONVERSION_API_REGION': Aws.REGION,
            },
            role=Role(
                self,
                id=f'{app_name}-MODERATE-TEXT-FUNC-ROLE',
                assumed_by=ServicePrincipal('lambda.amazonaws.com'),
                managed_policies=[
                    ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole'),
                    ManagedPolicy.from_aws_managed_policy_name('AmazonAPIGatewayInvokeFullAccess'),
                ]
            ),

        )

        self.convert_text_to_audio_func = Function(
            self,
            id=f'{app_name}-LAMBDA-CONVERT-TEXT-TO-AUDIO',
            function_name=f'{app_name}-convert-text-to-audio',
            handler='convert_text_to_audio.lambda_handler',
            runtime=Runtime.PYTHON_3_7,
            code=Code.from_asset(str(pathlib.PurePath(__file__).parent / 'lambda_convert_text_to_audio')),
            environment={
                'APP_NAME': app_name,
                'CONVERSION_API_ENDPOINT': conversion_api.ref,
                'CONVERSION_API_REGION': Aws.REGION,
                'S3_BUCKET': s3_bucket.bucket_name,
                f'{app_name}_POLLY_SNS_TOPIC_ARN': polly_sns_topic.topic_arn,
            },
            role=Role(
                self,
                id=f'{app_name}-CONVERT-TEXT-TO-AUDIO-FUNC-ROLE',
                assumed_by=ServicePrincipal('lambda.amazonaws.com'),
                managed_policies=[
                    ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole'),
                    ManagedPolicy.from_aws_managed_policy_name('AmazonAPIGatewayInvokeFullAccess'),
                    ManagedPolicy.from_aws_managed_policy_name('AmazonDynamoDBFullAccess'),
                    ManagedPolicy.from_aws_managed_policy_name('AmazonPollyFullAccess'),
                    ManagedPolicy.from_aws_managed_policy_name('AmazonS3FullAccess'),
                    ManagedPolicy.from_aws_managed_policy_name('AmazonSNSFullAccess'),
                ]
            ),
        )

        # tag all resources with app_name
        self.tags.set_tag(TAG_NAME, app_name, apply_to_launched_instances=True)

