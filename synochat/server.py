"""Server class for combining web server and services"""

import datetime
import logging
import os
import pprint
from typing import List

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, Response, request, send_file
from model import syno
from service import reminder
from service_conf import BOT_CONF, BOT_SERVER_CONF, ServiceConf
from werkzeug.datastructures.structures import ImmutableMultiDict

SERVER_HELP_NOTE = """
~~ *Bot Basic Usage* ~~
`progress`: Show the latest progress of this bot service.
`service`: Show subscribable services.
`sub <SERVICE_NAME>`: Subscribe SERVICE.
`unsub <SERVICE_NAME>`: Unsubscribe SERVICE.
"""


SERVER_PROGRESS = """
~~ *Bot Progress* ~~
2024.07.21 -
    1. Fix request function
2024.07.27 -
    1. Restructured server.
"""

# add service name if create new service
SERVICES = """
*reminder* : hourly remind for work summary, for more info, see `help` after subscribe.
"""


class ServiceServer(Flask):
    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        bot_service_conf: ServiceConf,
    ) -> None:
        super().__init__(import_name=name)
        self.syno_api = syno.Bot(
            service_name=bot_service_conf["service_name"],
            server_url=bot_service_conf["server_url"],
            incoming_url=bot_service_conf["incoming_url"],
            token=bot_service_conf["token"],
        )
        self.schedular = BackgroundScheduler()
        # info
        self.host: str = host
        self.port: int = port
        # service
        self.agnomer: reminder.Agnomeing = reminder.Agnomeing(
            chat_api=self.syno_api, scheduler=self.schedular
        )
        # route
        self.add_url_rule("/webhook", view_func=self.webhook, methods=["POST"])
        self.add_url_rule("/download/gtu.gif", view_func=self.download_gnome_throwup)

    def run_server(self) -> None:
        self.schedular.start()
        self.run(host=self.host, port=self.port)

    def parse_input(self, event: syno.BotEvent) -> syno.ReturnDict:
        words: list[str] = event.text.split()
        command = words[0]
        ret_dict: syno.ReturnDict = {}
        if command in self.agnomer.command_keys:
            ret_dict = self.agnomer.parse_command(event)
        else:
            match command:
                case "help":
                    ret_dict["text"] = self.show_help(event)
                case "service":
                    ret_dict["text"] = self.show_service()
                case "progress":
                    ret_dict["text"] = self.show_progress(event)
                case "sub":
                    ret_dict["text"] = self.register_service(event, True)
                case "unsub":
                    ret_dict["text"] = self.register_service(event, False)
                case _:
                    ret_dict = self.check_input(event)

        logging.debug(f"parsed result:{ret_dict}")
        return ret_dict

    def check_input(self, event: syno.PostEvent) -> syno.ReturnDict:
        if (event.user_id not in self.agnomer._sub_id) or (
            not self.agnomer._sub_list[event.user_id].wait_for_reply
        ):
            # throw up and return app
            words: list[str] = event.text.split()
            command: str = words[0]
            paras: List[str] = words[1:]
            ret_text: str = (
                f'unknown command: {command}\nTry "help" for current available services'
                + " "
                + " ".join(paras)
            )
            return {"text": ret_text, "file_url": f"{request.host_url}download/gtu.gif"}

        self.agnomer._sub_notes[event.user_id][
            self.agnomer._sub_list[event.user_id].idx_hour - 1
        ] += "\n" + event.text
        self.agnomer._sub_list[event.user_id].wait_for_reply = False
        ret: str = (
            f"Note taken for hour {self.agnomer._sub_list[event.user_id].idx_hour}"
        )

        return {"text": ret}

    def show_help(self, event: syno.PostEvent) -> str:
        # show appended help
        # check sub for services
        help_note = SERVER_HELP_NOTE
        if event.user_id in self.agnomer._sub_id:
            help_note += "\n" + self.agnomer.help

        return help_note

    def show_progress(self, event: syno.PostEvent) -> str:
        progress = SERVER_PROGRESS
        if event.user_id in self.agnomer._sub_id:
            progress += "\n" + self.agnomer.progress

        return progress

    def show_service(self) -> str:
        """Show available services

        Returns:
            str: service list
        """
        list_service = "Current available services:"
        return list_service + SERVICES

    def register_service(self, event: syno.PostEvent, sub: bool):
        words: list[str] = event.text.split()
        service_name: str = words[1] if len(words) > 1 else " "
        match service_name:
            case "reminder":
                return self.agnomer.register(event, sub)
            case _:
                return (
                    f"Unknow services:'{service_name}'.\n"
                    "Use `services` to see availible services"
                )

    # routes

    def webhook(self) -> syno.ReturnDict:
        # Parse URL-encoded form data
        form_data: ImmutableMultiDict[str, str] = request.form
        logging.debug(f"raw_request:{pprint.pformat(form_data)}")
        event = syno.BotEvent(
            token=form_data["token"],
            user_id=int(form_data["user_id"]),
            username=form_data["username"],
            post_id=int(form_data["post_id"]),
            thread_id=int(form_data["thread_id"]),
            timestamp=datetime.datetime.fromtimestamp(
                float(form_data["timestamp"]) / 1000.0
            ),
            text=form_data["text"],
        )
        if not event:
            logging.error(f"empty event catched, may have a error? event:{event}")
        logging.debug(f"Raw event:{event}")

        ret_dict: syno.ReturnDict = self.parse_input(event)

        return ret_dict

    def download_gnome_throwup(self) -> Response:
        path: str = os.path.abspath("./assets/gtu_s.gif")
        return send_file(path, as_attachment=False)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    scheduler = BackgroundScheduler()
    service_server = ServiceServer(
        name=__name__,
        host=BOT_SERVER_CONF["ip"],
        port=BOT_SERVER_CONF["port"],
        bot_service_conf=BOT_CONF,
    )
    service_server.run_server()
