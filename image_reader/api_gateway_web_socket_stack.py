# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk.core import Construct, Stack
from aws_cdk.aws_apigatewayv2 import CfnApi


TAG_NAME = 'app'


class ApiGatewayWebSocketStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        app_name = self.node.try_get_context('app-name')

        self.conversion_api = self._create_api_gateway_web_socket(app_name)

        # tag all resources with app_name
        self.tags.set_tag(TAG_NAME, app_name, apply_to_launched_instances=True)

    # TODO use aws_cdk.aws_apigatewayv2.WebSocketApi instead, when it becomes usable
    def _create_api_gateway_web_socket(self, app_name):
        conversion_api = CfnApi(
            scope=self,
            id=f'{app_name}-CONVERSION-API',
            protocol_type='WEBSOCKET',
            route_selection_expression="$request.body.action",
            name=f'{app_name}-CONVERSION-API',
        )

        return conversion_api
