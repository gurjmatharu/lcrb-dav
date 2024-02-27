import json

import requests


def deliver_notification(payload: dict, endpoint: str):
    url = endpoint.split("#")[0]
    api_key = endpoint.split("#")[1]
    headers = {"Content-Type": "application/json"}
    if api_key is not None:
        headers["x-api-key"] = api_key
    return requests.post(url=url, data=json.dumps(payload), headers=headers)
