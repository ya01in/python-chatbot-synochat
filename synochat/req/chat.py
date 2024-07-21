import json
import logging
from typing import Any, Dict

import requests


class WebhookPostService:
    def __init__(self, incoming_webhook_url) -> None:
        self.income_wh_url: str = incoming_webhook_url

    def send_message(
        self, response_text: str = "", user_id: int = -1, file_url: str = ""
    ) -> None:
        message: Dict[str, Any] = {
            "text": response_text,
        }
        if user_id != -1:
            message["user_ids"] = [int(user_id)]

        if file_url:
            message["file_url"] = file_url

        payload: str = "payload=" + json.dumps(message)
        try:
            response: requests.Response = requests.post(self.income_wh_url, payload)
            response.raise_for_status()  # Raise an exception if the response contains an HTTP error
        except requests.exceptions.RequestException as e:
            logging.error(f"Error sending message to Synology Chat: {e}")

        logging.debug(f"Sent message:{payload} to user_id:{user_id}")


class WebhookGetService:
    def __init__(self, chat_server: str, token: str) -> None:
        self.wh_token: str = token
        self.chat_server: str = chat_server

    def check_aval_users(self):
        check_url: str = f"{self.chat_server}/webapi/entry.cgi?api=SYNO.Chat.External&method=user_list&version=2"
        token: str = "token=" + self.wh_token
        try:
            response: requests.Response = requests.get(
                check_url,
                token,
            )
            # response = requests.post(INCOMING_WEBHOOK_URL, json=payload)
            response.raise_for_status()  # Raise an exception if the response contains an HTTP error
        except requests.exceptions.RequestException as e:
            logging.error(f"Error sending message to Synology Chat: {e}")
            return "Error sending message to Synology Chat", 500

        data = response.json()
        logging.debug(f"aval users json data:{data}")
        return data["data"]["users"]

    def check_aval_channels(self) -> requests.Response:
        check_url: str = f"{self.chat_server}//webapi/entry.cgi?api=SYNO.Chat.External&method=channel_list&version=2"

        token: str = "token=" + self.wh_token
        try:
            response: requests.Response = requests.get(
                check_url,
                token,
            )
            # response = requests.post(INCOMING_WEBHOOK_URL, json=payload)
            response.raise_for_status()  # Raise an exception if the response contains an HTTP error
        except requests.exceptions.RequestException as e:
            # print(f"Error sending message to Synology Chat: {e}")
            # return "Error sending message to Synology Chat", 500
            raise e
        data = response.json()
        logging.debug(f"aval channel json data:{data}")
        return response


if __name__ == "__main__":
    from synochat.service_conf import BOT_CONF, CHANNEL_SERVICE_CONF

    logging.basicConfig(level=logging.DEBUG)

    AUTO_SPEAKER = "https://chat.synology.com/webapi/entry.cgi?api=SYNO.Chat.External&method=incoming&version=2&token=%2280k4CJ6BssSWhIzREAHYlOXvXDBYHhKy8deHstAV7k3TyI3RVHrDq3XwB8W3AjIs%22"

    chat_server = "https://chat.synology.com"

    channel_get_service = WebhookGetService(
        CHANNEL_SERVICE_CONF["server_url"],
        token=CHANNEL_SERVICE_CONF["token"],
    )

    channel_post_service = WebhookPostService(
        incoming_webhook_url=CHANNEL_SERVICE_CONF["incoming_url"],
    )

    bot_get_service = WebhookGetService(BOT_CONF["server_url"], token=BOT_CONF["token"])

    bot_post_service = WebhookPostService(incoming_webhook_url=BOT_CONF["incoming_url"])

    users = bot_get_service.check_aval_users()

    # pprint.pprint(users[0])

    # for user in users:
    #     if user['username'] == 'nicholasli':
    #         # pprint.pprint(user)

    bot_post_service.send_message(
        response_text="test",
        user_id=5971,
    )
    # users = get_service.check_aval_users()

    # user_data_list: list[UserData] = [UserData(**user) for user in users]

    # logging.info(f'Current user count: {len(user_data_list)}')
    # pprint.pprint()
    # post_service.send_back_message(response_text="我們的工具齊全了")
