"""Wallet repository for database operations."""

import decimal
from decimal import Decimal
from typing import Any

from super_services.db.services.models.wallet import TaskRequestLogModel
from super_services.libs.core.db import executeQuery
from super_services.libs.core.jsondecoder import convert_decimal
from super_services.libs.core.redis import REDIS


def fetchOrg(user_id: int) -> int | None:
    """
    Fetch the active organization ID for a user.

    Args:
        user_id: The user ID to look up

    Returns:
        The active organization ID or None if not found
    """
    query = """
        SELECT userbasicdetail_user.active_organization_id
        FROM users_user AS "user"
        JOIN users_userbasicdetail AS userbasicdetail_user ON "user".id = userbasicdetail_user.user_id
        WHERE "user".id = %(user_id)s
    """
    org = executeQuery(query, params={"user_id": user_id})
    if org:
        print(org)
        return org["active_organization_id"]
    return None


def fetchSpace(space_slugs: list[str]) -> dict[str, Any] | None:
    """
    Fetch space by list of slugs.

    Args:
        space_slugs: List of space slugs to search for

    Returns:
        First matching space dict or None if not found
    """
    query = """
        SELECT * from space_space
        WHERE slug = ANY(%(space_slugs)s)
    """
    spaces = executeQuery(query, params={"space_slugs": space_slugs}, many=True)
    if len(spaces) > 0:
        return spaces[0]
    return None


def fetchSpaceByToken(token: str) -> dict[str, Any] | None:
    """
    Fetch space by token.

    Args:
        token: The space token to look up

    Returns:
        Space dict or None if not found
    """
    query = """
        SELECT id,name,token,slug,space_type,content_type from space_space
        WHERE token = %(token)s
    """
    space = executeQuery(query, params={"token": token})
    print(space)
    return space


def fetch_unit(curreny: str) -> Decimal:
    """
    Fetch currency unit value with Redis caching.

    Args:
        curreny: The currency code (typo preserved for compatibility)

    Returns:
        The unit value as Decimal, defaulting to 1 if not found
    """
    redis_key = f"currency_{curreny}"
    unit = REDIS.get(redis_key)
    if unit:
        return Decimal(unit.decode())
    query = """
        SELECT * FROM wallet_bitconvertormodel WHERE currency = %(currency)s
    """
    unit = executeQuery(query, params={"currency": curreny})
    if unit:
        REDIS.set(redis_key, str(unit.get("unit_value")), ex=3600)
        return Decimal(unit.get("unit_value"))
    return Decimal(1)


def fetchWallet(user_id: int, org_id: int | None = None) -> dict[str, Any]:
    """
    Fetch wallet for a user's organization.

    Args:
        user_id: The user ID
        org_id: Optional organization ID (will fetch if not provided)

    Returns:
        Wallet dict (either from DB or default empty wallet)

    Raises:
        ValueError: If user has no organization
    """
    if not org_id:
        org_id = fetchOrg(user_id)
        if not org_id:
            raise ValueError("You Need to Join the Hub First")
    query = "SELECT * FROM wallet_userwallet WHERE organization_id = %(org_id)s"
    wallet = executeQuery(query, params={"org_id": org_id})
    if wallet:
        return wallet
    return {
        "id": 0,
        "bits": Decimal("0.000000"),
        "last_tranaction_id": 0,
        "organization_id": org_id,
        "user_id": user_id,
    }


def updateWallet(
    wallet_id: int | None, bits: Decimal, user_id: int, org_id: int | None = None
) -> None:
    """
    Update wallet bits balance (deduct bits).

    Args:
        wallet_id: The wallet ID (will fetch if None)
        bits: Amount of bits to deduct
        user_id: The user ID
        org_id: Optional organization ID
    """
    if wallet_id is None:
        wallet = fetchWallet(user_id, org_id)
        wallet_id = wallet.get("id")
    query = """
        UPDATE wallet_userwallet SET bits = bits - %(bits)s WHERE id = %(wallet_id)s
    """
    executeQuery(query, params={"bits": bits, "wallet_id": wallet_id}, commit=True)


def addTaskRequest(
    thread_id: str,
    user: dict[str, Any],
    org_id: int,
    pilot: str,
    tokens: dict[str, Any],
    cost: Decimal,
    wallet: dict[str, Any] | None = None,
    **kwargs: Any,
) -> Any:
    """
    Add a task request log entry and update wallet.

    Args:
        thread_id: The thread identifier
        user: User dictionary
        org_id: Organization ID
        pilot: Pilot identifier
        tokens: Token usage information
        cost: Cost in bits
        wallet: Optional wallet dict
        **kwargs: Additional fields for the log entry

    Returns:
        The created TaskRequestLogModel instance
    """
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


def calculateBit(amount: Decimal | float, currency: str) -> Decimal:
    """
    Calculate bit amount from currency amount.

    Args:
        amount: Amount in the specified currency
        currency: Currency code (INR, BITS, USD, or others)

    Returns:
        Calculated bit amount
    """
    unit_value = fetch_unit(currency)
    if currency not in ["INR", "BITS", "USD"]:
        INR_unit = fetch_unit("INR")
        amount = decimal.Decimal(amount) * unit_value
        return round((decimal.Decimal(amount) / INR_unit), 6)
    return round((decimal.Decimal(amount) / unit_value), 6)


def checkWallet(user: dict[str, Any]) -> dict[str, Any]:
    """
    Check user wallet and return wallet info.

    Args:
        user: User dictionary with user_id and potentially space info

    Returns:
        Wallet dictionary

    Raises:
        InsufficientFundException: If wallet check fails
    """
    try:
        if user.get("is_anonymous", False) is True:
            user_id = user.get("user_id", 0)
            org_id = user.get("space", {}).get("org_id", 0)
            return {
                "id": 0,
                "bits": decimal.Decimal("0.000000"),
                "last_tranaction_id": 0,
                "organization_id": org_id,
                "user_id": user_id,
            }
        else:
            wallet = fetchWallet(user.get("user_id", user.get("id", 0)))
            bits = wallet.get("bits", 0)
            if False:
                raise InsufficientFundException(
                    f"You have low credit in your Hub wallet.\nPlease recharge your wallet to peform this task.\n Your Current credit is {round(float(bits), 6)} bits"
                )
            return wallet
    except Exception as ex:
        raise InsufficientFundException(str(ex))


def getTokenCost(response: Any) -> dict[str, Any]:
    """
    Extract token cost information from response.

    Args:
        response: Response object with token usage info

    Returns:
        Dictionary with tokens and cost information
    """
    return {
        "tokens": {
            "prompt_tokens_used": response.prompt_tokens_used,
            "completion_tokens_used": response.completion_tokens_used,
            "model": response.model_info.name,
        },
        "cost": round(decimal.Decimal(response.total_cost), 6),
        "currency": "USD",
    }


# TODO: review and move these at appropriate place.
PILOT_INFO = {
    "gpt-4": {
        "provider": "openai",
        "model": "gpt-4o",
        "temperature": 0.5,
    },
    "gpt-3.5": {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "temperature": 0.5,
    },
}


def getModelKargs(pilot: str) -> tuple[str, str]:
    """
    Get model configuration for a pilot.

    Args:
        pilot: Pilot identifier (e.g., 'gpt-4', 'gpt-3.5')

    Returns:
        Tuple of (provider, model)
    """
    pilot_info = PILOT_INFO.get(pilot)
    return pilot_info.get("provider"), pilot_info.get("model")


class InsufficientFundException(Exception):
    """Exception raised when wallet has insufficient funds."""

    pass
