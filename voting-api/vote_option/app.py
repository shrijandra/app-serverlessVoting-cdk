import boto3
import os
import json
from datetime import datetime
import logging
import json

'''
AWS Lambda Function to store data. Requests come from Amazon API Gateway.
'''

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def vote(vote_ID):
    logging.info("Vote an option")
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.getenv("TABLE_NAME"))
    table.update_item(
        Key={
            'VOTE_ID': vote_ID,
        },
        UpdateExpression='ADD votes :inc',
        ExpressionAttributeValues={
            ':inc': 1
        }
    )
    return True


def handler(event, context):
    logger.info(event)
    logger.info("Test")
    logger.info('store-data is called')
    data = json.loads(event['body'])
    status = vote(data['vote_ID'])
    response = {}
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
    }
    if status:
        response = {
            "statusCode": 200,
            "headers":headers,
            "body": json.dumps({
                "message": "success"
            }),
        }
    else:
        response = {
            "statusCode": 500,
            "headers":headers,
            "body": json.dumps({
                "message": "failed"
            }),
        }
    return response
