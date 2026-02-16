def generate_public_post_by_voice(request, space):
    origin = request.headers.get("origin")
    if "unpod" not in origin:
        return None
    session_user = request.data.get("session_user") or request.query_params.get(
        "session_user"
    )
    if not request.user.is_authenticated:
        return None
    elif not session_user:
        return None
    from unpod.thread.serializers import ThreadAnonymousCreateSerializer

    related_data = {**request.data.copy()}
    data = {
        "content_type": "voice",
        "post_type": "ask",
        "execution_type": "general",
        "focus": "my_space",
        "related_data": related_data,
    }
    ser = ThreadAnonymousCreateSerializer(
        data=data, context={"request": request, "space": space}
    )
    post = None
    if ser.is_valid():
        post = ser.save()
    return post
