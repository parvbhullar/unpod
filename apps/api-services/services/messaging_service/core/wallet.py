from decimal import Decimal
from libs.core.jsondecoder import convert_decimal
from libs.storage.postgres import executeQuery
from libs.storage.redis_storage import REDIS
from services.messaging_service.models.wallet import TaskRequestLogModel
from libs.api.logger import get_logger

app_logging = get_logger("messaging_service")


def fetchOrg(user_id):
    org = executeQuery(
        """
        SELECT userbasicdetail_user.active_organization_id
        FROM users_user AS "user"
        JOIN users_userbasicdetail AS userbasicdetail_user ON "user".id = userbasicdetail_user.user_id
        WHERE "user".id = %s
        """,
        (user_id,),
    )
    if org:
        app_logging.debug("fetchOrg result", org)
        return org["active_organization_id"]
    return None


def fetchSpace(space_slugs):
    spaces = executeQuery(
        "SELECT * FROM space_space WHERE slug = ANY(%s)",
        (space_slugs,),
    )
    if spaces:
        return spaces
    return None


def fetchSpaceByToken(token):
    space = executeQuery(
        "SELECT id, name, token, slug, space_type, content_type FROM space_space WHERE token = %s",
        (token,),
    )
    app_logging.debug("fetchSpaceByToken result", space)
    return space


def fetch_unit(curreny):
    redis_key = f"currency_{curreny}"
    unit = REDIS.get(redis_key)
    if unit:
        return Decimal(unit.decode())
    unit = executeQuery(
        "SELECT * FROM wallet_bitconvertormodel WHERE currency = %s",
        (curreny,),
    )
    if unit:
        REDIS.set(redis_key, str(unit.get("unit_value")), ex=3600)
        return Decimal(unit.get("unit_value"))
    return 1


def fetchWallet(user_id, org_id=None):
    if not org_id:
        org_id = fetchOrg(user_id)
        if not org_id:
            raise ValueError("You Need to Join the Hub First")
    wallet = executeQuery(
        "SELECT * FROM wallet_userwallet WHERE organization_id = %s",
        (org_id,),
    )
    if wallet:
        return wallet
    return {
        "id": 0,
        "bits": Decimal("0.000000"),
        "last_tranaction_id": 0,
        "organization_id": org_id,
        "user_id": user_id,
    }


def updateWallet(wallet_id, bits, user_id, org_id=None):
    if wallet_id is None:
        wallet = fetchWallet(user_id, org_id)
        wallet_id = wallet.get("id")
    executeQuery(
        "UPDATE wallet_userwallet SET bits = bits - %s WHERE id = %s",
        (bits, wallet_id),
        commit=True,
    )


def addTaskRequest(thread_id, user, org_id, pilot, tokens, cost, wallet=None, **kwargs):
    create_data = {
        "thread_id": thread_id,
        "user_id": user.get("user_id") or user.get("id"),
        "user": user,
        "org_id": org_id,
        "pilot": pilot,
        "tokens": tokens,
        "cost": cost,
        **kwargs,
    }
    data = TaskRequestLogModel.Meta.model(**create_data)
    bits = data.bits
    request_log = data.to_mongo()
    data = convert_decimal(data.to_mongo())
    res = TaskRequestLogModel._get_collection().insert_one(data)
    request_log["_id"] = res.inserted_id
    request_log = TaskRequestLogModel.Meta.model.from_mongo(request_log)
    if wallet:
        updateWallet(wallet.get("id"), bits, user.get("user_id"), org_id)
    return request_log
