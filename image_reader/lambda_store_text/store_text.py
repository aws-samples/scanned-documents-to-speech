# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
import os


APP_NAME = os.environ['APP_NAME']
S3_BUCKET = os.environ['S3_BUCKET']
s3_client = boto3.client('s3')

CONVERSION_API_ENDPOINT = os.environ['CONVERSION_API_ENDPOINT']
CONVERSION_API_REGION = os.environ['CONVERSION_API_REGION']
apig_management_client = boto3.client(
    'apigatewaymanagementapi',
    endpoint_url=f'https://{CONVERSION_API_ENDPOINT}.execute-api.{CONVERSION_API_REGION}.amazonaws.com/prod',
)


def lambda_handler(event, context):
    text = event['Payload']['Text']
    user_id = event['Payload']['UserId']
    app_job_id = event['Payload'][f'{APP_NAME}JobId']
    connection_id = event['Payload']['ConnectionId']

    s3_client.put_object(
        Body=text,
        Bucket=S3_BUCKET,
        Key=f'{user_id}/{app_job_id}/text/text.txt',
    )

    apig_response = apig_management_client.post_to_connection(
        Data='Text stored to S3',
        ConnectionId=connection_id,
    )
