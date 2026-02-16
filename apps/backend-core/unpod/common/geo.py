import requests

IPFIND_TOKEN = "ef917b3df22471"


def getUserIp(request):
    if request:
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
    else:
        ip = "127.0.0.1"

    if ip in ["127.0.0.1", "localhost"]:
        ip = "59.89.110.158"
    return ip


def getIPAddressLocation(ip_address):
    data = {}
    default_data = {
        "zip": "209601",
        "city": "Gurdaspur",
        "state": "Uttar Pradesh",
        "country": "India",
        "lat": "00",
        "lng": "00",
        "ip_address": ip_address,
    }
    loc = requests.get(f"https://ipinfo.io/{ip_address}?token={IPFIND_TOKEN}")
    # print("Loc Data Request",loc.request.url, loc.status_code, loc.content)
    if loc.status_code == 200:
        loc = loc.json()
        loc_data = loc.get("loc")
        data = {
            "zip": loc.get("postal"),
            "city": loc.get("city"),
            "state": loc.get("region"),
            "country": loc.get("country"),
            "timezone": loc.get("timezone"),
            "ip_address": ip_address,
        }
        if loc_data:
            loc_data = loc_data.split(",")
            data["lat"] = loc_data[0] or default_data["lat"]
            data["lng"] = loc_data[1] or default_data["lng"]
        else:
            data["lat"] = default_data["lat"]
            data["lng"] = default_data["lng"]
    else:
        data = default_data
    return data
