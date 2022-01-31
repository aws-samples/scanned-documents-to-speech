# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
import datetime
import json
import os
import uuid

from boto3.dynamodb.conditions import Key


APP_NAME = os.environ['APP_NAME']
ddb_table = boto3.resource('dynamodb').Table(f'{APP_NAME}Jobs')
sfn_client = boto3.client('stepfunctions')

CONVERSION_API_ENDPOINT = os.environ['CONVERSION_API_ENDPOINT']
CONVERSION_API_REGION = os.environ['CONVERSION_API_REGION']
apig_management_client = boto3.client(
    'apigatewaymanagementapi',
    endpoint_url=f'https://{CONVERSION_API_ENDPOINT}.execute-api.{CONVERSION_API_REGION}.amazonaws.com/prod',
)


def lambda_handler(event, context):

    textract_job_ids = []
    for textract_record in event['Records']:
        message = json.loads(textract_record['Sns']['Message'])
        job_id = message['JobId']
        status = message['Status']
        file_loc = message['DocumentLocation']['S3ObjectName']

        textract_job_ids.append(job_id)

        print(f'JobId {job_id} has finished with status {status} for file {file_loc}.')

    if len(textract_job_ids) != 1:
        raise ValueError(f'Number of Textract job ids is not one: {textract_job_ids}.')

    ddb_response = ddb_table.query(
        IndexName='TextractJobId',
        KeyConditionExpression=Key('TextractJobId').eq(textract_job_ids[0]),
    )

    if ddb_response['ResponseMetadata']['HTTPStatusCode'] != 200:
        raise RuntimeError(f'Failed to query Dynamodb with TextractJobId {textract_job_ids[0]}.  DynamoDB response: {ddb_response}.')

    if ddb_response['Count'] != 1:
        raise ValueError(f'Number of DynamoDB items matching TextractJobId {textract_job_ids[0]} is not one.  DynamoDB response: {ddb_response}.')

    item = ddb_response['Items'][0]
    app_job_id = item[f'{APP_NAME}JobId']
    connection_id = item['ConnectionId']
    user_id = item['UserId']
    input_file = item['InputFile']

    state_machine_arn = os.environ[f'{APP_NAME}_STATE_MACHINE']
    sfn_client.start_execution(  # this returns immediately
        stateMachineArn=state_machine_arn,
        name=datetime.datetime.utcnow().strftime(f'%Y%m%d-%H%M%S-{uuid.uuid1()}'),
        input=f'''
            {{
                "TextractJobId": "{textract_job_ids[0]}",
                "{APP_NAME}JobId": "{app_job_id}",
                "ConnectionId": "{connection_id}",
                "UserId": "{user_id}",
                "InputFile": "{input_file}"
            }}
        ''',
    )

    apig_response = apig_management_client.post_to_connection(
        Data=f'Textract output is ready for App Job {app_job_id}',
        ConnectionId=connection_id,
    )
