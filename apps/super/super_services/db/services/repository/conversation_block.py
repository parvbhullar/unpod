import json
from typing import TYPE_CHECKING

from super_services.db.services.models.conversations import BlockModel
from super_services.libs.core.block_processor import get_pilot, getUser, processSaveBlock
from super_services.libs.core.datetime import get_create_modify
from super_services.libs.core.string import slugify

if TYPE_CHECKING:
    from super.core.context.schema import Message


def _extract_user_from_message(message: "Message") -> tuple[dict, str | None]:
    """
    Extract user dict and pilot_handle from a Message object.

    Args:
        message: The Message object to extract from

    Returns:
        Tuple of (user_dict, pilot_handle)
    """
    if message.sender.role == "user":
        pilot_handle = None
        sender_user = message.sender.to_dict()
        sender_user["full_name"] = sender_user.pop("name")
        sender_user["user_id"] = message.sender.id
        user_data = sender_user.pop("data", {})
        if user_data.get("user_token"):
            sender_user["user_token"] = user_data.get("user_token")
    else:
        pilot_handle = slugify(message.sender.name)
        sender_user = get_pilot(pilot_handle)
        sender_user.update({"role": message.sender.role})
    return sender_user, pilot_handle


# Map SDK block types to valid database enum values
# Valid: reply, text_msg, image_msg, video_msg, sys_msg, content_block,
#        heading_block, pilot_response, pilot_warning, question, write, notebook,
#        location, cards, json, audio_msg, file_msg, call, callee_msg
SDK_BLOCK_TYPE_MAP = {
    "text": "text_msg",
    "location": "location",
    "image": "image_msg",
    "video": "video_msg",
    "audio": "audio_msg",
    "file": "file_msg",
    "json": "json",
    "cards": "cards",
    "call": "call",
    "callee_msg": "callee_msg",
}


def _extract_block_data_from_message(message: "Message") -> tuple[dict, str]:
    """
    Extract block data dict from a Message object.

    Handles SDK messages in two formats:
    1. Simple: {"event":"message","data":{"content":"text","block_type":"text"}}
    2. Block: {"event":"block","data":{"block_type":"location","data":{"content":"...","location":{...}}}}

    Args:
        message: The Message object to extract from

    Returns:
        Tuple of (block_data dict, block_type string)
    """
    content = message.message
    msg_data = message.data
    block_type = "text_msg"
    block_data: dict = {}

    # Try to parse content as JSON (SDK messages come as JSON strings)
    if content and content.strip().startswith("{"):
        try:
            parsed = json.loads(content)
            outer_data = parsed.get("data", {})

            # Check for nested data structure (block format)
            # Format: {"event":"block","data":{"block_type":"location","data":{"content":"...","location":{...}}}}
            nested_data = outer_data.get("data", {}) if isinstance(outer_data, dict) else {}

            # Extract block_type from outer data first
            if outer_data.get("block_type"):
                sdk_type = outer_data["block_type"]
                block_type = SDK_BLOCK_TYPE_MAP.get(sdk_type, "text_msg")

            # Extract content - check nested data first, then outer data
            if nested_data.get("content"):
                block_data["content"] = nested_data["content"]
            elif outer_data.get("content"):
                block_data["content"] = outer_data["content"]
            else:
                block_data["content"] = content

            # Preserve structured data from both nested and outer data
            for key in ["location", "files", "metadata"]:
                if nested_data.get(key):
                    block_data[key] = nested_data[key]
                elif outer_data.get(key):
                    block_data[key] = outer_data[key]

            # Preserve event type if present
            if parsed.get("event"):
                block_data["event"] = parsed["event"]

        except json.JSONDecodeError:
            # Not valid JSON, use as plain content
            block_data["content"] = content
    else:
        block_data["content"] = content

    # Handle additional data from message.data
    if msg_data and isinstance(msg_data, dict):
        # Preserve cards from assistant responses
        if "cards" in msg_data:
            block_data["cards"] = msg_data["cards"]

        # Preserve ref_docs as metadata
        if "ref_docs" in msg_data:
            block_data["metadata"] = msg_data

        # Handle call events - block_type specified in message.data
        if msg_data.get("block_type") == "call" and "call" in msg_data:
            block_type = "call"
            block_data["call"] = msg_data["call"]

        # Handle callee messages (voice call transcripts)
        if msg_data.get("block_type") == "callee_msg":
            block_type = "callee_msg"
            if "call_ref" in msg_data:
                block_data["call_ref"] = msg_data["call_ref"]
            if msg_data.get("type"):
                block_data["type"] = msg_data["type"]

        # Handle cards block_type (provider cards, web results, etc.)
        if msg_data.get("block_type") == "cards" and "cards" in msg_data:
            block_type = "cards"

        # Handle location block_type (location requests and responses)
        if msg_data.get("block_type") == "location" and "location" in msg_data:
            block_type = "location"
            block_data["location"] = msg_data["location"]

    return block_data, block_type


def save_message_block(
    message: "Message",
    thread_id: str,
    save: bool = True,
) -> dict:
    """
    Save a block from a Message object.

    Extracts user info and content from the Message and saves to database.

    Args:
        message: The Message object to save
        thread_id: Thread identifier
        save: Whether to persist to database (default: True)

    Returns:
        Block dict with saved data
    """
    if not thread_id:
        print(f"[DEBUG] save_message_block: empty thread_id, skipping")
        return {}

    sender_user, pilot_handle = _extract_user_from_message(message)
    block_data, block_type = _extract_block_data_from_message(message)

    # Determine if we should save (system messages are not saved)
    should_save = save and pilot_handle not in ["system"]

    print(
        f"[DEBUG] save_message_block: thread_id={thread_id}, "
        f"pilot_handle={pilot_handle}, block_type={block_type}, should_save={should_save}, "
        f"content_len={len(block_data.get('content', '') or '')}"
    )

    result = save_block(
        thread_id=thread_id,
        data=block_data,
        user=sender_user,
        block_type=block_type,
        pilot_handle=pilot_handle,
        save=should_save,
    )

    print(f"[DEBUG] save_message_block result: block_id={result.get('block_id')}")
    return result


def save_message_stream_block(
    message: "Message",
    thread_id: str,
    block_id: str | None = None,
) -> tuple[str, dict]:
    """
    Save or append a streaming block from a Message object.

    Args:
        message: The Message object to save/append
        thread_id: Thread identifier
        block_id: If provided, appends to existing block

    Returns:
        Tuple of (block_id, block_data)
    """
    if not thread_id:
        return "", {}

    sender_user, pilot_handle = _extract_user_from_message(message)
    block_data, block_type = _extract_block_data_from_message(message)
    content = block_data.get("content", message.message)

    return save_stream_block(
        thread_id=thread_id,
        content=content,
        user=sender_user,
        block_type=block_type,
        pilot_handle=pilot_handle,
        block_id=block_id,
    )


def save_stream_block(
    thread_id: str,
    content: str,
    user: dict,
    block: str = "text",
    block_type: str = "text_msg",
    pilot_handle: str | None = None,
    block_id: str | None = None,
    **extra,
) -> tuple[str, dict]:
    """
    Save or append to a streaming block.

    Args:
        thread_id: Thread identifier
        content: Content to append
        user: User dict with user_id, full_name, role
        block: Block category (default: "text")
        block_type: Type of block (default: "text_msg")
        pilot_handle: Optional pilot identifier
        block_id: If provided, appends to existing block
        **extra: Additional fields to include in block data

    Returns:
        Tuple of (block_id, block_data)
    """
    if not thread_id:
        return "", {}

    block_data: dict = {
        "block": block,
        "block_type": block_type,
        "data": {"content": content, **extra},
    }
    if pilot_handle:
        block_data["pilot_handle"] = pilot_handle

    if block_id:
        # Append to existing block using MongoDB's $concat aggregation
        cond = {"block_id": block_id}
        update_data = {"data.content": {"$concat": ["$data.content", content]}}
        BlockModel._get_collection().update_one(cond, [{"$set": update_data}])
        block_data["user_id"] = user.get("user_id")
        block_data["user"] = getUser(user)
        block_data["stream"] = True
        block_data["block_id"] = block_id
        block_data["thread_id"] = thread_id
        return block_id, block_data

    # Create new block
    block_obj = processSaveBlock(block_data, user, thread_id)
    block_obj["stream"] = True
    return block_obj["block_id"], block_obj


def save_block(
    thread_id,
    data,
    user,
    block="text",
    block_type="text_msg",
    pilot_handle: str = None,
    save=True,
):
    block_data = {}
    block_data["block"] = block
    block_data["block_type"] = block_type
    block_data["data"] = {}
    if "event" in data:
        block_data["event"] = data["event"]
    if "question" in data:
        block_data["block_type"] = "question"
        block_data["data"].update(data)
    elif "messsage" in data:
        block_data["block_type"] = "text_msg"
        block_data["data"]["content"] = data["messsage"]
    elif "steps" in data:
        block_data["block_type"] = data["block_type"]
        block_data["data"].update(data)
    else:
        block_data["data"].update(data)
    if pilot_handle:
        block_data["pilot_handle"] = pilot_handle

    print(f"[DEBUG] save_block: thread_id={thread_id}, save={save}, pilot_handle={pilot_handle}")

    if save:
        block_obj = processSaveBlock(block_data, user, thread_id)
        print(f"[DEBUG] save_block: saved to DB, block_id={block_obj.get('block_id')}")
    else:
        block_obj = {
            "thread_id": thread_id,
            "user_id": user.get("user_id"),
            "user": getUser(user),
        }
        block_obj.update(block_data)
        block_obj.update(get_create_modify(utc=True))
        print(f"[DEBUG] save_block: NOT saved to DB (save=False)")
    return block_obj



def get_blocks_by_thread(thread_id: str) -> list:
    """
    Fetch all blocks for a given thread_id for verification/debugging.

    Args:
        thread_id: The thread ID to query blocks for

    Returns:
        List of block documents sorted by seq_number
    """
    if not thread_id:
        return []

    blocks = BlockModel._get_collection().find(
        {"thread_id": thread_id}
    ).sort("seq_number", 1)

    return list(blocks)


def fetch_history_by_time(thread_id, start_time, end_time):
    from bson import ObjectId

    blocks = BlockModel._get_collection().find(
        {
            "thread_id": thread_id,
            "_id": {
                "$gte": ObjectId.from_datetime(start_time),
                "$lte": ObjectId.from_datetime(end_time),
            },
        }
    )
    blocks = list(blocks)
    return [
        {
            "role": block["user"]["role"],
            "content": block["data"]["content"],
        }
        for block in blocks
    ]


def get_call_transcript(call_id: str, thread_id: str | None = None) -> list:
    """
    Fetch all transcript blocks for a specific call.

    Args:
        call_id: The call ID to query blocks for
        thread_id: Optional thread_id filter for additional scoping

    Returns:
        List of block documents sorted by call_seq
    """
    if not call_id:
        return []

    query = {
        "data.call_ref.call_id": call_id,
        "block_type": "callee_msg",
    }
    if thread_id:
        query["thread_id"] = thread_id

    blocks = BlockModel._get_collection().find(query).sort("data.call_ref.call_seq", 1)

    return list(blocks)


def get_call_summary(call_id: str, thread_id: str | None = None) -> dict | None:
    """
    Get summary information for a call including metadata and transcript stats.

    Args:
        call_id: The call ID to summarize
        thread_id: Optional thread_id filter

    Returns:
        Dict with call metadata and transcript statistics, or None if not found
    """
    if not call_id:
        return None

    # Get call status block
    call_query: dict = {
        "block_type": "call",
        "data.call.call_id": call_id,
    }
    if thread_id:
        call_query["thread_id"] = thread_id

    call_block = BlockModel._get_collection().find_one(
        call_query, sort=[("created", -1)]
    )

    # Get transcript blocks
    transcripts = get_call_transcript(call_id, thread_id)

    if not call_block and not transcripts:
        return None

    # Build summary
    call_data = call_block.get("data", {}).get("call", {}) if call_block else {}

    return {
        "call_id": call_id,
        "provider_name": call_data.get("provider_name"),
        "status": call_data.get("status"),
        "duration_seconds": call_data.get("duration_seconds"),
        "started_at": call_data.get("started_at"),
        "ended_at": call_data.get("ended_at"),
        "transcript_count": len(transcripts),
        "speakers": list(set(
            t.get("data", {}).get("call_ref", {}).get("speaker")
            for t in transcripts
            if t.get("data", {}).get("call_ref", {}).get("speaker")
        )),
    }


def get_thread_calls(thread_id: str) -> list[dict]:
    """
    Get all calls in a thread with summary info.

    Args:
        thread_id: The thread ID to query

    Returns:
        List of call summaries sorted by created time (newest first)
    """
    if not thread_id:
        return []

    # Find all call status blocks in thread
    call_blocks = BlockModel._get_collection().find(
        {"thread_id": thread_id, "block_type": "call"},
        sort=[("created", -1)]
    )

    # Get unique call_ids and their latest status
    seen_calls: dict = {}
    for block in call_blocks:
        call_data = block.get("data", {}).get("call", {})
        call_id = call_data.get("call_id")
        if call_id and call_id not in seen_calls:
            seen_calls[call_id] = {
                "call_id": call_id,
                "provider_name": call_data.get("provider_name"),
                "status": call_data.get("status"),
                "duration_seconds": call_data.get("duration_seconds"),
                "created": block.get("created"),
            }

    return list(seen_calls.values())
