import codecs
import os
from typing import List
from django.conf import settings
from unpod.common.logger import print_log
from unpod.common.s3 import upload_s3
from unpod.common.sitemap_generator.core import Sitemap
from unpod.thread.models import ThreadPost
from unpod.space.models import Space, SpaceOrganization
from unpod.core_components.models import Pilot

BASE_URL = settings.BASE_FRONTEND_URL

if not BASE_URL.endswith("/"):
    BASE_URL = BASE_URL + "/"


def generate_post_sitemap():
    sitemap_file = "sitemap-post"
    post_list: List[ThreadPost] = ThreadPost.objects.filter(
        privacy_type="public", post_status="published"
    ).prefetch_related("space", "space__space_organization")
    count = 0
    sm = Sitemap(changefreq="weekly", sitemap_url=BASE_URL)
    for post in post_list:
        url = f"{BASE_URL}thread/{post.slug}/"
        sm.add(url, changefreq="weekly", priority=1, lastmod=post.modified)
        count += 1
    print_log(count, sitemap_file)
    sm.write(sitemap_file)
    upload_sitemap(sitemap_file)


def generate_organization_sitemap():
    sitemap_file = "sitemap-organization"
    organization_list: List[SpaceOrganization] = SpaceOrganization.objects.filter(
        privacy_type="public"
    )
    count = 0
    sm = Sitemap(changefreq="daily", sitemap_url=BASE_URL)
    for organization in organization_list:
        url = f"{BASE_URL}{organization.domain_handle}/org/"
        sm.add(url, changefreq="daily", priority=1, lastmod=organization.modified)
        count += 1
    print_log(count, sitemap_file)
    sm.write(sitemap_file)
    upload_sitemap(sitemap_file)


def generate_space_sitemap():
    sitemap_file = "sitemap-space"
    space_list: List[Space] = Space.objects.filter(
        privacy_type="public"
    ).prefetch_related("space_organization")
    count = 0
    sm = Sitemap(changefreq="daily", sitemap_url=BASE_URL)
    for space in space_list:
        url = f"{BASE_URL}spaces/{space.slug}/"
        sm.add(url, changefreq="daily", priority=1, lastmod=space.modified)
        count += 1
    print_log(count, sitemap_file)
    sm.write(sitemap_file)
    upload_sitemap(sitemap_file)


def generate_pilot_sitemap():
    sitemap_file = "sitemap-ai-agents"
    pilot_list: List[Pilot] = Pilot.objects.filter(
        privacy_type="public", state="published"
    ).prefetch_related("owner")
    count = 0
    sm = Sitemap(changefreq="daily", sitemap_url=BASE_URL)
    for pilot in pilot_list:
        url = f"{BASE_URL}{pilot.owner.domain_handle}/{pilot.handle}/"
        sm.add(url, changefreq="daily", priority=1, lastmod=pilot.modified)
        count += 1
    print_log(count, sitemap_file)
    sm.write(sitemap_file)
    try:
        upload_sitemap(sitemap_file)
    except Exception as e:
        print(e)


def upload_sitemap(file_name: str):
    if not file_name.endswith(".xml"):
        file_name = f"{file_name}.xml"
    data = codecs.open(f"{settings.SITEMAP_DIR}/{file_name}", "r", "utf-8").read()
    metadata = {"Content-Type": "application/xml"}
    file_url, status = upload_s3(
        settings.AWS_STORAGE_BUCKET_NAME,
        data,
        f"{settings.AWS_SITEMAP_DIR}/{file_name}",
        ContentType="application/xml",
    )
    print_log(file_url, status)


def generate_sitemap():
    os.makedirs(settings.SITEMAP_DIR, exist_ok=True)
    generate_post_sitemap()
    generate_organization_sitemap()
    generate_space_sitemap()
    generate_pilot_sitemap()
