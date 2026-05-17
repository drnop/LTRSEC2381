"""
For lab LTRSEC-2381.
Used when moving to a new section in the lab.
Moves devices in Cisco CyberVision PLC1, PLC2, HMI1 back to grup Plant.
Clear any ISE ANC policies.
Optionally reports progress to central website.
"""
from turtle import st
from urllib import response
from xml.etree.ElementTree import indent

import requests
import urllib3
import json
import time
import os
import sys

# Disable warnings for self-signed certificates (common in lab environments)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Configuration ---
# Define the file path (assumes it's in the same directory)
CONFIG_FILE = "creds.json"

try:
    with open(CONFIG_FILE, "r") as f:
        creds = json.load(f)

    # Populate variables from the JSON structure
    CYBERVISION_IP = creds["CYBERVISION_IP"]
    API_TOKEN = creds["API_TOKEN"]

    ISE_SERVER = creds["ISE_SERVER"]
    ISE_USERNAME = creds["ISE_USERNAME"]
    ISE_PASSWORD = creds["ISE_PASSWORD"]

except FileNotFoundError:
    print(f"[-] Critical Error: '{CONFIG_FILE}' missing. Execution halted.")
    sys.exit(1)
except json.JSONDecodeError:
    print(f"[-] Critical Error: '{CONFIG_FILE}' contains invalid JSON formatting.")
    sys.exit(1)
except KeyError as e:
    print(f"[-] Critical Error: Missing expected configuration key: {e}")
    sys.exit(1)

def get_headers():
    return {
        "x-token-id": API_TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

def get_group_id(group_name):
    """Generic helper to find an ID based on a 'label' or 'name' attribute."""
    url = f"https://{CYBERVISION_IP}/api/3.0/groups"
    try:
        response = requests.get(url, headers=get_headers(), verify=False)
        response.raise_for_status()
        data = response.json()
        # print(json.dumps(data,indent=4 ))
        for d in data:
            if d["label"] == group_name:
                #print("found group " + group_name + "id is " + d["id"])
                #print(json.dumps(d,indent=4))
                return d["id"]
    except Exception as e:
        print(f"Error fetching {group_name}: {e}")
        return None


def get_device_id(device_name):
    """Generic helper to find an ID based on a 'label' or 'name' attribute."""
    ms_per_hour = 3600 * 1000
    now_ms = int(time.time() * 1000)
    yesterday_ms = now_ms - (30* 24 * ms_per_hour)

    # API URL with time filters
    params = {
        "from": yesterday_ms,
        "to": now_ms,
        "size": 100 # Adjust based on network size
    }
    url = f"https://{CYBERVISION_IP}/api/3.0/devices"
    try:
        response = requests.get(url, headers=get_headers(), params=params, verify=False)
        response.raise_for_status()
        data = response.json()
        # print(json.dumps(data,indent=4))
        for d in data:
            if d["label"] == device_name:
                #print("Found " + device_name)
                #print(json.dumps(d,indent=4))
                #print("---------")
                return (d["id"])

    except Exception as e:
        print(f"Error fetching devices: {e}")
        return None



def move_devices_to_group(device_ids, target_group_uuid):

    payload = {
        "comments": "",
        "color": "#441e91",
        "criticalness": 3,
        "description": "",
        "deviceIds": device_ids,
        "label": "Plant",
        "locked": False,
        "parentId": "",
        "userProperties": []
    }
    # 1. Fetch the Device details to get its internal components
    URL = f"https://{CYBERVISION_IP}/api/3.0/groups/4af1f50c-1575-479f-bfea-fbfb4afc7d24"
    headers = {
        "x-token-id": f"{API_TOKEN}",
        "Content-Type": "application/json",
        "accept": "application/json"
    }

    try:
        response = requests.put(URL, headers=headers, json=payload,verify=False)
        if response.status_code in [200, 204]:
            print(f"Successfully moved ")
        else:
            print(f"Failed to moved")

    except Exception as e:
        print(f"An error occurred: {e}")

def cybervision_move_devices_to_plant():
    device_ids = []
    group_id = get_group_id("Plant")
    print("Group id for Plant is {}".format(group_id))

    device_id = get_device_id("PLC1")
    print("device_id PLC1 {}".format(device_id))
    device_ids.append(device_id)

    device_id = get_device_id("PLC2")
    device_ids.append(device_id)
    print("device_id PLC2 {}".format(device_id))

    device_id = get_device_id("HMI1")
    print("device_id HMI1 {}".format(device_id))
    device_ids.append(device_id)

    print("Moving devices {} to group {} ".format(str(device_ids),group_id))
    move_devices_to_group(device_ids,group_id)


def ise_clear_all_anc_endpoints():
    base_url = f"https://{ISE_SERVER}:9060/ers/config"
    auth = (ISE_USERNAME, ISE_PASSWORD)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    anc_url = f"{base_url}/ancendpoint"

    try:
        response = requests.get(anc_url, auth=auth, headers=headers, verify=False)
        response.raise_for_status()
        resources = response.json().get("SearchResult", {}).get("resources", [])

        if not resources:
            print("No endpoints found with ANC policies.")
            return

        for res in resources:
            detail_url = res['link']['href']
            detail_resp = requests.get(detail_url, auth=auth, headers=headers, verify=False)

            if detail_resp.status_code == 200:
                body = detail_resp.json()

                # Check for both possible keys: 'ErsAncEndpoint' or 'AncEndpoint'
                endpoint_data = body.get("ErsAncEndpoint") or body.get("AncEndpoint")

                if endpoint_data:
                    mac = endpoint_data.get("macAddress")
                    if mac:
                        print(f"MAC {mac} ANC policy will be cleared!")
                        addData = {"name":"macAddress",
                               "value":mac}
                        putdata = {"OperationAdditionalData" : {"additionalData" : []} }
                        putdata["OperationAdditionalData"]["additionalData"].append(addData)
                        clear_url = f"{base_url}/ancendpoint/clear"
                        #print(json.dumps(putdata))
                        clear_resp = requests.put(clear_url, auth=auth, headers=headers, json=putdata, verify=False)
                        if clear_resp.status_code == 204:
                            print(f"MAC {mac} ANC cleared!")
                        else:
                            print(f"{clear_resp.status_code}  | {clear_resp.text}" )

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

def report_progress(section_id):
    # Retrieve the persistent variables
    group_id = os.environ.get("GROUPID")
    post_url = os.environ.get("POSTURL")

    if not group_id or not post_url:
        print("Not posting. Configuration missing.")
        sys.exit(1)

    # Clean the URL to ensure no double slashes or missing protocol
    base_url = post_url.rstrip('/')
    """
    payload = {
        "group_id" : group_id,
        "section_id" : section_id
    }
    """
    base_url = f"{base_url}/{group_id}/{section_id}"
    print(f"Posting: {base_url}")

    try:
        response = requests.get(base_url,verify=False, timeout=10)
        response.raise_for_status()
        print(f"Response ({response.status_code}): {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to Post progress connect: {e}")

def get_valid_section_number():
    while True:
        # Prompt the user for input
        print("Choose the Next Section!")
        print("========================================")
        print("3 : Secure Firewall and Cyber Vision")
        print("4 : Splunk Enterprise and Cyber Vision")
        print("5 : Secure Equipment Access")
        print("6 : Secure Network Analytics and Cyber Vision")
        user_input = input("Please enter the number of the section you want to start (e.g. 2): ")

        try:
            # Convert the string input to an integer
            val = int(user_input)

            # Validate the range
            if 3 <= val <= 6:
                print(f"Verified: {val} is a great choice.")
                return val  # Exit the function with the valid number
            else:
                print(f"Out of range! '{val}' is not between 3 and 6. Try again.")

        except ValueError:
            # Handle cases where the user types letters or symbols
            print(f"Invalid input! '{user_input}' is not a number. Please enter digits only.")


def main():

    section_id = get_valid_section_number()
    cybervision_move_devices_to_plant()
    ise_clear_all_anc_endpoints()
    report_progress(section_id)

if __name__ == "__main__":
   main()
