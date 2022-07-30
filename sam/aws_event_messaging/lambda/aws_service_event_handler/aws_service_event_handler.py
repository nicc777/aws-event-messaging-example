import json
import boto3
import os
import logging

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
                    "body": "{\n  \"Type\" : \"Notification\",\n  \"MessageId\" : \"oooooooooo\",\n  \"TopicArn\" : \"arn:aws:sns:eu-central-1:000000000000:aws-event-messaging-stack-AwsServiceEventsTopic-oooooooooo\",\n  \"Message\" : \"{\\\"version\\\":\\\"0\\\",\\\"id\\\":\\\"oooooooooo\\\",\\\"detail-type\\\":\\\"EC2 Instance State-change Notification\\\",\\\"source\\\":\\\"aws.ec2\\\",\\\"account\\\":\\\"000000000000\\\",\\\"time\\\":\\\"2022-07-30T08:40:32Z\\\",\\\"region\\\":\\\"eu-central-1\\\",\\\"resources\\\":[\\\"arn:aws:ec2:eu-central-1:000000000000:instance/i-0b4c854ee43718713\\\"],\\\"detail\\\":{\\\"instance-id\\\":\\\"i-0b4c854ee43718713\\\",\\\"state\\\":\\\"running\\\"}}\",\n  \"Timestamp\" : \"2022-07-30T08:40:32.470Z\",\n  \"SignatureVersion\" : \"1\",\n  \"Signature\" : \"oooooooooo\",\n  \"SigningCertURL\" : \"oooooooooo\",\n  \"UnsubscribeURL\" : \"oooooooooo\"\n}",
                    "attributes": {
                        "ApproximateReceiveCount": "1",
                        "SentTimestamp": "1659170432500",
                        "SenderId": "oooooooooo",
                        "ApproximateFirstReceiveTimestamp": "1659170432504"
                    },
                    "messageAttributes": {},
                    "md5OfBody": "oooooooooo",
                    "eventSource": "aws:sqs",
                    "eventSourceARN": "arn:aws:sqs:eu-central-1:000000000000:aws-event-messaging-stack-AwsServiceEventsQueue-oooooooooo",
                    "awsRegion": "eu-central-1"
                }
            ]
        }

    The body record includes a Message attribute with it's contents in JSON below:

    .. highlight:: json
    .. code-block:: json

        {
            "version": "0",
            "id": "oooooooooo",
            "detail-type": "EC2 Instance State-change Notification",
            "source": "aws.ec2",
            "account": "000000000000",
            "time": "2022-07-30T08: 40: 32Z",
            "region": "eu-central-1",
            "resources": [
                "arn:aws:ec2:eu-central-1:000000000000:instance/i-oooooooooo"
            ],
            "detail": {
                "instance-id": "i-oooooooooo",
                "state": "running"
            }
        }
    """

    logger.info('event={}'.format(json.dumps(event, default=str)))
    target_sns_topic = os.getenv('TOPIC_ARN', None)
    if target_sns_topic is None:
        raise Exception('Environment variable TOPIC_ARN must be set')

    if 'Records' in event:
        for record in event['Records']:
            message = extract_message_from_record(record=record)
    else:
        raise Exception('Event does not contain key "Records"')

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "event handled",
        }),
    }
