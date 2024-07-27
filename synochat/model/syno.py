import dataclasses
import datetime
import logging
from typing import Optional, TypedDict

from api import chat


class ReturnDict(TypedDict, total=False):
    text: str
    file_url: Optional[str]


@dataclasses.dataclass
class KeyPair:
    public_key: str  # ''


@dataclasses.dataclass
class UserProp:
    avatar_color: str  # '#4cbf73',
    description: str  # 'Ingrid Chiu',
    email: str  # 'Ingridchiu@synology.com'
    key_pair: KeyPair
    timezone: str  # ''
    timezoneUTC: str  # 'Asia/Taipei'


@dataclasses.dataclass
class UserData:
    avatar_version: int
    deleted: bool
    dsm_uid: int
    first_time_login: bool  # False
    human_type: str  # 'dsm'
    is_disabled: bool
    nickname: str
    status: str  # 'online'
    type: str  # 'human'
    user_id: int  # 7708
    username: str  # 'Ingridchiu'
    user_props: UserProp


@dataclasses.dataclass
class PostEvent:
    token: str  # 'G9ZQiNZxUQG4SMlvrHlyfSFQblrk1mPYYpeWmJFgpevv5VIw8SrDBn40LEwZWuYw',
    user_id: int  # nt '5971'
    username: str  # 'nicholasli'
    post_id: int  # 1233746535650568'
    thread_id: int  # nt '0'
    timestamp: datetime.datetime  # nt '1720000284907'
    text: str  # 'stk helloworld'


@dataclasses.dataclass
class BotEvent(PostEvent):
    pass


@dataclasses.dataclass
class ServiceEvent(PostEvent):
    channel_id: int = -1  # nt '287254',
    channel_type: int = -1  # nt '1',
    channel_name: str = ""  # '排程機器人功能測試與改進',
    trigger_word: str = ""  # 'stk'


class ChatService:
    """Service for chat

    typically, a channel service is used for announcing info, so the
    url_incoming is fixed, and token_outgoing is optional
    """

    def __init__(
        self,
        service_name: str,
        server_url: str,
        incoming_url: str,
        token: Optional[str] = "",
    ) -> None:
        self.name: str = service_name
        self.server: str = server_url
        self._url_incoming: str = incoming_url
        self._token: Optional[str] = token

        self.web_post = chat.WebhookPostService(self._url_incoming)
        self.web_get: chat.WebhookGetService | None = (
            chat.WebhookGetService(self.server, self._token) if self._token else None
        )

        if self.web_get is None:
            logging.warning(f"ChatService with Name:{self.name} has no get service.")


@dataclasses.dataclass
class Bot(ChatService):
    """Bot service for chat
    A bot service contains both input and output
    change the token to be fixed
    """

    def __init__(
        self,
        service_name: str,
        server_url: str,
        incoming_url: str,
        token: str,
    ) -> None:
        super().__init__(service_name, server_url, incoming_url, token)
