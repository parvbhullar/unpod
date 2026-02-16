from django.conf import settings
import requests


def generate_room_token_server(room_name, agent_name, room_metadata, user):
    url = f"{settings.API_SERVICE_URL}/voice/genrate_voice_token/"
    data = {
        "room_name": room_name,
        "agent_name": agent_name,
        "metadata": room_metadata,
        "user": user,
    }
    res = requests.post(url, json=data)
    data = res.json()
    data["data"]["metadata"] = room_metadata
    data["data"]["space_token"] = room_metadata["token"]
    return data


def delete_room_server(room_name):
    url = f"{settings.API_SERVICE_URL}/voice/delete_voice_room/{room_name}/"
    res = requests.delete(url)
    data = res.json()
    return data
