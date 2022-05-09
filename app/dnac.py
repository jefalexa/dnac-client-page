# Modules import
import requests
from requests.auth import HTTPBasicAuth
import sys
import datetime as dt
import json

# Disable SSL warnings. Not needed in production environments with valid certificates
import urllib3
urllib3.disable_warnings()


# URLs
AUTH_URL = '/dna/system/api/v1/auth/token'
CLIENT_DETAILS = '/dna/intent/api/v1/client-detail'
USER_DETAILS = '/dna/intent/api/v1/user-enrichment-details'
        
# Get Authentication token
def get_dnac_jwt_token():
    response = requests.post(BASE_URL + AUTH_URL,
                             auth=HTTPBasicAuth(USERNAME, PASSWORD),
                             verify=False)
    token = response.json()['Token']
    return token



# Setup Credentials
with open('creds.json', 'r') as file: 
    dnac_creds = json.load(file)

BASE_URL = dnac_creds['BASE_URL']
USERNAME = dnac_creds['USERNAME']
PASSWORD = dnac_creds['PASSWORD']

# obtain the Cisco DNA Center Auth Token
token = get_dnac_jwt_token()
headers = {'X-Auth-Token': token, 'Content-Type': 'application/json'}


# Get client details
def get_client_details(headers, timestamp, macAddress):
    timestamp = str(int(round(timestamp * 1000, 0)))
    response = requests.get(BASE_URL + CLIENT_DETAILS,
                            params={'timestamp':timestamp, 'macAddress':macAddress},
                            headers=headers, verify=False)
    return response.json()


def get_client_details_history(headers, macAddress, interval, count):
    timestamp = dt.datetime.timestamp(dt.datetime.now())
    count = int(round(count, 0))
    result = {}
    
    response = get_client_details(headers, timestamp, macAddress)
    result[timestamp] = response

    for x in range(1, count):
        timestamp -= interval
        response = get_client_details(headers, timestamp, macAddress)
        result[timestamp] = response
        
    return(result) 
        


# Get user details
def get_user_details(headers, entity_type, entity_value):
    headers['entity_type'] = entity_type
    headers['entity_value'] = entity_value
    response = requests.get(BASE_URL + USER_DETAILS,
                            headers=headers, verify=False)
    return response.json()
    

def get_clients(entity_type, entity_value):
    results = get_user_details(headers, entity_type, entity_value)
    client_details_list = []

    # Get Details for Each Client
    interval = 60 * 5 # how often to sample in seconds
    count = 60 / 5 # how many samples to take 

    for client in results:
        mac_address = client['userDetails']['hostMac']
        results = get_client_details_history(headers, mac_address, interval, count)   
        client_details_list.append(results)

    return(client_details_list)
    

def proc_clients(client_details_list):
    client_details_list_display = []
    client_count = 0

    for client_instance in client_details_list:
        first_run = True
        client_count += 1
        client_historical_list = []
        for client_key, client_value in client_instance.items():
            client_instance_details = client_value['detail']
            client_historical_attribs = {'avgRssi':'', 'avgSnr':'', 'dataRate':'', 'txBytes':'', 'rxBytes':'', 'txLinkError':'', 'rxLinkError':''}
            if first_run:
                if client_instance_details['hostName']:
                    client_name = f'Client {client_count} - {client_instance_details["hostName"]}'
                else:
                    client_name = f'Client {client_count}'
                
                client_current_state = client_instance_details
                
                for hc in client_current_state['healthScore']:
                    if hc['healthType'] == 'OVERALL':
                        new_score = hc['score']

                client_current_state['healthScore'] = new_score
                    
                first_run = False
   
            ts = dt.datetime.strftime(dt.datetime.fromtimestamp(client_key), "%b %w - %-I:%M %p")
            
            for attrib in client_historical_attribs.keys():
                val = client_instance_details[attrib]
                try:
                    val = int(round(float(val), 0))
                except:
                    pass
                client_historical_attribs[attrib] = val

            client_historical_attribs['Timestamp'] = ts
            client_historical_list.append(client_historical_attribs)
        client_details_list_display.append({'client_name':client_name, 'client_current_state':client_current_state, 'client_historical_list':client_historical_list})
        
    return(client_details_list_display)


def get_client_details_display(entity_type, entity_value):
    try:
        client_details_list = get_clients(entity_type, entity_value)
        client_details_list_display = proc_clients(client_details_list)
        return(client_details_list_display)
    except:
        return([])

