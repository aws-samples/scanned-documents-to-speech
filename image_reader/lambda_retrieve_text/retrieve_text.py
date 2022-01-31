# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
import os


CONFIDENCE_LIMIT = 80

APP_NAME = os.environ['APP_NAME']

CONVERSION_API_ENDPOINT = os.environ['CONVERSION_API_ENDPOINT']
CONVERSION_API_REGION = os.environ['CONVERSION_API_REGION']
apig_management_client = boto3.client(
    'apigatewaymanagementapi',
    endpoint_url=f'https://{CONVERSION_API_ENDPOINT}.execute-api.{CONVERSION_API_REGION}.amazonaws.com/prod',
)

textract_client = boto3.client(
    service_name = 'textract',
    region_name = CONVERSION_API_REGION,
)


def lambda_handler(event, context):
    textract_job_id = event['TextractJobId']
    connection_id = event['ConnectionId']

    extracted_lines = []
    textract_resp = textract_client.get_document_text_detection(
        JobId=textract_job_id,
    )
    if textract_resp['JobStatus'] == 'SUCCEEDED':
        for block in textract_resp['Blocks']:
            if block['BlockType'] == 'LINE' and block['Confidence'] >= CONFIDENCE_LIMIT:
                extracted_lines.append(block['Text'])
    else:
        raise RuntimeError(f'Textract job {textract_job_id} failed.')

    apig_response = apig_management_client.post_to_connection(
        Data='Text retrieved from Textract',
        ConnectionId=connection_id,
    )

    return {
        'TextractJobId': textract_job_id,
        'Text': '\n'.join(extracted_lines),
        f'{APP_NAME}JobId': event[f'{APP_NAME}JobId'],
        'ConnectionId': connection_id,
        'UserId': event['UserId'],
        'InputFile': event['InputFile'],
    }
