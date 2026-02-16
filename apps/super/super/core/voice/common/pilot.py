import logging
import re

from super_services.libs.core.db import executeQuery

logger = logging.getLogger(__name__)


def normalize_phone_number(number: str) -> str:
    """
    Normalize phone number to E.164 format for consistent lookups.

    Args:
        number: Phone number in any format

    Returns:
        Normalized phone number with + prefix
    """
    if not number:
        return ""

    # Remove all non-digit characters except leading +
    cleaned = re.sub(r"[^\d+]", "", number)

    # Ensure + prefix for E.164 format
    if not cleaned.startswith("+"):
        cleaned = f"+{cleaned}"

    return cleaned


def get_pilot_slug(number: str) -> str | None:
    """Get pilot handle by phone number using JSON search on telephony_config."""
    normalized = normalize_phone_number(number)
    logger.debug(f"Looking up pilot for number: {number} (normalized: {normalized})")

    query = """
          SELECT *
          FROM core_components_pilot
          WHERE EXISTS (
              SELECT 1 FROM jsonb_array_elements(telephony_config->'telephony') elem
              WHERE elem->>'number' = %(number)s
          )
          LIMIT 1;
          """
    # Try with normalized number first
    res = executeQuery(query, many=True, params={"number": normalized})
    if res:
        handle = res[0].get("handle")
        logger.info(f"Found pilot {handle} for number {normalized}")
        return handle

    # Fallback: try original number if different
    if normalized != number:
        res = executeQuery(query, many=True, params={"number": number})
        if res:
            handle = res[0].get("handle")
            logger.info(f"Found pilot {handle} for original number {number}")
            return handle

    logger.warning(f"No pilot found for number: {number}")

    return None


# async def get_pilot_and_space_for_number(number: str) -> str | None:
#     from super_services.db.services.models.task import TaskModel
#
#     query = """
#              SELECT *
#              FROM core_components_pilot
#              WHERE JSON_SEARCH(telephony_config, 'one', %(number)s, NULL, '$.telephony[*].number') IS NOT NULL;
#              """
#
#     res = executeMysqlQuery(query, many=True, params={"number": number})
#     if res:
#         handles = [pilot.get("handle") for pilot in res]
#         pilots = list(
#             TaskModel._get_collection()
#             .find({"assignee": {"$in": handles}})
#             .sort([("created", -1)])
#             .limit(1)
#         )
#
#         data = {
#             "pilot": pilots[0].get("assignee"),
#             "space_id": pilots[0].get("space_id"),
#             "user_id": pilots[0].get("user"),
#             "task_id": pilots[0].get("task_id"),
#         }
#
#         return data
#
#     return None
def get_pilot_from_assistant_id(assistant_id: str) -> str | None:
    query = """
             SELECT handle
             FROM core_components_pilot
             WHERE config->'voice'->>'vapi_agent_id' = %(assistant_id)s
             LIMIT 1;
             """
    try:
        res = executeQuery(
            query=query, many=True, params={"assistant_id": assistant_id}
        )
        if not res:
            return None

        return res[0].get("handle")

    except Exception as e:
        logger.error(f"Error fetching pilot for assistant {assistant_id}: {e}")
        return None


def get_space_token(space_id: str) -> str | None:
    query = """
    select token from space_space  where id = %(space_id)s
    """
    params = {"space_id": space_id}

    res = executeQuery(query, many=True, params=params)

    if res:
        return res[0].get("token")

    return None


def get_pilot_handle_by_space_token(space_token: str) -> str | None:
    """Get pilot handle from space token."""
    query = """
    SELECT cp.handle
    FROM core_components_pilot AS cp
    JOIN space_space AS ss ON cp.space_id = ss.id
    WHERE ss.token = %(space_token)s
    LIMIT 1
    """
    res = executeQuery(query, many=True, params={"space_token": space_token})
    if res:
        return res[0].get("handle")
    return None


async def get_pilot_and_space_for_number(number: str) -> dict | None:
    """
    Get pilot handle and space info for a phone number.

    Lookup strategy:
    1. Try normalized number with junction table query
    2. Try original number with junction table query
    3. If pilot found but no tasks, return pilot data directly from DB

    Args:
        number: Phone number to lookup (any format)

    Returns:
        Dict with pilot, space_id, user_id, task_id or None if not found
    """
    from super_services.db.services.models.task import TaskModel

    normalized = normalize_phone_number(number)
    logger.info(
        f"Looking up pilot for inbound number: {number} (normalized: {normalized})"
    )

    query = """
    SELECT cp.handle, cp.space_id
    FROM core_components_pilot AS cp
    JOIN core_components_pilot_numbers AS cpn
        ON cp.id = cpn.pilot_id
    JOIN telephony_telephonynumber AS num
        ON num.id = cpn.telephonynumber_id
    WHERE num.number = %(number)s;
    """

    # Try normalized number first
    res = executeQuery(query, many=True, params={"number": normalized})

    # Fallback: try original number if different
    if not res and normalized != number:
        logger.debug(
            f"Lookup failed for {normalized}, trying original format: {number}"
        )
        res = executeQuery(query, many=True, params={"number": number})

    if not res:
        logger.warning(
            f"No pilot found for number: {number} (normalized: {normalized})"
        )
        return None

    handles = [pilot.get("handle") for pilot in res]
    space_id = res[0].get("space_id")
    logger.info(f"Found pilot handles for {number}: {handles}")

    # Try to find the most recent task for these pilots
    try:
        pilots = list(
            TaskModel._get_collection()
            .find(
                {
                    "assignee": {"$in": handles},
                    "space_id": {"$nin": [None, "", "<your_space_id>"]},
                }
            )
            .sort([("created", -1)])
            .limit(1)
        )

        try:
            query = "select token , name from space_space where id=%(space_id)s"
            space = executeQuery(
                query=query, params={"space_id": pilots[0].get("space_id")}
            )
            space_token = space.get("token")
            space_name = space.get("name")
        except Exception as e:
            logger.warning(f"Error fetching space token: {e}")
            space_token = ""
            space_name = ""

        if pilots:
            data = {
                "pilot": pilots[0].get("assignee"),
                "space_id": pilots[0].get("space_id"),
                "user_id": pilots[0].get("user"),
                "task_id": pilots[0].get("task_id"),
                "token": space_token,
                "space_name": space_name,
            }
            logger.info(f"Found pilot from task history: {data['pilot']}")
            return data

    except Exception as e:
        logger.warning(f"Error querying task history: {e}")

    # Fallback: Return pilot data directly from DB (no task history)
    logger.info(f"No task history found, using pilot directly: {handles[0]}")
    return {
        "pilot": handles[0],
        "space_id": space_id,
        "user_id": None,
        "task_id": None,
        "token": None,
        "space_name": None,
    }


def get_space_id(token):
    query = "select id from space_space where token=%(space_token)s"
    res = executeQuery(query=query, params={"space_token": token})

    logger.debug("Getting space id from token")

    if res:
        return res.get("id")
    return ""


if "__main__" == __name__:
    print(get_space_id("A2TDB1BZGKYT8XTHGGD7FXWD"))
    print(get_pilot_from_assistant_id("27500aa2-ea42-4210-8b46-aa1dff7bde04"))
