from mongomantic import BaseRepository
from libs.core.datetime import get_modify


def updateModelInstance(model: BaseRepository, condition, update_data):
    if isinstance(update_data, dict):
        update_data.update(get_modify())
    model.update_one(condition, update_data)
    return True
