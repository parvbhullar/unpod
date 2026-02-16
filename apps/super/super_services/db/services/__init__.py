from mongomantic import connect
from super_services.libs.config import settings

connect(settings.MONGO_DSN, settings.MONGO_DB)