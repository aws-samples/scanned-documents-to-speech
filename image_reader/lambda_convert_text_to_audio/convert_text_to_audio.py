# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
import os


APP_NAME = os.environ['APP_NAME']
S3_BUCKET = os.environ['S3_BUCKET']

polly_client = boto3.client('polly')
ddb_table = boto3.resource('dynamodb').Table(f'{APP_NAME}Jobs')

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
    input_file = event['Payload']['InputFile']

    sns_topic_arn = os.environ[f'{APP_NAME}_POLLY_SNS_TOPIC_ARN']

    invoke_polly(text, user_id, app_job_id, connection_id, input_file, sns_topic_arn)

def invoke_polly(text, user_id, app_job_id, connection_id, input_file, sns_topic_arn):
    notify_user('Invoking Polly', connection_id)
    resp = polly_client.start_speech_synthesis_task(
        OutputFormat='mp3',
        OutputS3BucketName=S3_BUCKET,
        OutputS3KeyPrefix=f'{user_id}/{app_job_id}/audio/audio',
        Text=text,
        VoiceId='Ivy',
        SnsTopicArn=sns_topic_arn,
    )

    ddb_table.update_item(
        Key={
            f'{APP_NAME}JobId': app_job_id,
        },
        UpdateExpression='SET PollyJobId = :polly_job_id',
        ExpressionAttributeValues={
            ':polly_job_id': resp['SynthesisTask']['TaskId']
        },
        ReturnValues='ALL_NEW',
    )

    notify_user(f'Polly (Lambda) response: {resp}', connection_id)

def notify_user(message, connection_id):
    apig_response = apig_management_client.post_to_connection(
        Data=message,
        ConnectionId=connection_id,
    )
