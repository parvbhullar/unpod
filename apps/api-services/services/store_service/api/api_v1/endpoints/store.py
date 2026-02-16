from typing import List
from fastapi import APIRouter, Request

from libs.core.jsondecoder import customResponse
from libs.core.pagination import getPagination
from services.store_service.schemas.collection import (
    BulkUpdateItem,
    CollectionFile,
    CollectionStoreConfig,
    CollectionStoreConfigUpdate,
)
from services.store_service.views.collection import (
    check_upload_status,
    fetch_collection_data,
    processUploadFileOld,
    storeCollectionConfig,
    getStoreConfig,
    updateCollectionConfig,
)
from services.store_service.views.connector import (
    fetch_collector_based_data,
    fetch_doc_info,
    update_doc_info,
    delete_doc_info,
    create_doc_info,
    bulk_update_docs,
)

router = APIRouter()


@router.get("/health")
async def health(request: Request):
    return customResponse({"status": 200}, False)


@router.post("/config/")
async def config(data: CollectionStoreConfig, request: Request):
    return customResponse(storeCollectionConfig(data))


@router.get("/config/{token}/")
async def getConfig(token: str, request: Request):
    return customResponse(await getStoreConfig(token))


@router.put("/config/{token}/")
async def updateConfig(token: str, data: CollectionStoreConfigUpdate, request: Request):
    return customResponse(await updateCollectionConfig(data, token))


@router.post("/upload-file/{token}/")
async def uploadProcessFile(token: str, file: CollectionFile, request: Request):
    return customResponse(await processUploadFileOld(file, token))


@router.get("/upload-status/{token}/")
async def checkUploadStatus(token: str, request: Request):
    return customResponse(await check_upload_status(token))


@router.get("/collection-data/{token}/")
async def collectionData(token: str, request: Request):
    skip, limit = getPagination(request)
    return customResponse(await fetch_collection_data(token, limit, skip))


@router.get("/collection-connector-data/{token}/")
async def collectionConnectorData(token: str, request: Request):
    skip, limit = getPagination(request)
    query_params = request.query_params._dict
    return customResponse(
        await fetch_collector_based_data(token, limit, skip, query_params)
    )


@router.get("/collection-doc-data/{token}/{document_id}")
async def collectionDocData(token: str, document_id: str, request: Request):
    return customResponse(await fetch_doc_info(token, document_id))


@router.post("/collection-doc-data/{token}/{document_id}")
async def update_collection_doc(
    token: str, document_id: str, data: dict, request: Request
):
    return customResponse(await update_doc_info(token, document_id, data))


@router.delete("/collection-doc-data/{token}/{document_id}")
async def delete_collection_doc(token: str, document_id: str, request: Request):
    return customResponse(await delete_doc_info(token, document_id))


@router.post("/collection-doc-data/{token}")
async def create_collection_doc(token: str, data: dict, request: Request):
    return customResponse(await create_doc_info(token, data))


@router.post("/collection-doc-bulk-update/{token}")
async def bulk_update_collection_docs(
    token: str, data: List[BulkUpdateItem], request: Request
):
    return customResponse(await bulk_update_docs(token, data))


@router.get("/scrape-website/")
async def scrape_website(url: str, request: Request):
    from services.store_service.views.exa_ai_scarpper import scrape_website

    return customResponse(scrape_website(url))
