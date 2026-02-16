from decimal import Decimal
import decimal
import json
from datetime import datetime
from bson import ObjectId, Decimal128
from starlette.responses import JSONResponse
from libs.core.constant import DATETIME_FORMAT


def fetchError(errors):
    error_list = []
    for err in errors:
        msg = err.get("msg", "Invalid Value")
        err_mgs = {"errorCode": "InvalidValue", "errorMessage": msg}
        loc = list(err.get("loc", []))
        if len(loc) and loc[0] != "__root__":
            loc = list(map(str, loc))
            field = ".".join(loc)
            err_mgs["field"] = field
        error_list.append(err_mgs)
    return error_list


class MongoJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime(DATETIME_FORMAT)
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, decimal.Decimal):
            return float(str(obj))
        return json.JSONEncoder.default(self, obj)


def json_dumps(obj, **kwargs):
    return json.dumps(obj, cls=MongoJsonEncoder, **kwargs)


def convertMongo(obj):
    if "id" in obj:
        obj["_id"] = str(obj.pop("id"))
    if "_id" in obj:
        obj["id"] = str(obj.pop("_id"))
        # obj['id'] = str(obj['_id'])
    obj = json.dumps(obj, cls=MongoJsonEncoder)
    return json.loads(obj)


def convertFromMongo(obj):
    if isinstance(obj, list):
        for o in obj:
            o = convertMongo(o)
    elif isinstance(obj, dict):
        obj = convertMongo(obj)
    return obj


def convertFromBaseModel(obj):
    if not obj:
        return obj
    final_data = dict()
    if isinstance(obj, list):
        final_data = []
        for o in obj:
            final_data.append(convertFromBaseModel(o))
    elif isinstance(obj, dict):
        final_data = convertMongo(obj)
    else:
        final_data = convertMongo(obj.dict())
    return final_data


def customResponse(res, error=False):
    if error:
        status_code = 206
        if "success" not in res:
            res["success"] = False
        if "error" in res:
            res["message"] = res.pop("error")
        if "status_code" in res:
            status_code = res.pop("status_code")
        if "data" not in res:
            res["data"] = {}
        return JSONResponse(res, status_code=status_code)
    else:
        final_res = {}
        final_res["success"] = True
        final_res["message"] = res.pop("message", "Success")
        if "count" in res:
            final_res["count"] = res.pop("count")
        final_res["data"] = res.pop("data", res)
        return final_res


def convert_decimal(dict_item):
    if dict_item is None:
        return None
    if not isinstance(dict_item, dict):
        return dict_item
    for k, v in list(dict_item.items()):
        if isinstance(v, dict):
            convert_decimal(v)
        elif isinstance(v, list):
            for l in v:
                convert_decimal(l)
        elif isinstance(v, Decimal):
            dict_item[k] = Decimal128(str(v))

    return dict_item
