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
~~ *Me Gnome here* ~~
Usage:
`progress`: Show the latest progress of this bot.
"""


SERVER_PROGRESS = """
2024.07.19 -
    1. Fix message length bug.
    2. Add daily reset method.
2024.07.21 -
    1. Fix request function

To-Do list:
    * _print_status log need to be a function
    * add append feature
    * add skip feature
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
        self.agnomer: reminder.Agnomeing = reminder.Agnomeing()
        # route
        self.add_url_rule("/webhook", view_func=self.webhook, methods=["POST"])
        self.add_url_rule("/download/gtu.gif", view_func=self.download_gnome_throwup)

    def run_server(self) -> None:
        self.schedular.start()
        self.run(host=self.host, port=self.port)

    def report_unknown(self, event: syno.PostEvent) -> syno.ReturnDict:
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

    def parse_input(self, event: syno.PostEvent) -> syno.ReturnDict:
        words: list[str] = event.text.split()
        command = words[0]
        ret_dict: syno.ReturnDict = {}
        match command:
            case "help":
                ret_dict["text"] = SERVER_HELP_NOTE
            case "progress":
                ret_dict["text"] = SERVER_PROGRESS
            case _:
                ret_dict = self.report_unknown(event)

        logging.debug(f"parsed result:{ret_dict}")
        return ret_dict

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
        schedular=scheduler,
        host=BOT_SERVER_CONF["ip"],
        port=BOT_SERVER_CONF["port"],
        bot_service_conf=BOT_CONF,
    )
    service_server.run_server()
