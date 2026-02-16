import decimal
import json
import traceback
from datetime import date

import requests
from bson import ObjectId
from django.contrib.auth import get_user_model
from django.db.models import Model

from unpod.common.datetime import get_datetime_now
from unpod.common.jsonencoder import MongoJsonEncoder
from unpod.common.mongodb import MongoDBQueryManager
from unpod.subscription.models import (
    ActiveSubscription,
)
from unpod.wallet.enum import BitsTransactionVia, TransactionEnum, BitsTransactionType
from unpod.wallet.models import (
    BitConvertorModel,
    BitsTransaction,
    TransactionOrder,
    UserWallet,
)


def increment_order_number(model: Model):
    current_date = date.today()
    new_order_number = str(1)
    last_order = model.objects.all().order_by("id").last()
    if not last_order:
        # return '1'
        return f"ORDER{current_date.year}00000001"
    else:
        order_number = last_order.order_number

        if order_number is not None and len(order_number) > 0:
            if "ORDER" in order_number:
                order_number = int(order_number[9:])
            else:
                order_number = int(order_number)
            new_order_number = order_number + 1
            new_order_number = (
                f"ORDER{current_date.year}{str(new_order_number).zfill(8)}"
            )
        else:
            new_order_number = str(1)
            new_order_number = (
                f"ORDER{current_date.year}{str(new_order_number).zfill(8)}"
            )

    return new_order_number


def increment_receipt_number(model: Model):
    current_date = date.today()
    last_booking = (
        model.objects.filter(order_status=TransactionEnum.success.name)
        .order_by("id")
        .last()
    )
    if not last_booking:
        # return '1'
        return f"RE{current_date.year}00000001"
    else:
        receipt_number = last_booking.receipt_number
        if receipt_number is not None and len(receipt_number) > 0:
            if "RE" in receipt_number:
                receipt_number = int(receipt_number[9:])
            else:
                receipt_number = int(receipt_number)
            new_receipt_number = receipt_number + 1
            new_receipt_number = (
                f"RE{current_date.year}{str(new_receipt_number).zfill(8)}"
            )
        else:
            new_receipt_number = str(1)
            new_receipt_number = (
                f"RE{current_date.year}{str(new_receipt_number).zfill(8)}"
            )

    return new_receipt_number


def getINRUnitValue():
    obj = (
        BitConvertorModel.objects.filter(currency="INR")
        .values("unit_value", "currency")
        .last()
    )
    if obj:
        return obj.get("unit_value", 75)
    else:
        return 75


def getWallet(user, org_id=None) -> UserWallet:
    if not org_id:
        org_id = user.organization.id
    if org_id is None:
        raise ValueError("You Need to Join the organisation First")
    user_wallet, created = UserWallet.objects.get_or_create(organization_id=org_id)
    return user_wallet


def getActiveSubscription(user, org_id=None, product_id=None):
    if not org_id:
        try:
            org_id = user.organization.id
        except AttributeError:
            raise ValueError("User does not belong to any organization.")

    if org_id is None:
        raise ValueError("You need to join an organization first.")

    print(f"Checking for active subscription for organization ID: {org_id}")

    active_subscription = ActiveSubscription.objects.filter(
        organization_id=org_id,
        product_id=product_id,
        is_active=True,
        expired=False,
    ).first()

    if active_subscription:
        print(f"Active Subscription Found: {active_subscription}")
    else:
        print(f"No active subscription found for organization ID: {org_id}")

    return active_subscription


def checkActiveSubscription(org_id=None, product_id=None, **exclude_query):
    filter_query = {
        "organization_id": org_id,
        "product_id": product_id,
        "is_active": True,
        "expired": False,
    }

    active_subscription = ActiveSubscription.objects.filter(**filter_query)
    if exclude_query:
        active_subscription = active_subscription.exclude(**exclude_query)
    active_subscription = active_subscription.first()
    return active_subscription


def calculateBit(amount, currency):
    unit_value = 1
    obj = BitConvertorModel.objects.filter(currency=currency).first()
    if obj:
        unit_value = obj.unit_value
    bit_amount = round((decimal.Decimal(amount) / unit_value), 6)
    return bit_amount, unit_value


def updateWalletForTransaction(
    transaction, user, org_id=None, user_wallet=None, old_amount=0
):
    if not user_wallet:
        user_wallet = getWallet(user, org_id)
    if transaction.transaction_type == BitsTransactionType.added.name:
        user_wallet.bits = user_wallet.bits + transaction.bits - old_amount
    elif transaction.transaction_type == BitsTransactionType.subtracted.name:
        user_wallet.bits = user_wallet.bits - transaction.bits + old_amount
    user_wallet.last_tranaction = transaction
    user_wallet.save()


def createTransactionOrder(order_data: dict, user, org_id=None):
    amount, currency, reason = (
        order_data.get("amount"),
        order_data.get("currency"),
        order_data.pop("reason", ""),
    )
    order_number = increment_order_number(TransactionOrder)
    create_data = {
        "amount": amount,
        "currency": currency,
        "reason": reason,
        "order_number": order_number,
        "order_data": order_data,
        "user_id": user.id,
        "organization_id": org_id,
        "updated_by": user.id,
        "created_by": user.id,
    }
    trans_order = TransactionOrder.objects.create(**create_data)
    return trans_order


def processOrderTransaction(order_data: dict, user, org_id=None, update_wallet=True):
    try:
        user_wallet = getWallet(user, org_id)
    except Exception as ex:
        return "Please Join Atleast one organsation"
    if not org_id:
        org_id = user.organization.id
    trans_order = createTransactionOrder(order_data, user, org_id)
    bits = order_data.get("bits")
    if not bits:
        bits, unit_value = calculateBit(
            order_data.get("amount"), order_data.get("currency")
        )
    bits_transaction_create = {
        "transaction_type": BitsTransactionType.subtracted.name,
        "transaction_via": BitsTransactionVia.spent.name,
        "bits": bits,
        "user_id": user.id,
        "organization_id": org_id,
        "order_id": trans_order.id,
        "updated_by": user.id,
        "created_by": user.id,
        "transaction_date": get_datetime_now(),
    }
    bits_transaction = BitsTransaction.objects.create(**bits_transaction_create)
    if update_wallet:
        updateWalletForTransaction(
            bits_transaction, user, org_id=org_id, user_wallet=None, old_amount=0
        )
    else:
        user_wallet.last_tranaction = bits_transaction
        user_wallet.save()
    return bits_transaction


def updateUSDRate():
    url = "https://v6.exchangerate-api.com/v6/16743d60fa4ec4aaca577ec4/latest/USD"
    try:
        res = requests.get(url, timeout=20)
    except Exception as ex:
        print(ex)
        return f"Error --> {str(ex)}"
    INR_value = res.json().get("conversion_rates").get("INR")
    if INR_value:
        BitConvertorModel.objects.update_or_create(
            currency="USD", defaults={"unit_value": INR_value}
        )
        return f"Rate Updated, {INR_value}"
    return "Rate Not Updated"


def convertCurrency(amount, from_currency):
    if from_currency == "INR":
        return amount
    from_rate = BitConvertorModel.objects.filter(currency=from_currency).first()
    if not from_rate:
        return amount
    amount = decimal.Decimal(str(amount))
    from_rate = from_rate.unit_value  # 85.06
    return round(float(amount * from_rate), 2)


def generateTransaction(task_log_data):
    UserModel = get_user_model()
    org_id = task_log_data.get("_id").get("org_id")
    user_id = task_log_data.get("_id").get("user_id")
    pilot = task_log_data.get("_id").get("pilot")

    task_log_data["total_bits"] = decimal.Decimal(str(task_log_data["total_bits"]))
    order_data = {
        "org_id": org_id,
        "user_id": user_id,
        "pilot": pilot,
        "date": task_log_data.get("_id").get("date"),
        "bits": task_log_data.get("total_bits"),
        "rows": task_log_data.get("rows"),
    }
    user = UserModel.objects.get(id=order_data.get("user_id"))
    print({**order_data, "user": user})
    order_data["amount"] = order_data.get("bits")
    order_data["currency"] = "BITS"
    reason = f"Usage Cost to use the Pilot - {pilot.replace('-', ' ').title()}, Date - {task_log_data.get('_id').get('date')}"
    order_data["reason"] = reason
    row_query = [ObjectId(_id) for _id in task_log_data.get("rows")]
    row_query = {"_id": {"$in": row_query}}
    rows_data = MongoDBQueryManager.run_query("task_request_log", "find", row_query)
    rows_data = json.dumps(list(rows_data), cls=MongoJsonEncoder)
    rows_data = json.loads(rows_data)
    order_data["rows_data"] = rows_data
    processOrderTransaction(order_data, user, org_id, update_wallet=False)
    MongoDBQueryManager.run_query(
        "task_request_log", "update_many", row_query, update={"$set": {"status": 2}}
    )


def processGenerateHistory():
    query = [
        {"$match": {"status": 1}},
        {
            "$group": {
                "_id": {
                    "org_id": "$org_id",
                    "user_id": "$user_id",
                    "pilot": "$pilot",
                    "date": {
                        "$dateToString": {
                            "format": "%Y-%m-%dT%H:00:00",
                            "date": "$created",
                        }
                    },
                },
                "total_bits": {"$sum": "$bits"},
                "rows": {"$push": {"$toString": "$_id"}},
            }
        },
    ]
    unprocessed_data = list(
        MongoDBQueryManager.run_query("task_request_log", "aggregate", query)
    )
    print("unprocessed_data", len(unprocessed_data))
    for data in unprocessed_data:
        try:
            generateTransaction(data)
        except Exception as ex:
            print("Exception in generateTransaction", str(ex))
            traceback.print_exc()
    return f"Done, Count --> {len(unprocessed_data)}"
