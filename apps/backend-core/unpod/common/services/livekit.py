def get_livekit_trunks():
  url = f"https://{settings.LIVEKIT_BASE}/twirp/livekit.SIP/ListSIPInboundTrunk"

  api_key = settings.LIVEKIT_API_KEY
  api_secret = settings.LIVEKIT_API_SECRET
  now = int(time.time())
  _token_expiry = now + 3500

  payload = {
    "iss": api_key,
    "exp": now + 3600,
    "iat": now,
    "video": {"ingressAdmin": True},
    "sip": {"call": True, "admin": True},
  }
  token = jwt.encode(payload, api_secret, algorithm="HS256")
  token = token if isinstance(token, str) else token.decode("utf-8")

  headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
  }

  try:
    data = requests.post(f"{url}", headers=headers, json={})
    res = data.json().get("items")
    return res
  except Exception as e:
    print("exception occured while fetching numbers", str(e))
    return []
