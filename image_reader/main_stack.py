# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk.core import Aws, CfnOutput, Construct, RemovalPolicy, Stack
from aws_cdk.aws_apigateway import (
    AwsIntegration,
    IntegrationOptions,
    IntegrationResponse,
    MethodLoggingLevel,
    MethodResponse,
    MockIntegration,
    RestApi,
    StageOptions
)
from aws_cdk.aws_apigatewayv2 import (
    CfnApi,
    CfnIntegration,
    CfnIntegrationResponse,
    CfnRoute,
    CfnRouteResponse,
    CfnStage
)
from aws_cdk.aws_dynamodb import Attribute, AttributeType, BillingMode, Table
from aws_cdk.aws_iam import ManagedPolicy, Role, ServicePrincipal
from aws_cdk.aws_lambda import Function


TAG_NAME = 'app'


class MainStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, conversion_api: CfnApi, convert_images_to_text_func: Function, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        app_name = self.node.try_get_context('app-name')

        apig_role = self._create_api_gateway_role(app_name)
        self.file_api = self._create_api_gateway_rest(app_name, apig_role)
        self._configure_api_gateway_web_socket(app_name, conversion_api, apig_role, convert_images_to_text_func)
        self._create_dynamo_db_table(app_name)

        CfnOutput(
            scope=self,
            id=f'{app_name}-FILE-API-ENDPOINT',
            value=self.file_api.url,
        )

        CfnOutput(
            scope=self,
            id=f'{app_name}-CONVERSION-API-ENDPOINT',
            value=f'{conversion_api.attr_api_endpoint}/{self.conversion_stage.stage_name}',
        )

        # tag all resources with app_name
        self.tags.set_tag(TAG_NAME, app_name, apply_to_launched_instances=True)

    def _create_api_gateway_role(self, app_name):
        return Role(
            scope=self,
            id=f'{app_name}-APIG-ROLE',
            assumed_by=ServicePrincipal('apigateway.amazonaws.com'),
            managed_policies=[
                ManagedPolicy.from_aws_managed_policy_name('AmazonS3FullAccess'),
                ManagedPolicy.from_aws_managed_policy_name('service-role/AmazonAPIGatewayPushToCloudWatchLogs'),
                ManagedPolicy.from_aws_managed_policy_name('AmazonDynamoDBFullAccess'),
                ManagedPolicy.from_aws_managed_policy_name('AWSLambda_FullAccess'),
            ],
        )

    def _create_api_gateway_rest(self, app_name, apig_role):
        file_api = RestApi(
            scope=self,
            id=f'{app_name}-FILE-API',
            deploy_options=StageOptions(
                logging_level=MethodLoggingLevel.INFO,
                # in console this is Stages -> Logs/Tracing -> Log full requests/responses data
                # may want to turn off later
                data_trace_enabled=True,
            ),
            binary_media_types=[
                'application/pdf',
                'audio/mpeg',
                'image/jpeg',
                'image/png',
            ],
        )

        bucket_resource = file_api.root.add_resource('{bucket}')
        key_resource = bucket_resource.add_resource('{key}')
        key_resource.add_method(
            http_method='PUT',
            integration=AwsIntegration(
                service='s3',
                path='{bucket}/{key}',
                integration_http_method='PUT',
                options=IntegrationOptions(
                    credentials_role=apig_role,
                    request_parameters={
                        'integration.request.path.bucket': 'method.request.path.bucket',
                        'integration.request.path.key': 'method.request.path.key',
                    },
                    integration_responses=[
                        IntegrationResponse(
                            status_code='200',
                            response_parameters={
                                'method.response.header.Content-Type': 'integration.response.header.Content-Type',
                                'method.response.header.Access-Control-Allow-Origin': "'*'",
                            },
                        ),
                        IntegrationResponse(
                            status_code='400',
                            selection_pattern='4\d{2}',
                        ),
                        IntegrationResponse(
                            status_code='500',
                            selection_pattern='5\d{2}',
                        ),
                    ]
                )
            ),
            request_parameters={
                'method.request.header.Content-Type': False,
                'method.request.path.bucket': True,
                'method.request.path.key': True,
            },
            method_responses=[
                MethodResponse(
                    status_code='200',
                    response_parameters={
                        'method.response.header.Content-Type': True,
                        'method.response.header.Access-Control-Allow-Origin': True,
                    },
                ),
                MethodResponse(
                    status_code='400',
                ),
                MethodResponse(
                    status_code='500',
                ),
            ],
        )
        key_resource.add_method(
            http_method='GET',
            integration=AwsIntegration(
                service='s3',
                path='{bucket}/{key}',
                integration_http_method='GET',
                options=IntegrationOptions(
                    credentials_role=apig_role,
                    request_parameters={
                        'integration.request.path.bucket': 'method.request.path.bucket',
                        'integration.request.path.key': 'method.request.path.key',
                    },
                    integration_responses=[
                        IntegrationResponse(
                            status_code='200',
                            response_parameters={
                                'method.response.header.Content-Type': 'integration.response.header.Content-Type',
                                'method.response.header.Access-Control-Allow-Origin': "'*'",
                            },
                        ),
                        IntegrationResponse(
                            status_code='400',
                            selection_pattern='4\d{2}',
                        ),
                        IntegrationResponse(
                            status_code='500',
                            selection_pattern='5\d{2}',
                        ),
                    ]
                )
            ),
            request_parameters={
                'method.request.header.Content-Type': False,
                'method.request.path.bucket': True,
                'method.request.path.key': True,
            },
            method_responses=[
                MethodResponse(
                    status_code='200',
                    response_parameters={
                        'method.response.header.Content-Type': True,
                        'method.response.header.Access-Control-Allow-Origin': True,
                    },
                ),
                MethodResponse(
                    status_code='400',
                ),
                MethodResponse(
                    status_code='500',
                ),
            ],
        )
        key_resource.add_method(
            http_method='OPTIONS',
            integration=MockIntegration(
                request_templates={ 'application/json': '{ "statusCode": 200 }' },
                integration_responses=[
                    IntegrationResponse(
                        status_code='200',
                        response_parameters={
                            'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                            'method.response.header.Access-Control-Allow-Methods': "'GET,OPTIONS,PUT'",
                            'method.response.header.Access-Control-Allow-Origin': "'*'",
                        },
                    ),
                ],
            ),
            request_parameters={
                'method.request.path.bucket': True,
                'method.request.path.key': True,
            },
            method_responses=[
                MethodResponse(
                    status_code='200',
                    response_parameters={
                        'method.response.header.Access-Control-Allow-Headers': True,
                        'method.response.header.Access-Control-Allow-Methods': True,
                        'method.response.header.Access-Control-Allow-Origin': True,
                    },
                ),
            ],
        )

        return file_api

    # TODO use aws_cdk.aws_apigatewayv2.WebSocketApi instead, when it becomes usable
    def _configure_api_gateway_web_socket(self, app_name, conversion_api, apig_role, convert_images_to_text_func):
        conversion_integ = CfnIntegration(
            scope=self,
            id=f'{app_name}-WS-API-INTEGRATION',
            api_id=conversion_api.ref,
            credentials_arn=apig_role.role_arn,
            integration_type='AWS',
            integration_uri=f'arn:aws:apigateway:{Aws.REGION}:lambda:path/2015-03-31/functions/{convert_images_to_text_func.function_arn}/invocations',
            template_selection_expression='\$default',
            request_templates={
                '$default': f"""
                    {{
                        "Bucket": "$input.path('$.Bucket')",
                        "Key": "$input.path('$.Key')",
                        "{app_name}JobId": "$input.path('$.{app_name}JobId')",
                        "UserId": "$input.path('$.UserId')",
                        "ConnectionId": "$context.connectionId"
                    }}
                """
            },
        )
        conversion_route = CfnRoute(
            scope=self,
            id=f'{app_name}-WS-API-ROUTE',
            api_id=conversion_api.ref,
            route_key='$default',
            authorization_type=None,
            target=f'integrations/{conversion_integ.ref}',
            route_response_selection_expression='$default',
        )
        conversion_integ_response = CfnIntegrationResponse(
            scope=self,
            id=f'{app_name}-WS-API-INTEGRATION_RESPONSE',
            api_id=conversion_api.ref,
            integration_id=conversion_integ.ref,
            integration_response_key='$default',
        )
        CfnRouteResponse(
            scope=self,
            id=f'{app_name}-WS-API-ROUTE_RESPONSE',
            api_id=conversion_api.ref,
            route_id=conversion_route.ref,
            route_response_key='$default',
        )
        self.conversion_stage = CfnStage(
            scope=self,
            id=f'{app_name}-WS-API-STAGE',
            api_id=conversion_api.ref,
            stage_name='prod',
            auto_deploy=True,
            default_route_settings=CfnStage.RouteSettingsProperty(
                data_trace_enabled=True,
                detailed_metrics_enabled=True,
                logging_level='INFO',
            )
        )
        self.conversion_stage.add_depends_on(conversion_route)
        self.conversion_stage.add_depends_on(conversion_integ_response)

    def _create_dynamo_db_table(self, app_name):
        table = Table(
            self,
            id=f'{app_name}-DYNAMODB-TABLE',
            table_name=f'{app_name}Jobs',
            partition_key=Attribute(name=f'{app_name}JobId', type=AttributeType.STRING),
            billing_mode=BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )
        table.add_global_secondary_index(
            partition_key=Attribute(name='TextractJobId', type=AttributeType.STRING),
            index_name='TextractJobId',
        )
        table.add_global_secondary_index(
            partition_key=Attribute(name='PollyJobId', type=AttributeType.STRING),
            index_name='PollyJobId',
        )
