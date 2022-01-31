# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
import datetime
import os
import pathlib

import img2pdf


APP_NAME = os.environ['APP_NAME']
TEXTRACT_SERVICE_ROLE_ARN = os.environ['TEXTRACT_SERVICE_ROLE']

CONVERSION_API_ENDPOINT = os.environ['CONVERSION_API_ENDPOINT']
CONVERSION_API_REGION = os.environ['CONVERSION_API_REGION']
apig_management_client = boto3.client(
    'apigatewaymanagementapi',
    endpoint_url=f'https://{CONVERSION_API_ENDPOINT}.execute-api.{CONVERSION_API_REGION}.amazonaws.com/prod',
)

ddb_table = boto3.resource('dynamodb').Table(f'{APP_NAME}Jobs')

textract_client = boto3.client(
    service_name = 'textract',
    region_name = CONVERSION_API_REGION,
)

s3_client = boto3.client('s3')


def lambda_handler(event, context):
    try:
        invoke_textract(event)
    except Exception:
        notify_user('ERROR - Failed to convert file', event['ConnectionId'])
        raise


def invoke_textract(event):
    start_time_utc = datetime.datetime.utcnow().isoformat()

    sns_topic_arn = os.environ[f'{APP_NAME}_TEXTRACT_SNS_TOPIC_ARN']

    notify_user('Invoking Textract', event['ConnectionId'])

    app_job_id = event[f'{APP_NAME}JobId']
    bucket_name = event['Bucket']
    input_file_s3_key = convert_to_pdf(event['Key'], app_job_id, bucket_name)

    resp = textract_client.start_document_text_detection(
        DocumentLocation={
            'S3Object': {
                'Bucket': bucket_name,
                'Name': input_file_s3_key,
            },
        },
        NotificationChannel={
            'RoleArn': TEXTRACT_SERVICE_ROLE_ARN,
            'SNSTopicArn': sns_topic_arn,
        },
    )

    ddb_table.put_item(
        Item={
            f'{APP_NAME}JobId': app_job_id,
            'UserId': event['UserId'],
            'StartTime': start_time_utc,
            'ConnectionId':  event['ConnectionId'],
            'TextractJobId': resp['JobId'],
            'InputFile': os.path.basename(input_file_s3_key),
        },
    )

    return resp

def convert_to_pdf(input_file_s3_key, app_job_id, bucket_name):
    input_file_suffix_lower = pathlib.PurePath(input_file_s3_key).suffix.lower()

    # TODO use S3 object type instead?
    if input_file_suffix_lower == '.pdf':
        return input_file_s3_key
    elif input_file_suffix_lower in ('.jpg', '.png'):
        new_input_file_s3_key = str(pathlib.PurePath(input_file_s3_key).with_suffix('.pdf'))

        s3_resp = s3_client.get_object(
            Bucket=bucket_name,
            Key=input_file_s3_key,
        )
        with open(f'/tmp/input-file-{app_job_id}.pdf', 'wb') as f:
	        f.write(img2pdf.convert(s3_resp['Body']))

        s3_client.upload_file(
            Filename=f'/tmp/input-file-{app_job_id}.pdf',
            Bucket=bucket_name,
            Key=new_input_file_s3_key,
        )
        return new_input_file_s3_key
    else:
        raise ValueError(f'Input file type not supported: {input_file_suffix_lower}')

def notify_user(message, connection_id):
    apig_response = apig_management_client.post_to_connection(
        Data=message,
        ConnectionId=connection_id,
    )
