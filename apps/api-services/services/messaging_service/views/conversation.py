from services.messaging_service.core.block_processor import convert_files_url
from libs.core.jsondecoder import convertFromMongo
from libs.core.pagination import paginateData
from services.messaging_service.models.conversation import (
    BlockModel,
    BlockReactionModel,
)


def fetchBlocks(thread_id: str, request):
    query = {"thread_id": thread_id, "is_active": True}
    projection = {
        "thread_id",
        "block_id",
        "block",
        "block_type",
        "data",
        "media",
        "seq_number",
        "created",
        "user_id",
        "user",
        "reaction_count",
        "parent_id",
        "parent",
    }
    data = paginateData(
        BlockModel, request, mongo=True, query=query, projection=projection
    )
    data["data"].reverse()
    for block in data["data"]:
        if "files" in block.get("data", {}) and block["data"]["files"]:
            block["data"]["files"] = convert_files_url(block["data"]["files"])
    return {**data, "message": "Successfully fetched blocks"}


def createBlockReaction(block, data, user):
    reaction = BlockReactionModel.save_single_to_db(
        {
            "block_id": block.block_id,
            "thread_id": block.thread_id,
            "user_id": user["user_id"],
            "reaction_type": data.reaction_type,
            "reaction_count": data.reaction_count,
        }
    )
    BlockModel._get_collection().update_one(
        {"block_id": block.block_id}, {"$inc": {"reaction_count": data.reaction_count}}
    )
    return {
        "message": "",
        "data": {"reaction": True, "reaction_count": data.reaction_count},
    }


def fetchAnswer(thread_id: str):
    query = {
        "thread_id": thread_id,
        "is_active": True,
        "block_type": {"$ne": "sys_msg"},
    }
    projection = {
        "thread_id",
        "block_id",
        "block",
        "block_type",
        "data",
        "media",
        "seq_number",
        "user",
    }
    data = BlockModel._get_collection().find_one(query, projection=projection)
    data = convertFromMongo(data)
    if data:
        if "files" in data.get("data", {}) and data["data"]["files"]:
            data["data"]["files"] = convert_files_url(data["data"]["files"])
    return {"message": "", "data": data or {}}


def deleteBlock(block_id: str, user: str):
    user_id = user["user_id"]
    delete_count = (
        BlockModel._get_collection()
        .delete_one({"block_id": block_id, "user_id": user_id})
        .deleted_count
    )
    if delete_count == 0:
        return {"message": "You can't delete others comment/block"}, True
    return {"message": "Successfully deleted block"}, False
