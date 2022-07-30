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


HUMAN_READABLE_TEMPLATE = 'Infrastructure Source: __SOURCE__\nResource Identifier: __ARN__\nEvent: __EVENT__'


def extract_message_from_record(record: dict)->str:
    logger.info('record={}'.format(json.dumps(record, default=str)))
    if 'body' in record:
        body = json.loads(record['body'])
        logger.info('body={}'.format(json.dumps(body, default=str)))
        if 'Message' in body:
            message_raw = body['Message']
            logger.info('message={}'.format(json.dumps(message_raw, default=str)))
            return message_raw
        else:
            raise Exception('Expected "Message" key')
    else:
        raise Exception('Expected "body" key')


def prepare_human_readable_message(origin_message: str)->str:
    hm = copy.deepcopy(HUMAN_READABLE_TEMPLATE)
    logger.info('origin_message={}'.format(origin_message))
    values = origin_message.split(',', 2)
    logger.info('values={}'.format(values))
    aws_source = values[0]
    arn = values[1]
    state = values[2]
    logger.info('aws_source={}'.format(aws_source))
    logger.info('arn={}'.format(arn))
    logger.info('state={}'.format(state))
    aws_source = aws_source.replace('.', ' ').upper()
    hm = hm.replace('__SOURCE__', aws_source)
    if aws_source.lower().endswith('ec2') is True:
        instance_sate_data = json.loads(state)
        hm = hm.replace('__EVENT__', 'New State: {}'.format(instance_sate_data['state'].upper()))
        arn_components = arn.split(':')
        instance_id = arn_components[5]
        aws_region = arn_components[3]
        if len(aws_region) < 2:
            aws_region = 'unknown or global resource'
        if '/' in instance_id:
            instance_id = instance_id.split('/')[-1]
        hm = hm.replace('__ARN__', 'Instance ID "{}" in AWS Region "{}"'.format(instance_id, aws_region))
    else:
        hm = hm.replace('__ARN__', arn)
        hm = hm.replace('__EVENT__', 'Source cannot yet be converted to a more human readable format. RAW_DATA: {}'.format(state))
    return hm


def handler(event, context):
    logger.info('event={}'.format(json.dumps(event, default=str)))
    client = boto3.client('sns')
    target_sns_topic = os.getenv('TOPIC_ARN', None)
    if target_sns_topic is None:
        raise Exception('Environment variable TOPIC_ARN must be set')

    if 'Records' in event:
        for record in event['Records']:
            message = extract_message_from_record(record=record)
            human_readable_message = prepare_human_readable_message(origin_message=message)
            logger.info('Sending message to SNS Topic OrgResourceEventsNotificationTopic: {}'.format(human_readable_message))
            response = client.publish(
                TopicArn=target_sns_topic,
                Message=human_readable_message,
                Subject='AWS Resource State Change Event'
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
