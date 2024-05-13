import json

import requests


def deliver_notification(payload: dict, endpoint: str):
    url_split = endpoint.split("#")
    url = url_split[0]
    api_key = url_split[1] if 1 < len(url_split) else None
    headers = {"Content-Type": "application/json"}
    if api_key is not None:
        headers["x-api-key"] = api_key
    return requests.post(url=url, data=json.dumps(payload), headers=headers)
