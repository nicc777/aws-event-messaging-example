import json
import boto3
import os
import logging
import copy

logger = logging.getLogger()
if os.getenv('DEBUG', None) is not None:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)


def extract_message_from_record(record: dict)->dict:
    logger.info('record={}'.format(json.dumps(record, default=str)))
    if 'Sns' in record:
        return {
            'Subject': record['Sns']['Subject'],
            'Body': record['Sns']['Message'],
        }
    else:
        raise Exception('Expected "Sns" key')


def handler(event, context):

    logger.info('event={}'.format(json.dumps(event, default=str)))
    client = boto3.client('ses')
    sender = os.getenv('FROM_EMAIL_ADDR')
    recipient = os.getenv('TO_EMAIL_ADDR')
    if 'NOT_SET' in sender or 'NOT_SET' in recipient:
        raise Exception('Cannot send emails - sender and recipients have not been set')
    
    if 'Records' in event:
        for record in event['Records']:
            message = extract_message_from_record(record=record)
            response = client.send_email(
                Source=sender,
                Destination={'ToAddresses': [recipient,]},
                Message={
                    'Subject': {'Data': message['Subject']},
                    'Body': {'Text': {'Data': message['Body']}}
                },
                ReplyToAddresses=[sender,]
            )
            logger.info('response={}'.format(response))

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "event handled",
        }),
    }
