from django.utils import timezone
from django.conf import settings
from unpod.common.datetime import date_to_datetime
from unpod.common.helpers.service_helper import send_email
from unpod.space.models import Space, SpaceOrganization
from unpod.thread.models import ThreadPost
from unpod.common.mongodb import MongoDBQueryManager
from django.contrib.auth import get_user_model
from bson import ObjectId
from django.db.models import Count


def get_data(query, today):
    week_date = today - timezone.timedelta(days=7)
    month_date = today - timezone.timedelta(days=30)
    today_count = query.filter(created__date=today)
    last_day_count = query.filter(created__date=today - timezone.timedelta(days=1))
    weekly = query.filter(created__date__gte=week_date, created__date__lte=today)
    monthly = query.filter(created__date__gte=month_date, created__date__lte=today)
    return (
        query.count(),
        today_count.count(),
        last_day_count.count(),
        weekly.count(),
        monthly.count(),
    )


def get_organization_group_data(query, today, organization_key):
    week_date = today - timezone.timedelta(days=7)
    month_date = today - timezone.timedelta(days=30)
    today_count = query.filter(created__date=today)
    last_day_count = query.filter(created__date=today - timezone.timedelta(days=1))
    weekly = query.filter(created__date__gte=week_date, created__date__lte=today)
    monthly = query.filter(created__date__gte=month_date, created__date__lte=today)
    today_group = today_count.values(organization_key).annotate(count=Count(organization_key))
    today_group = {each[organization_key]: each["count"] for each in today_group}
    last_day_group = last_day_count.values(organization_key).annotate(count=Count(organization_key))
    last_day_group = {each[organization_key]: each["count"] for each in last_day_group}
    weekly_group = weekly.values(organization_key).annotate(count=Count(organization_key))
    weekly_group = {each[organization_key]: each["count"] for each in weekly_group}
    monthly_group = monthly.values(organization_key).annotate(count=Count(organization_key))
    monthly_group = {each[organization_key]: each["count"] for each in monthly_group}
    total_group = query.values(organization_key).annotate(count=Count(organization_key))
    total_group = {each[organization_key]: each["count"] for each in total_group}
    return {
        "total": total_group,
        "today": today_group,
        "last_day": last_day_group,
        "weekly": weekly_group,
        "monthly": monthly_group,
    }


def get_data_mongo(collection, today, query: dict = {}):
    week_date = today - timezone.timedelta(days=7)
    month_date = today - timezone.timedelta(days=30)
    last_day = today - timezone.timedelta(days=1)
    week_date_query = {
        "_id": {"$gte": ObjectId.from_datetime(date_to_datetime(week_date))},
        **query,
    }
    month_date_query = {
        "_id": {
            "$gte": ObjectId.from_datetime(date_to_datetime(month_date)),
        },
        **query,
    }
    last_day_query = {
        "_id": {
            "$gte": ObjectId.from_datetime(date_to_datetime(last_day)),
            "$lt": ObjectId.from_datetime(date_to_datetime(today)),
        },
        **query,
    }
    today_query = {
        "_id": {"$gte": ObjectId.from_datetime(date_to_datetime(today))},
        **query,
    }
    return (
        MongoDBQueryManager.run_query(collection, "count_documents", {**query}),
        MongoDBQueryManager.run_query(collection, "count_documents", today_query),
        MongoDBQueryManager.run_query(collection, "count_documents", last_day_query),
        MongoDBQueryManager.run_query(collection, "count_documents", week_date_query),
        MongoDBQueryManager.run_query(collection, "count_documents", month_date_query),
    )


def get_hubwise_data_mongo(collection, today, query: dict = {}):
    week_date = today - timezone.timedelta(days=7)
    month_date = today - timezone.timedelta(days=30)
    last_day = today - timezone.timedelta(days=1)
    week_date_query = {
        "_id": {"$gte": ObjectId.from_datetime(date_to_datetime(week_date))},
        **query,
    }
    month_date_query = {
        "_id": {
            "$gte": ObjectId.from_datetime(date_to_datetime(month_date)),
        },
        **query,
    }
    last_day_query = {
        "_id": {
            "$gte": ObjectId.from_datetime(date_to_datetime(last_day)),
            "$lt": ObjectId.from_datetime(date_to_datetime(today)),
        },
        **query,
    }
    today_query = {
        "_id": {"$gte": ObjectId.from_datetime(date_to_datetime(today))},
        **query,
    }
    group = {"_id": "$pilot", "count": {"$sum": 1}}
    total_group = MongoDBQueryManager.run_query(
        collection, "aggregate", [{"$match": {**query}}, {"$group": group}]
    )
    total_group = {each["_id"]: each["count"] for each in total_group}
    today_group = MongoDBQueryManager.run_query(
        collection, "aggregate", [{"$match": today_query}, {"$group": group}]
    )
    today_group = {each["_id"]: each["count"] for each in today_group}
    last_day_group = MongoDBQueryManager.run_query(
        collection, "aggregate", [{"$match": last_day_query}, {"$group": group}]
    )
    last_day_group = {each["_id"]: each["count"] for each in last_day_group}
    weekly_group = MongoDBQueryManager.run_query(
        collection, "aggregate", [{"$match": week_date_query}, {"$group": group}]
    )
    weekly_group = {each["_id"]: each["count"] for each in weekly_group}
    monthly_group = MongoDBQueryManager.run_query(
        collection, "aggregate", [{"$match": month_date_query}, {"$group": group}]
    )
    monthly_group = {each["_id"]: each["count"] for each in monthly_group}
    return {
        "total": total_group,
        "today": today_group,
        "last_day": last_day_group,
        "weekly": weekly_group,
        "monthly": monthly_group,
    }


def merge_hub_data(organizationDictId, space_data, post_data):
    merged_data = {}
    for organization in organizationDictId:
        merge_hub_data = []
        stats_keys = ["total", "today", "last_day", "weekly", "monthly"]
        for stats in stats_keys:
            merge_hub_data.append(space_data[stats].get(organization, 0))
            merge_hub_data.append(post_data[stats].get(organization, 0))
        merged_data[organizationDictId[organization]["name"]] = merge_hub_data
    return merged_data


def hubWiseData(hubData, today=None):
    if today is None:
        today = timezone.now().date().today()
    hubDataDictId = {}
    hubDataDictHandle = {}
    for each in hubData:
        hubDataDictHandle[each["domain_handle"]] = each
        hubDataDictId[each["id"]] = each
    space_data = Space.objects.all()
    post_data = ThreadPost.objects.all()
    space_data = get_hub_group_data(space_data, today, "space_organization_id")
    post_data = get_hub_group_data(post_data, today, "space__space_organization_id")
    merged_data = merge_hub_data(hubDataDictId, space_data, post_data)
    return merged_data


def dailyActivityReport():
    today = timezone.now().date().today()
    organization_query = SpaceOrganization.objects.all()
    organization_data = get_data(organization_query, today)
    space_query = Space.objects.all()
    space_data = get_data(space_query, today)
    thread_query = ThreadPost.objects.all()
    thread_data = get_data(thread_query, today)

    user_query = get_user_model().objects.all()
    user_data = get_data(user_query, today)
    blocks_data = get_data_mongo("blocks", today)
    data = {}
    data["Users"] = user_data
    data["organization"] = organization_data
    data["Space"] = space_data
    data["Thread"] = thread_data
    data["Blocks"] = blocks_data
    all_pilots = MongoDBQueryManager.run_query("task_request_log", "distinct", "pilot")
    for pilot in all_pilots:
        pilot_data = get_data_mongo("task_request_log", today, {"pilot": pilot})
        data[pilot.title()] = pilot_data
    body = ""
    body += """<h3 style="text-align:center; margin-top:10px;">Last 30 Days Overall Data</h3>"""

    body += """
            <table width="100%" border="2" cellspacing="10" cellpadding="10" rules="ALL" style="border-collapse:
            collapse;color:#1f2240;background-color:#ffffff; padding: 10px">
            <tr><th>Metrics</th><th>Total</th><th>Today</th><th>Yesterday</th>
            <th>Last 7 Days</th><th>Last 30 Days</th></tr>
            """
    for k, v in data.items():
        body += "<tr>"
        body += "<td>" + k + "</td>"
        for each in v:
            body += "<td>" + str(each) + "</td>"
        body += "</tr>"
    body += "</table>"
    body += "<br><br>"
    body += """<h3 style="text-align:center; margin-top:10px;">Last 30 Days Organization Wise Data</h3>"""
    organizationList = SpaceOrganization.objects.all().values("id", "domain_handle", "name")
    organizationData = hubWiseData(organizationList, today)
    body += """
            <table width="100%" border="2" cellspacing="10" cellpadding="10" rules="ALL" style="border-collapse:collapse;color:#1f2240;background-color:#fff;padding:10px">
                <tr>
                    <th>Org Name</th>
                    <th colspan="2">Total</th>
                    <th colspan="2">Today</th>
                    <th colspan="2">Yesterday</th>
                    <th colspan="2">Last 7 Days</th>
                    <th colspan="2">Last 30 Days</th>
                </tr>
                <tr>
                    <td></td>
                    <td>Space</td>
                    <td>Post</td>
                    <td>Space</td>
                    <td>Post</td>
                    <td>Space</td>
                    <td>Post</td>
                    <td>Space</td>
                    <td>Post</td>
                    <td>Space</td>
                    <td>Post</td>
                </tr>
            """
    organizationWisePilotData = {}
    for organization in organizationList:
        pilot_data = get_hubwise_data_mongo(
            "task_request_log", today, {"org_id": organization["id"]}
        )
        organizationWisePilotData[organization["name"]] = pilot_data
    for k, v in organizationData.items():
        body += "<tr>"
        body += "<td>" + k + "</td>"
        for each in v:
            body += "<td>" + str(each) + "</td>"
        body += "</tr>"
    body += "</table>"
    body += "<br><br>"
    body += """<h3 style="text-align:center; margin-top:10px;">Last 30 Days Organization Wise Pilot Usage</h3>"""
    body += """
            <table width="100%" border="2" cellspacing="10" cellpadding="10" rules="ALL" style="border-collapse:collapse;color:#1f2240;background-color:#fff;padding:10px">
                <tr>
                    <th>Org Name</th>
                    <th>Total</th>
                    <th>Today</th>
                    <th>Yesterday</th>
                    <th>Last 7 Days</th>
                    <th>Last 30 Days</th>
                </tr>
            """
    for k, v in organizationWisePilotData.items():
        pilot_body = "<tr>"
        pilot_body += "<td>" + k + "</td>"
        stats_keys = ["total", "today", "last_day", "weekly", "monthly"]
        has_data = False
        for each in stats_keys:
            pilot_body += "<td>"
            pilot_data = v[each]
            if pilot_data:
                has_data = True
                pilot_body += "<ul>"
                for pilot_name, count in pilot_data.items():
                    pilot_body += f"<li>{pilot_name.title()}: {count}</li>"
                pilot_body += "</ul>"
            else:
                pilot_body += "---"
            pilot_body += "</td>"
        pilot_body += "</tr>"
        if has_data:
            body += pilot_body
    body += "</table>"
    body += "</body>"

    to_emails = settings.DAILY_REPORT_EMAILS
    email_from = settings.EMAIL_FROM_ADDRESS
    subject = f"Daily Activity Report {settings.ENV_NAME} - {today.__str__()}"
    send_email(
        subject,
        email_from,
        to_emails,
        mail_body=body,
        mail_type="html",
    )
