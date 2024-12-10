import requests
import boto3
import json
import random
import string

API_VERSION = "3.18"
SECRET_ID = False
assert SECRET_ID, 'NEED to fix tableau credentials'
REGION = "us-west-2"


def get_secrets():
    return json.loads(boto3.client('secretsmanager', region_name=REGION)
                      .get_secret_value(SecretId=SECRET_ID)['SecretString'])

def generate_password(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

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

def main(user_email):
    creds = get_secrets()
    base_url = f"{creds['server']}/api/{API_VERSION}"

    credential_payload = {"credentials": 
                          {"name": creds["username"], 
                           "password": creds["password"],
                             "site": {"contentUrl": ""}}}
    

    auth_data = api_request(base_url,
                             "/auth/signin",
                               method="POST", 
                               json_payload= credential_payload
                               )

    token = auth_data["credentials"]["token"]
    site_id = auth_data["credentials"]["site"]["id"]
    
    site_url = f"/sites/{site_id}"

    users = api_request(base_url, f"{site_url}/users", token=token)["users"]["user"]
    user = next((u for u in users if u.get("email") == user_email), None)
    if not user:
        raise ValueError(f"User {user_email} not found.")

    new_password = generate_password()
    api_request(base_url, f"{site_url}/users/{user['id']}", method="PUT", token=token, json_payload={
        "user": {"password": new_password}
    })
    print(f"{user_email}: {new_password}")

if __name__ == "__main__":
    __name__
