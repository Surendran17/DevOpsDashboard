from datetime import datetime
import uuid
from flask import Flask,request, jsonify, make_response
import boto3
from flask_cors import CORS
from boto3.dynamodb.conditions import Attr

# DynamoDB Variables
metric_table = "dashboardStats"

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})   # Allow CORS for all sources 

# List all grants
@app.route("/metrics",methods = ['GET'])
def getMetrics():
    """The endpoint that will be used to fetch all metrics needed from dynamodb table 
    Route - /metrics
    Type - GET
    
    :return: List of metrics
    :rtype: list
    """        
    client = boto3.client(
    'dynamodb',
    region_name="us-east-1"
    )
    response = client.scan(
        TableName = metric_table
    )
    output = response["Items"]
    return make_response(jsonify(
                    message="Data fethced",
                    data=output),
                    200
                )
            
if __name__ == "__main__":
    app.run(host='0.0.0.0')
