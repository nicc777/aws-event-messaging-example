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


MESSAGE_TEMPLATE = '__EVENT_SOURCE__,__RESOURCE_ID__,__EVENT__'


def extract_message_from_record(record: dict)->dict:
    logger.info('record={}'.format(json.dumps(record, default=str)))
    if 'body' in record:
        body = json.loads(record['body'])
        logger.info('body={}'.format(json.dumps(body, default=str)))
        if 'Message' in body:
            message = json.loads(body['Message'])
            logger.info('message={}'.format(json.dumps(message, default=str)))
            return message
        else:
            raise Exception('Expected "Message" key')
    else:
        raise Exception('Expected "body" key')


def build_standard_event_message(origin_message: dict)->list:
    messages = list()
    for resource in origin_message['resources']:
        message = copy.deepcopy(MESSAGE_TEMPLATE)
        message = message.replace('__EVENT_SOURCE__', origin_message['source'])
        message = message.replace('__RESOURCE_ID__', resource)
        message = message.replace('__EVENT__', json.dumps(origin_message['detail']))
        logger.info('Generated message: {}'.format(message))
        messages.append(message)
    return messages


def handler(event, context):
    logger.info('event={}'.format(json.dumps(event, default=str)))
    client = boto3.client('sns')
    target_sns_topic = os.getenv('TOPIC_ARN', None)
    if target_sns_topic is None:
        raise Exception('Environment variable TOPIC_ARN must be set')

    if 'Records' in event:
        for record in event['Records']:
            message = extract_message_from_record(record=record)
            for event_msg in build_standard_event_message(origin_message=message):
                logger.info('Sending message to SNS Topic OrgResourceEventsTopic: {}'.format(event_msg))
                response = client.publish(
                    TopicArn=target_sns_topic,
                    Message=event_msg,
                    Subject='AWS Event'
                )
                logger.info('response={}'.format(response))
    else:
        raise Exception('Event does not contain key "Records"')

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "event handled",
        }),
    }
