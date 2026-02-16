def reverseDict(data: dict):
    final = {}
    for key, value in data.items():
        if value and not isinstance(value, dict):
            final[value] = key
    return final


def checkKeyValue(data, key):
    if key in data and data[key] and data[key] != '':
        return True
    return False
