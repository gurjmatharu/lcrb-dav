import json
import requests


def deliver_notification(topic: str, payload: dict, endpoint: str):
    ret_data = {topic: payload}
    return requests.post(
        endpoint, data=json.dumps(payload), headers={"Content-Type": "application/json"}
    )
