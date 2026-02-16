from libs.api.config import get_settings

settings = get_settings()


class ImageKitStrorageBackend:
    endpoint = settings.IMAGE_KIT_ENDPOINT

    def __init__(self) -> None:
        pass

    def generateURL(self, name: str):
        if name is None:
            return None
        if name == "":
            return None
        if "media" in name:
            name = name.replace("media", "")
        if "private" in name:
            name = name.replace("private", "")
        if "//" in name:
            name = name.replace("//", "/")
        if not name.startswith("/"):
            name = f"/{name}"
        return f"{self.endpoint}{name}"


imagekitBackend = ImageKitStrorageBackend()
