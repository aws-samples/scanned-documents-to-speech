# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
import json
import os

from boto3.dynamodb.conditions import Key


APP_NAME = os.environ['APP_NAME']
ddb_table = boto3.resource('dynamodb').Table(f'{APP_NAME}Jobs')

CONVERSION_API_ENDPOINT = os.environ['CONVERSION_API_ENDPOINT']
CONVERSION_API_REGION = os.environ['CONVERSION_API_REGION']
apig_management_client = boto3.client(
    'apigatewaymanagementapi',
    endpoint_url=f'https://{CONVERSION_API_ENDPOINT}.execute-api.{CONVERSION_API_REGION}.amazonaws.com/prod',
)


def lambda_handler(event, context):

    polly_job_ids = []
    audio_output_file_uri = None
    for polly_record in event['Records']:
        message = json.loads(polly_record['Sns']['Message'])
        job_id = message['taskId']
        status = message['taskStatus']
        audio_output_file_uri = message['outputUri']

        polly_job_ids.append(job_id)

        print(f'JobId {job_id} has finished with status {status}.  Output: {audio_output_file_uri}.')

    if len(polly_job_ids) != 1:
        raise ValueError(f'Number of Polly job ids is not one: {polly_job_ids}.')

    ddb_response = ddb_table.query(
        IndexName='PollyJobId',
        KeyConditionExpression=Key('PollyJobId').eq(polly_job_ids[0]),
    )

    if ddb_response['ResponseMetadata']['HTTPStatusCode'] != 200:
        raise RuntimeError(f'Failed to query Dynamodb with PollyJobId {polly_job_ids[0]}.  DynamoDB response: {ddb_response}.')

    if ddb_response['Count'] != 1:
        raise ValueError(f'Number of DynamoDB items matching PollyJobId {polly_job_ids[0]} is not one.  DynamoDB response: {ddb_response}.')

    item = ddb_response['Items'][0]
    app_job_id = item[f'{APP_NAME}JobId']
    connection_id = item['ConnectionId']

    apig_response = apig_management_client.post_to_connection(
        Data=f'Polly output is ready for App Job {app_job_id}',
        ConnectionId=connection_id,
    )
    apig_response = apig_management_client.post_to_connection(
        Data=audio_output_file_uri,
        ConnectionId=connection_id,
    )
