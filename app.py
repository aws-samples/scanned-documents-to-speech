#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import os
import shutil
import tempfile

from aws_cdk import core as cdk

from image_reader.api_gateway_web_socket_stack import ApiGatewayWebSocketStack
from image_reader.lambda_stack import LambdaStack
from image_reader.main_stack import MainStack
from image_reader.s3_stack import S3Stack
from image_reader.sns_stack import SnsStack
from image_reader.step_functions_stack import StepFunctionsStack
from image_reader.amplify_stack import AmplifyStack


def build_client_zip_file():
    shutil.make_archive('client', 'zip', 'client/')

def build_lambda_layer_zip_file():
    tmp_dir = tempfile.mkdtemp()
    shutil.copytree('.venv/lib', f'{tmp_dir}/python/lib/')
    shutil.make_archive(
        base_name='image_reader/lambda_convert_images_to_text_layer/img2pdf',
        format='zip',
        root_dir=tmp_dir,
        base_dir='python',
    )
    shutil.rmtree(tmp_dir)

def build_stacks():
    app = cdk.App()
    s3_stack = S3Stack(
        app,
        'image-reader-s3-stack',
    )
    sns_stack = SnsStack(
        app,
        'image-reader-sns-stack',
    )
    api_gateway_ws_stack = ApiGatewayWebSocketStack(
        app,
        'image-reader-api-gateway-web-socket-stack',
    )
    lambda_stack = LambdaStack(
        app,
        'image-reader-lambda-stack',
        s3_stack.s3_bucket,
        api_gateway_ws_stack.conversion_api,
        sns_stack.textract_topic,
        sns_stack.polly_topic,
    )
    step_functions_stack = StepFunctionsStack(
        app,
        'image-reader-step-functions-stack',
        api_gateway_ws_stack.conversion_api,
        lambda_stack,
    )
    MainStack(
        app,
        'image-reader-main-stack',
        api_gateway_ws_stack.conversion_api,
        lambda_stack.convert_images_to_text_func,
    )
    amplify_stack = AmplifyStack(
        app,
        'image-reader-amplify-stack',
    )

    sns_stack.add_textract_topic_subscription(step_functions_stack.on_textract_ready_func)
    sns_stack.add_polly_topic_subscription(lambda_stack.on_polly_ready_func)

    app.synth()

build_client_zip_file()
build_lambda_layer_zip_file()
build_stacks()
