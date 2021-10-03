import boto3
import os
import json
import logging
import json
import decimal

'''
AWS Lambda Function to list all data. Requests come from Amazon API Gateway.
'''


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return int(obj)
        return super(DecimalEncoder, self).default(obj)


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def list_data():
    data = []
    dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-1')
    table = dynamodb.Table(os.getenv("TABLE_NAME"))
    scan_kwargs = {}
    done = False
    start_key = None
    while not done:
        if start_key:
            scan_kwargs['ExclusiveStartKey'] = start_key
        response = table.scan(**scan_kwargs)
        data.extend(response.get('Items'))
        start_key = response.get('LastEvaluatedKey', None)
        done = start_key is None
    return data


def handler(event, context):
    logger.info('get-options is called')
    data = list_data()
    logger.info('returning data ->{}'.format(data))
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
    }
    response = {"statusCode": 200, "headers": headers, "body": json.dumps(
        {"data": data}, cls=DecimalEncoder)}
    return response
