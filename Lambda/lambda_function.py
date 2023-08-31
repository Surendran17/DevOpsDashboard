import json
import boto3
from datetime import datetime, timedelta
from google.cloud import monitoring_v3
from google.oauth2.service_account import Credentials
from google.protobuf.timestamp_pb2 import Timestamp

def lambda_handler(event, context):
    # Initialize AWS CloudWatch client
    client = boto3.client('cloudwatch')
    
    # Get the current date and time
    today = datetime.now()
    
    # Calculate the timedelta for one day
    one_day = timedelta(days=1)
    
    # Subtract one day from the current date
    yesterday = today - one_day
    
    # Retrieve AWS CloudWatch metric data
    response = client.get_metric_data(
        MetricDataQueries=[
            {
                'Id': 'metricCall',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/EC2',
                        'MetricName': 'CPUUtilization',
                        'Dimensions': [
                            {
                                'Name': 'InstanceId',
                                'Value': 'i-06fc4072adc5f71f6'
                            },
                        ]
                    },
                    'Period': 300,
                    'Stat': 'Average'
                },
            },
        ],
        StartTime=yesterday,
        EndTime=datetime.now(),
    )
    
    # Initialize AWS DynamoDB client
    client1 = boto3.client('dynamodb')
    
    format_string = '%Y-%m-%d %H:%M:%S'
    timestampList = response['MetricDataResults'][0]["Timestamps"]
    values = response['MetricDataResults'][0]["Values"]
    
    # Store AWS CloudWatch metric data in DynamoDB
    for timestamp, value in zip(timestampList, values):
        response1 = client1.put_item(
            TableName="dashboardStats",
            Item={
                'label': {"S": response['MetricDataResults'][0]["Label"]},
                'timestamp': {"S": timestamp.strftime(format_string)},
                'value': {"S": str(value)},
                'cp': {"S": "AWS"},
                'instanceId': {"S": "i-06fc4072adc5f71f6"}
            }
        )
    
    # Initialize AWS S3 client
    client1 = boto3.client('s3')
    
    # Retrieve Google Cloud credentials from S3
    response = client1.get_object(Bucket='gcpdeets', Key="groovy-karma-396614-8e7f292552f4.json")
    data = response['Body'].read()
    json_acct_info = json.loads(data)
    creds = Credentials.from_service_account_info(json_acct_info)
    
    # Initialize Google Cloud Monitoring client
    client = monitoring_v3.MetricServiceClient(credentials=creds)
    project_id = 'groovy-karma-396614'
    project_name = f"projects/{project_id}"
    
    # Set time interval for retrieving Google Cloud metric data
    current_time = datetime.now()
    start_time = (current_time - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    start_timestamp = Timestamp()
    start_timestamp.FromDatetime(start_time)
    current_timestamp = Timestamp()
    current_timestamp.FromDatetime(current_time)
    interval = monitoring_v3.TimeInterval(
        {
            "start_time": start_timestamp,
            "end_time": current_timestamp,
        }
    )
    
    # Retrieve Google Cloud metric time series
    results = client.list_time_series(
        request={
            "name": project_name,
            "filter": 'metric.type = "compute.googleapis.com/instance/cpu/utilization"',
            "interval": interval,
            "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
        }
    )
    
    # Store Google Cloud metric data in DynamoDB
    for time_series in results:
        metric_type = time_series.metric.type
        resource_type = time_series.resource.type
        labels = time_series.metric.labels
    
        for point in time_series.points:
            timestamp = point.interval.start_time
            value = point.value.double_value
            response1 = client1.put_item(
                TableName="dashboardStats",
                Item={
                    'label': {"S": "CPUUtilization"},
                    'timestamp': {"S": timestamp.strftime(format_string)},
                    'value': {"S": str(value)},
                    'cp': {"S": "GCP"},
                    'instanceId': {"S": "9111704565321745387"}
                }
            )
    
    return {
        'statusCode': 200,
        'body': json.dumps('Success!')
    }
