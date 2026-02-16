from fastapi import APIRouter, HTTPException

from services.store_service.models.connector import ConnectorModel
from services.store_service.schemas.connector import (
    ConnectorBase,
    ConnectorListResponse,
    StatusResponse,
)
from libs.api.logger import get_logger

app_logging = get_logger("store_service")

router = APIRouter()


@router.get("/connector")
def get_connectors() -> list[ConnectorListResponse]:
    connectors = ConnectorModel.find_many()
    results = []
    for c in connectors:
        results.append(
            ConnectorListResponse(
                id=str(c.id),
                name=c.name,
                source=c.source,
                input_type=c.input_type,
                connector_specific_config=c.connector_specific_config,
                refresh_freq=c.refresh_freq,
                prune_freq=c.prune_freq,
                disabled=c.disabled,
            )
        )
    return results


@router.post("/connector")
def store_connector_config(connector_data: ConnectorBase) -> StatusResponse:
    try:
        existing = ConnectorModel.find_one(
            name=connector_data.name, source=connector_data.source
        )
        if existing:
            update_data = connector_data.model_dump()
            for key, value in update_data.items():
                setattr(existing, key, value)
            ConnectorModel.save_single_to_db(existing.model_dump())
            return StatusResponse(
                success=True,
                message="Connector updated successfully",
                data=str(existing.id),
            )
        else:
            result = ConnectorModel.save_single_to_db(connector_data.model_dump())
            return StatusResponse(
                success=True,
                message="Connector created successfully",
                data=str(result.id) if result else None,
            )
    except Exception as e:
        app_logging.error(f"Error creating/updating connector: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/connector/{connector_id}")
def delete_connector_config_by_id(connector_id: str) -> StatusResponse:
    try:
        connector = ConnectorModel.find_one_by_id(connector_id)
        if connector is None:
            return StatusResponse(
                success=True,
                message="Connector was already deleted",
                data=connector_id,
            )
        ConnectorModel.delete_by_id(connector_id)
        return StatusResponse(
            success=True,
            message="Connector deleted successfully",
            data=connector_id,
        )
    except Exception as e:
        app_logging.error(f"Error deleting connector: {e}")
        raise HTTPException(status_code=400, detail="Connector is not deletable")


@router.put("/connector/{connector_id}")
def update_connector_config(
    connector_id: str, connector_data: ConnectorBase
) -> ConnectorBase:
    connector = ConnectorModel.find_one_by_id(connector_id)
    if connector is None:
        raise HTTPException(
            status_code=404, detail=f"Connector {connector_id} does not exist"
        )

    update_data = connector_data.model_dump()
    for key, value in update_data.items():
        setattr(connector, key, value)
    ConnectorModel.save_single_to_db(connector.model_dump())

    return ConnectorBase(
        name=connector.name,
        source=connector.source,
        input_type=connector.input_type,
        connector_specific_config=connector.connector_specific_config,
        refresh_freq=connector.refresh_freq,
        prune_freq=connector.prune_freq,
        disabled=connector.disabled,
    )


@router.get("/connector/{connector_id}")
def get_connector_by_id(connector_id: str) -> ConnectorBase | None:
    connector = ConnectorModel.find_one_by_id(connector_id)
    if connector is None:
        return None

    return ConnectorBase(
        name=connector.name,
        source=connector.source,
        input_type=connector.input_type,
        connector_specific_config=connector.connector_specific_config,
        refresh_freq=connector.refresh_freq,
        prune_freq=connector.prune_freq,
        disabled=connector.disabled,
    )
