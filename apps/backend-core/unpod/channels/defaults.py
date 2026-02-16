from unpod.channels.models import App

predefined_apps = {
    "Gmail": {
        "slug": "gmail",
        "logo": "",
        "config": {
            "initiate_url": "google_auth_login",
            "redirection_url": "google_auth_callback",
            "client_secret": "client_secrets.json",
            "scopes": [
                "openid",
                "email",
                "https://www.googleapis.com/auth/gmail.readonly"
            ],
        },
    },
    "Outlook": {
        "slug": "outlook",
        "logo": "",
        "config": {
            "initiate_url": "outlook_auth_login",
            "redirection_url": "outlook_auth_callback",
            "client_id": "dummy_client_id",
            "client_secret": "creds.json",
            "tenant_id": "fd3ec6c4-0319-4bb2-9601-971ec2f6e9fd",
            "scopes": [
                "https://graph.microsoft.com/Mail.Read"
            ],
        },
    },
}


def populate_channel_apps():
    for name, details in predefined_apps.items():
        app, created = App.objects.get_or_create(
            name=name,
            defaults={
                "description": f"{name} Integration",
                "icon": details.get("logo"),
                "slug": details.get("slug"),
                "config": details.get("config", {}),
                "is_active": True,
            },
        )
        if created:
            print(f"Created app: {name}")
        else:
            print(f"App already exists: {name}")
