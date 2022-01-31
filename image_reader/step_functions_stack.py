# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import pathlib

from aws_cdk.aws_apigatewayv2 import CfnApi
from aws_cdk.aws_iam import ManagedPolicy, Role, ServicePrincipal
from aws_cdk.aws_lambda import Code, Function, Runtime
from aws_cdk.aws_stepfunctions import JsonPath, StateMachine, Parallel
from aws_cdk.aws_stepfunctions_tasks import LambdaInvoke
from aws_cdk.core import Aws, Construct, Stack


TAG_NAME = 'app'


class StepFunctionsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, conversion_api: CfnApi, lambda_stack: Stack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        app_name = self.node.try_get_context('app-name')
        self.state_machine = self._create_state_machine(app_name, conversion_api, lambda_stack.retrieve_text_func, lambda_stack.store_text_func, lambda_stack.moderate_text_func, lambda_stack.convert_text_to_audio_func)

        # tag all resources with app_name
        self.tags.set_tag(TAG_NAME, app_name, apply_to_launched_instances=True)

    def _create_state_machine(self, app_name, conversion_api, retrieve_text_func, store_text_func, moderate_text_func, convert_text_to_audio_func):
        retrieve_text_lambda_invoke = LambdaInvoke(
            self,
            id=f'{app_name}-LambdaInvoke-RETRIEVE-TEXT',
            lambda_function=retrieve_text_func,
        )

        store_text_lambda_invoke = LambdaInvoke(
            self,
            id=f'{app_name}-LambdaInvoke-STORE-TEXT',
            lambda_function=store_text_func,
        )

        # TODO no need to retry for this one
        moderate_text_lambda_invoke = LambdaInvoke(
            self,
            id=f'{app_name}-LambdaInvoke-MODERATE-TEXT',
            lambda_function=moderate_text_func,
        )

        parallel_step = Parallel(
            self,
            id=f'{app_name}-PARALLEL',
            result_path=JsonPath.DISCARD,  # this sets ResultPath to null, making parallel_step use input as output
        )

        parallel_step.branch(
            store_text_lambda_invoke,
            moderate_text_lambda_invoke,
        )

        convert_text_to_audio_lambda_invoke = LambdaInvoke(
            self,
            id=f'{app_name}-LambdaInvoke-CONVERT-TEXT-TO-AUDIO',
            lambda_function=convert_text_to_audio_func,
        )

        state_machine_definition = retrieve_text_lambda_invoke.next(parallel_step).next(convert_text_to_audio_lambda_invoke)

        state_machine = StateMachine(
            self,
            id=f'{app_name}-STEP-FUNCTION',
            definition=state_machine_definition,
        )

        # moving this to the lambda stack would trigger a cyclic depenency error
        self.on_textract_ready_func = Function(
            self,
            id=f'{app_name}-LAMBDA-ON-TEXTRACT-READY',
            function_name=f'{app_name}-on-textract-ready',
            handler='on_textract_ready.lambda_handler',
            runtime=Runtime.PYTHON_3_7,
            code=Code.from_asset(str(pathlib.PurePath(__file__).parent / 'lambda_on_textract_ready')),
            environment={
                'APP_NAME': app_name,
                'CONVERSION_API_ENDPOINT': conversion_api.ref,
                'CONVERSION_API_REGION': Aws.REGION,
                f'{app_name}_STATE_MACHINE': state_machine.state_machine_arn,
            },
            role=Role(
                self,
                id=f'{app_name}-ON-TEXTRACT-READY-FUNC-ROLE',
                assumed_by=ServicePrincipal('lambda.amazonaws.com'),
                managed_policies=[
                    ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole'),
                    ManagedPolicy.from_aws_managed_policy_name('AmazonAPIGatewayInvokeFullAccess'),
                    ManagedPolicy.from_aws_managed_policy_name('AmazonDynamoDBReadOnlyAccess'),
                    ManagedPolicy.from_aws_managed_policy_name('AWSStepFunctionsFullAccess'),
                ],
            ),
        )
