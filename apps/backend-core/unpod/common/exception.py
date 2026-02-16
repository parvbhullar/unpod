from rest_framework.exceptions import APIException


class APIException206(APIException):
    status_code = 206


class APIException200(APIException):
    status_code = 200


class APIException401(APIException):
    status_code = 401


class ImageNotFound(Exception):
    pass


class MongoDBQueryNotFound(ValueError):
    pass
