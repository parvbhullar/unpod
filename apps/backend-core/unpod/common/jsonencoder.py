from bson import Decimal128, ObjectId
from django.core.serializers.json import DjangoJSONEncoder


class MongoJsonEncoder(DjangoJSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, Decimal128):
            return str(o)
        return super(MongoJsonEncoder, self).default(o)
