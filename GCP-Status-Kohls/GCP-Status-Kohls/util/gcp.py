import googleapiclient.discovery
from pprint import pprint
from googleapiclient import discovery
from google.oauth2 import service_account
from oauth2client.client import GoogleCredentials
import logging
import json
from flask import jsonify
import requests
from datetime import datetime, tzinfo, timedelta
from pytz import timezone
from google.auth import app_engine
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from datetime import datetime

# service account details

PROJECT_ID = 'cloud-migration-solution'
region = 'us-central1'
filter_zone = ("name:" + region + "*")
credentials = GoogleCredentials.get_application_default()
service = discovery.build('compute', 'v1', credentials=credentials, cache_discovery=False)



# service = discovery.build('compute', 'v1', cache_discovery=False)


def get_list_of_instances(PROJECT_ID, filter_zone, access_token, api_key):
    print ("Function is executing")
    print (access_token)
    zones_request = service.zones().list(project=PROJECT_ID, filter=filter_zone)
    zones_response = zones_request.execute()
    items = zones_response["items"]
    instance_list = []
    for item in items:
        zone = item['description']
        request = service.instances().list(project=PROJECT_ID, zone=zone)
        try:
            response = request.execute()
            for instance in response['items']:
                inst_status = instance['status']
                inst_name = instance['name']
                inst_id = instance['id']
                inst_zone = zone
                if (inst_status == "TERMINATED"):
                    data = {
                        "filter": (
                                    "resource.type: gce_instance AND resource.labels.instance_id=" + inst_id + " AND protoPayload.methodName: stop"),
                        "projectIds": [PROJECT_ID],
                        "orderBy": "timestamp desc",
                        "pageSize": 1
                    }
                elif (inst_status == "RUNNING"):
                    data = {
                        "filter": (
                                    "resource.type: gce_instance AND resource.labels.instance_id=" + inst_id + " AND protoPayload.methodName: start"),
                        "projectIds": [PROJECT_ID],
                        "orderBy": "timestamp desc",
                        "pageSize": 1
                    }
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    'Authorization': "Bearer {0}".format(access_token),
                }
                appurl = ('https://logging.googleapis.com/v2/entries:list?key=' + api_key)
                try:
                    response = requests.post(appurl, headers=headers, json=data)
                    json_response = response.json()
                    print (json_response)
                    user = (json_response['entries'][0]['protoPayload']['authenticationInfo']['principalEmail'])
                    time = (json_response['entries'][0]['timestamp'])
                    time = (json_response['entries'][0]['timestamp'])
                    date_str = time
                    print("date_str   : ", date_str)
                    datetime_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
                    print("datetime_obj   : ", datetime_obj)
                    time = datetime_obj.replace(tzinfo=timezone('EST'))
                    time = datetime_obj - timedelta(hours=5, minutes=0)
                    print("timeeeeeee : ", time)
                    time = time.replace(second=0, microsecond=0)
                    print(time)
                except:
                    pass
                    user = ""
                    time = ""
                instance_list.append(
                    {"name": inst_name, "zone": inst_zone, "status": inst_status, "user": user, "time": time})
        except:
            pass
    print (instance_list)
    return instance_list


def start_instance(zone, instance_name):
    try:
        requests = service.instances().start(project=PROJECT_ID, zone=zone, instance=instance_name)
        response = requests.execute()
        pprint(response)
        print(instance_name, "Successfully Running")
        return json.dumps(response)

    except:
        return json.dumps({"ERROR": 1, "description": "not found"})


def stop_instance(zone, instance_name):
    try:
        requests = service.instances().stop(project=PROJECT_ID, zone=zone, instance=instance_name)
        response = requests.execute()
        pprint(response)
        print(instance_name, "Successfully Stopped")
        return json.dumps(response)

    except:
        return json.dumps({"ERROR": 1, "description": "not found"})









