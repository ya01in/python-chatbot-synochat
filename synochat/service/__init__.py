from model import syno
from service_conf import BOT_CONF, CHANNEL_SERVICE_CONF

study_bot = syno.Bot(
    service_name=BOT_CONF["service_name"],
    server_url=BOT_CONF["server_url"],
    incoming_url=BOT_CONF["incoming_url"],
    token=BOT_CONF["token"],
)

study_service = syno.ChatService(
    service_name=CHANNEL_SERVICE_CONF["service_name"],
    server_url=CHANNEL_SERVICE_CONF["server_url"],
    incoming_url=CHANNEL_SERVICE_CONF["incoming_url"],
    token=CHANNEL_SERVICE_CONF["token"],
)
