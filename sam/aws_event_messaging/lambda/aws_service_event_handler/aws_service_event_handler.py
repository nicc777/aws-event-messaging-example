import json
import boto3
import os
import logging


logger = logging.getLogger()
if os.getenv('DEBUG', None) is not None:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)


def handler(event, context):

    logger.info('event={}'.format(json.dumps(event, default=str)))
    target_sns_topic = os.getenv('TOPIC_ARN', None)
    if target_sns_topic is None:
        raise Exception('Environment variable TOPIC_ARN must be set')

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "event handled",
        }),
    }
