from typing import TypedDict

SERVER_URL = "https://192.168.1.101:5001"


class ServerConf(TypedDict):
    port: int
    ip: str


class ServiceConf(TypedDict):
    service_name: str
    server_url: str
    incoming_url: str
    token: str


BOT_CONF = ServiceConf(
    **{
        "service_name": "Bot1",
        "server_url": SERVER_URL,
        "incoming_url": (
            "http://192.168.1.101:5000/webapi/entry.cgi?api=SYNO.Chat.External&method=chatbot&version=2&"
            "token=%22QGcBpMie68ttKEdQPBWd1CwdzZgOiAjAJAkE4xhTftaQEdt79zXWwMgGIfVDvYa6%22"
        ),
        "token": "QGcBpMie68ttKEdQPBWd1CwdzZgOiAjAJAkE4xhTftaQEdt79zXWwMgGIfVDvYa6",
    }
)


CHANNEL_SERVICE_CONF = ServiceConf(
    **{
        "service_name": "Service2",
        "server_url": SERVER_URL,
        "incoming_url": (
            "https://chat.synology.com/webapi/entry.cgi?api=SYNO.Chat.External&method=incoming&version=2&"
            "token=%22zbjPx8KzqLknV21YLP3jD8gTVj6NQl5sUQT0ochPVQAQTn23fQc1PBI1zQvLCDuf%22"
        ),
        "token": "G9ZQiNZxUQG4SMlvrHlyfSFQblrk1mPYYpeWmJFgpevv5VIw8SrDBn40LEwZWuYw",
    }
)

STUDY_CONF = ServerConf(port=5008, ip="192.168.1.103")

BOT_CONF_AUTOPAL = ServerConf(port=5009, ip="192.168.1.103")
