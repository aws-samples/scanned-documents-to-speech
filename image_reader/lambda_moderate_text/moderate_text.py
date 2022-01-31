import boto3
import os


# please use only lower-case for now
undesirable_words = set()

CONVERSION_API_ENDPOINT = os.environ['CONVERSION_API_ENDPOINT']
CONVERSION_API_REGION = os.environ['CONVERSION_API_REGION']
apig_management_client = boto3.client(
    'apigatewaymanagementapi',
    endpoint_url=f'https://{CONVERSION_API_ENDPOINT}.execute-api.{CONVERSION_API_REGION}.amazonaws.com/prod',
)


def lambda_handler(event, context):
    text = event['Payload']['Text']
    connection_id = event['Payload']['ConnectionId']

    all_words = set()
    for line in text.split('\n'):
        all_words |= {word.lower() for word in line.split() if word}

    if undesirable_words & all_words:
        notify_user('ERROR - Text moderation failed', connection_id)
        raise ValueError('ERROR - Text moderation failed')
    else:
        notify_user('Text moderation succeeded', connection_id)

def notify_user(message, connection_id):
    apig_response = apig_management_client.post_to_connection(
        Data=message,
        ConnectionId=connection_id,
    )
