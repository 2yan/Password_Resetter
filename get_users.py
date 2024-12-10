# -*- coding: utf-8 -*-
"""
Created on Mon Dec  2 15:54:16 2024

@author: Rdrac
"""

import requests
import boto3
import json
import csv

API_VERSION = "3.18"
SECRET_ID = False
assert SECRET_ID
REGION = "us-west-2"


def get_secrets():
    return json.loads(boto3.client('secretsmanager', region_name=REGION)
                      .get_secret_value(SecretId=SECRET_ID)['SecretString'])




def api_request(base_url, path, method="GET", token=None, json_payload=None):
    if json_payload:
        headers = {"Accept": "application/json",
                   "Content-Type": "application/json"}
    else:
        headers = {"Accept": "application/json"}

    if token:
        headers["X-Tableau-Auth"] = token

    response = requests.request(method,
                                 f"{base_url}{path}",
                                 json=json_payload,
                                 headers=headers)
    return response.json()


def get_all_users(base_url, token, site_id):
    site_url = f"/sites/{site_id}"
    users = []
    page_number = 1  
    page_size = 1000  # Maximum allowed by Tableau API

    while True:
        path = f"{site_url}/users?pageSize={page_size}&pageNumber={page_number}"
        response = api_request(base_url, path, token=token)
        current_users = response.get("users", {}).get("user", [])
        users.extend(current_users)

        total_available = int(response.get("pagination", {}).get("totalAvailable", 0))
        if len(users) >= total_available:
            break

        page_number += 1  

    user_info = []
    for user in users:
        user_info.append({
            "Name": user.get("fullName"),
            "Username": user.get("name"),
            "Email": user.get("email"),
            "Last Login Date": user.get("lastLogin", "Never") 
        })

    return user_info

def main():
    creds = get_secrets()
    base_url = f"{creds['server']}/api/{API_VERSION}"

    credential_payload = {
        "credentials": {
            "name": creds["username"],
            "password": creds["password"],
            "site": {"contentUrl": ""}
        }
    }


    auth_data = api_request(base_url, "/auth/signin", method="POST", json_payload=credential_payload)

    token = auth_data["credentials"]["token"]
    site_id = auth_data["credentials"]["site"]["id"]

    users = get_all_users(base_url, token, site_id)

    return users


if __name__ == '__main__':
    users = main()


    with open("users_list.csv", mode="w", newline="", encoding="utf-8") as file:
           writer = csv.DictWriter(file, fieldnames=["Name", "Username", "Email", "Last Login Date"])
           writer.writeheader()  
           writer.writerows(users) 
