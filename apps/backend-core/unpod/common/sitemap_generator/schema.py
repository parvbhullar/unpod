from django.conf import settings

from unpod.common.string import textify

BASE_URL = settings.BASE_FRONTEND_URL

if not BASE_URL.endswith("/"):
    BASE_URL = BASE_URL + "/"


def get_image_url(image_url, height=720, width=1280):
    if not image_url:
        return image_url
    if "imagekit" in image_url:
        image_url = f"{image_url}?tr=w-{width},h-{height}"
    elif "cloudinary" in image_url:
        image_url = image_url.replace("upload", f"upload/w_{width},h_{height}")
    return image_url


def get_thumbnail(playback_id):
    return f"https://image.mux.com/{playback_id}/thumbnail.png?height=720&width=1280&fit_mode=smartcrop"


def generate_post_schema(post):
    if post.get("post_type") == "ask" and len(post.get("block")):
        return generate_ask_schema(post)
    schema_json = dict()
    schema_json["@context"] = "https://schema.org"
    schema_json["@type"] = "Article"

    organization = post.get("organization", {})
    post_path = f"/{organization.get('domain_handle')}/{post.get('space', {}).get('slug')}/{post.get('slug')}/"

    schema_json["keywords"] = ",".join(post.get("tags", []))
    media = post.get("media")
    if media and media.get("media_type") == "video" and media.get("playback_id"):
        schema_json["@type"] = "VideoObject"
        schema_json["name"] = post.get("title")
        schema_json["thumbnailUrl"] = get_thumbnail(media.get("playback_id"))
        schema_json["uploadDate"] = post.get("created")
        schema_json["contentSize"] = f"{media.get('size')} Bytes"
        schema_json["interactionCount"] = post.get("view_count", 0)
    elif media and media.get("media_type") == "audio" and media.get("playback_id"):
        schema_json["@type"] = "AudioObject"
        schema_json["name"] = post.get("title")
        schema_json["thumbnailUrl"] = get_thumbnail(media.get("playback_id"))
        schema_json["uploadDate"] = post.get("created")
        schema_json["contentSize"] = f"{media.get('size')} Bytes"
        schema_json["interactionCount"] = post.get("view_count", 0)
    else:
        schema_json["headline"] = post.get("title")

    schema_json["datePublished"] = post.get("created")
    schema_json["dateModified"] = post.get("created")
    schema_json["description"] = post.get("description") or " ".join(
        textify(post.get("content")).split()[:250]
    )

    # mainEntityOfPage
    schema_json["mainEntityOfPage"] = dict()
    schema_json["mainEntityOfPage"]["@type"] = "WebPage"
    schema_json["mainEntityOfPage"]["@id"] = post_path

    # Image
    cover_image = post.get("cover_image", {}) or {}
    if cover_image.get("url"):
        image_url = cover_image.get("url")
        image_url = get_image_url(image_url)
        schema_json["image"] = dict()
        schema_json["image"]["@type"] = "ImageObject"
        schema_json["image"]["url"] = image_url
        schema_json["image"]["width"] = 1280
        schema_json["image"]["height"] = 720

    # Author
    schema_json["author"] = dict()
    schema_json["author"]["@type"] = "Person"
    schema_json["author"]["url"] = BASE_URL
    schema_json["author"]["name"] = "Team MastersIndia"
    if post.get("user", {}).get("full_name"):
        schema_json["author"]["name"] = post.get("user", {}).get("full_name")
    if post.get("user", {}).get("profile_picture"):
        schema_json["author"]["url"] = post.get("user", {}).get("profile_picture")

    # Publisher
    schema_json["publisher"] = dict()
    schema_json["publisher"]["@type"] = "Organization"
    schema_json["publisher"]["name"] = organization.get("name")
    schema_json["publisher"]["url"] = organization.get("domain")
    schema_json["publisher"]["logo"] = dict()
    schema_json["publisher"]["logo"]["@type"] = "ImageObject"
    schema_json["publisher"]["logo"]["url"] = (
        get_image_url(organization.get("logo")) or f"{BASE_URL}images/logo.png"
    )
    schema_json["publisher"]["logo"]["width"] = 400
    schema_json["publisher"]["logo"]["height"] = 300
    return schema_json


def generate_ask_schema(post):
    schema_json = dict()
    schema_json["@context"] = "https://schema.org"
    schema_json["@type"] = "Article"
    schema_json["headline"] = post.get("title")
    schema_json["mainEntityOfPage"] = dict()
    schema_json["mainEntityOfPage"]["@type"] = "WebPage"
    organization = post.get("organization", {})
    post_path = f"/{organization.get('domain_handle')}/{post.get('space', {}).get('slug')}/{post.get('slug')}/"
    schema_json["mainEntityOfPage"]["@id"] = post_path

    # schema_json["question"] = post.get("title")
    schema_json["description"] = post.get("description") or " ".join(
        textify(post.get("content")).split()[:250]
    )
    schema_json["keywords"] = ",".join(post.get("tags", []))
    # schema_json["articleSection"] = post["category"].get("title")
    # schema_json["keywords"] = post.get("seo_keyword")
    schema_json["image"] = dict()
    schema_json["image"]["@type"] = "ImageObject"
    schema_json["image"]["url"] = ""
    cover_image = post.get("cover_image", {}) or {}
    if cover_image.get("url"):
        image_url = cover_image.get("url")
        image_url = get_image_url(image_url)
        schema_json["image"]["url"] = image_url
    schema_json["image"]["width"] = 1280
    schema_json["image"]["height"] = 720

    schema_json["author"] = dict()
    schema_json["author"]["@type"] = "Person"
    schema_json["author"]["url"] = BASE_URL
    schema_json["author"]["name"] = "Team MastersIndia"
    if post.get("user", {}).get("full_name"):
        schema_json["author"]["name"] = post.get("user", {}).get("full_name")
    if post.get("user", {}).get("profile_picture"):
        schema_json["author"]["url"] = post.get("user", {}).get("profile_picture")

    schema_json["publisher"] = dict()
    schema_json["publisher"]["@type"] = "Organization"
    schema_json["publisher"]["name"] = organization.get("name")
    schema_json["publisher"]["url"] = organization.get("domain")
    schema_json["publisher"]["logo"] = dict()
    schema_json["publisher"]["logo"]["@type"] = "ImageObject"
    schema_json["publisher"]["logo"]["url"] = (
        get_image_url(organization.get("logo")) or f"{BASE_URL}images/logo.png"
    )
    schema_json["publisher"]["logo"]["width"] = 400
    schema_json["publisher"]["logo"]["height"] = 300

    schema_json["datePublished"] = post.get("created")
    schema_json["dateModified"] = post.get("created")

    schema_json["mainEntity"] = {}
    schema_json["mainEntity"]["@type"] = "Question"
    schema_json["mainEntity"]["name"] = post.get("title")
    schema_json["mainEntity"]["acceptedAnswer"] = {}
    schema_json["mainEntity"]["acceptedAnswer"]["@type"] = "Answer"
    schema_json["mainEntity"]["acceptedAnswer"]["text"] = (
        post.get("block").get("data", {}).get("content")
    )
    schema_json["mainEntity"]["acceptedAnswer"]["author"] = {}
    schema_json["mainEntity"]["acceptedAnswer"]["author"]["@type"] = "SuperPilot"
    schema_json["mainEntity"]["acceptedAnswer"]["author"]["name"] = (
        post.get("block", {}).get("user", {}).get("full_name")
    )
    return schema_json
