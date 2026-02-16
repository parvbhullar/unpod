def getFromDict(dataDict, maplist):
    first, rest = maplist[0], maplist[1:]

    if rest:
        return getFromDict(dataDict[first], rest)
    else:
        return dataDict[first]


def setInDict(dataDict, maplist, value):
    first, rest = maplist[0], maplist[1:]
    if rest:
        try:
            if not isinstance(dataDict[first], dict):
                dataDict[first] = {}
        except KeyError:
            dataDict[first] = {}
        setInDict(dataDict[first], rest, value)
    else:
        dataDict[first] = value


def removeKeyFromDict(dataDict: dict, Keys=[]):
    for key in Keys:
        if key in dataDict:
            dataDict.pop(key)
    return dataDict


def is_valid_value(value):
    if value not in (None, ""):
        return True
    return False


def check_key_value(obj_or_dict, key):
    if not obj_or_dict:
        return False

    if isinstance(obj_or_dict, dict):
        if key in obj_or_dict and is_valid_value(obj_or_dict[key]):
            return True
    else:
        value = getattr(obj_or_dict, key, None)
        if is_valid_value(value):
            return True
    return False


def check_dict_is_empty(data: dict):
    if not data:
        return True
    return all(not value for value in data.values())
