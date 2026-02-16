# Fix for Pydantic v2 compatibility with mongomantic OID validator
from bson import ObjectId
from bson.objectid import InvalidId

from super_services.libs.core.datetime import get_modify


# Monkey patch the OID validator to work with Pydantic v2
def _patched_oid_validate(cls, v, _info=None):
    """Fixed OID validator that works with both Pydantic v1 and v2"""
    try:
        return ObjectId(str(v))
    except InvalidId:
        raise ValueError("Invalid object ID")

# Apply the patch
try:
    from mongomantic.core.mongo_model import OID
    OID.validate = classmethod(_patched_oid_validate)
except ImportError:
    pass  # If mongomantic is not available, skip the patch

from mongomantic import BaseRepository


def updateModelInstance(model: BaseRepository, condition, update_data):
    if isinstance(update_data, dict):
        update_data.update(get_modify())
    model.update_one(condition, update_data)
    return True
