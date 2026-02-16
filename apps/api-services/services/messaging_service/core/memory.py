from typing import Dict, List, Union
from fastapi import UploadFile
from libs.storage.postgres import executeQuery
from libs.storage.s3 import read_file_header
from libs.api.config import get_settings

settings = get_settings()


def getKnToken(knowledge_bases: list[str]):
    res = executeQuery(
        "SELECT token FROM space_space WHERE slug = ANY(%s)",
        (knowledge_bases,),
        many=True,
    )
    if res:
        res = [item["token"] for item in res]
        return res
    return []


async def getKnowBase(brain_id) -> Union[Dict, None]:
    space = executeQuery(
        "SELECT * FROM space_space WHERE slug=%s",
        (brain_id,),
    )
    return space


async def getAllFiles(brain_id, force_query=None) -> Union[List, None]:
    knowledgeBase = []
    space = await getKnowBase(brain_id)
    if not space:
        return []
    space_id = space["id"]
    if force_query:
        files = executeQuery(force_query, many=True)
    else:
        files = executeQuery(
            "SELECT * FROM knowledge_base_dataobjectfile WHERE knowledge_base_id=%s AND status!='indexed'",
            (space_id,),
            many=True,
        )
    for file in files:
        try:
            s3_response_object = read_file_header(
                settings.AWS_STORAGE_BUCKET_NAME, f"media/{file.get('file')}"
            )
            fileObj = s3_response_object["Body"].read()
            file["file"] = UploadFile(
                fileObj,
                filename=file.get("name"),
                size=s3_response_object["ContentLength"],
            )
            knowledgeBase.append(file)
        except Exception as ex:
            pass
    return knowledgeBase
