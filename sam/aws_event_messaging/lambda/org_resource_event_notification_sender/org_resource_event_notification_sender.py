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
    hm = hm.replace('__SOURCE__', aws_source)
    hm = hm.replace('__ARN__', arn)
    if aws_source == 'aws.ec2':
        instance_sate_data = json.loads(state)
        hm = hm.replace('__EVENT__', 'New Instance State: {}'.format(instance_sate_data['state'].upper()))
    else:
        hm = hm.replace('__EVENT__', 'RAW_DATA: {}'.format(state))
    return hm


def handler(event, context):
    """Lambda function to handle events from AwsServiceEventsQueue and send standardized event messages to OrgResourceEventsTopic

    Example event:

    .. highlight:: json
    .. code-block:: json

        {
    "Records": [
        {
            "messageId": "oooooooooo",
            "receiptHandle": "oooooooooo",
            "body": "{\n  \"Type\" : \"Notification\",\n  \"MessageId\" : \"oooooooooo\",\n  \"TopicArn\" : \"arn:aws:sns:eu-central-1:0000000000:aws-event-messaging-stack-OrgResourceEventsTopic-oooooooooo\",\n  \"Subject\" : \"AWS Event\",\n  \"Message\" : \"aws.ec2,arn:aws:ec2:eu-central-1:0000000000:instance/i-0b4c854ee43718713,{\\\"instance-id\\\": \\\"i-0b4c854ee43718713\\\", \\\"state\\\": \\\"running\\\"}\",\n  \"Timestamp\" : \"2022-07-30T09:48:08.637Z\",\n  \"SignatureVersion\" : \"1\",\n  \"Signature\" : \"oooooooooo\",\n  \"SigningCertURL\" : \"oooooooooo\",\n  \"UnsubscribeURL\" : \"oooooooooo\"\n}",
            "attributes": {
                "ApproximateReceiveCount": "1",
                "SentTimestamp": "1659174488670",
                "SenderId": "oooooooooo",
                "ApproximateFirstReceiveTimestamp": "1659180249279"
            },
            "messageAttributes": {},
            "md5OfBody": "oooooooooo",
            "eventSource": "aws:sqs",
            "eventSourceARN": "arn:aws:sqs:eu-central-1:0000000000:aws-event-messaging-stack-OrgResourceEventsMessagingQueue-oooooooooo",
            "awsRegion": "eu-central-1"
        }
    ]
}

    """

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
