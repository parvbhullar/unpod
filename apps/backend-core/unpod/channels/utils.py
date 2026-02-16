import json
import os

from django.conf import settings


class AppCredUtility:
    @staticmethod
    def get_client_credentials(app):
        if app.name != "Gmail":
            return None

        config = app.config
        client_secret_path = os.path.join(settings.ROOT_DIR, config.get("client_secret"))

        if not client_secret_path or not os.path.exists(client_secret_path):
            raise FileNotFoundError(f"Client secret file not found: {client_secret_path}")

        try:
            with open(client_secret_path, 'r') as file:
                data = json.load(file)
                client_id = data['web']['client_id']
                client_secret = data['web']['client_secret']
                config = {
                    "client_id": client_id,
                    "client_secret": client_secret
                }
                return config
        except (KeyError, json.JSONDecodeError) as e:
            raise ValueError(f"Error reading client credentials: {e}")
