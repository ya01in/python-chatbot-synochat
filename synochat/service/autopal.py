import datetime
import logging
import os
import pprint
from typing import Dict, List, Set

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import Flask, Response, request, send_file
from model import chat_event, subscribe
from model.lc import Challenge
from req.daily import RequestHandler, RequestParser
from service import study_bot
from werkzeug.datastructures.structures import ImmutableMultiDict

HELP_NOTE = """
~~ *Me Gnome here* ~~
Usage:
`progress`: Show the latest progress of this machine.
`sub`: Subscribe to hourly check-in and log service. Enable after subscribe to hourly logging service.
`unsub`: Unsubscribe to hourly check-in and log service. Enable after subscribe to hourly logging service.
`on`: Start daily timer. Enable after subscribe to hourly logging service.
`log`: Show accumulated log of today. Enable after subscribe to hourly logging service.
    In the format of below:
```
on_time: 09:32(24 format)
Logs:
1(0932 - 1032): get breakfast, write email
2(1032 - 1132):
    Ask for 180 HDD drive
    Check on deploy machine
    Deploy env for package XX verification.
```
`amend` <Nth_HOUR> <LOG_MESSAGE>: Amend Nth_HOUR hour log with LOG_MESSAGE.
    Nth_Hour: 1 ~ 10
    LOG_MESSAGE: one or multiple lines of strings
    this will output the original log and log the next input. Enable after subscribe to hourly logging service.
    e.g. amend 2 "verifying bug #8964"
>   Amend hour 2 log from "" to "verifying bug #8964"
(unavailable) skip [YYYY-MM-DD, YYYY-MM-DD]: skip date(s), used for skipping days when taking day off.
    Enable after subscribe to hourly logging service.
~lc: Get daily supplement~
"""


PROGRESS = """
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


class AutoPal(Flask):
    def __init__(
        self,
        import_name: str,
        static_url_path: str | None = None,
        static_folder: str | os.PathLike[str] | None = "static",
        static_host: str | None = None,
        host_matching: bool = False,
        subdomain_matching: bool = False,
        template_folder: str | os.PathLike[str] | None = "templates",
        instance_path: str | None = None,
        instance_relative_config: bool = False,
        root_path: str | None = None,
    ) -> None:
        super().__init__(
            import_name=import_name,
            static_url_path=static_url_path,
            static_folder=static_folder,
            static_host=static_host,
            host_matching=host_matching,
            subdomain_matching=subdomain_matching,
            template_folder=template_folder,
            instance_path=instance_path,
            instance_relative_config=instance_relative_config,
            root_path=root_path,
        )
        self._sub_list: Dict[int, subscribe.SubInfo] = {}
        self._sub_id: Set[int] = set()
        self._sub_notes: Dict[int, List[str]] = {}

    def parse_service(self, event: chat_event.PostEvent) -> str:
        words: list[str] = event.text.split()
        command = words[0]
        ret: str = ""
        match command:
            case "help":
                ret = HELP_NOTE
            case "sub":
                ret = self.register(event, True)
            case "unsub":
                ret = self.register(event, False)
            case "log":
                self.show_log(event)
                ret = ""
            case "amend":
                ret = self.amend(event)
            case "progress":
                ret = PROGRESS
            case "lc":
                ret = self.leetcode()
            case "on":
                ret = self.onboard(event)
            case "note":
                ret = self.note(event)
            case "_print_status":
                self._print_status(event)
            case "_set_on":
                ret = self._set_on_time(event)
            # case 'note':
            #     ret = 'NotImplementedError'
            # case 'off':
            #     ret = 'NotImplementedError'
            # case 'skip':
            #     ret = 'NotImplementedError'
            case _:
                ret = self.check_for_note(event)

        logging.debug(f"parsed result:{ret}")
        return ret

    def leetcode(self):
        challenge_info = RequestHandler.get_challenge_info()
        challenge: Challenge = RequestParser.parse(challenge_info)
        response_text: str = f"""
Today's challenge: {challenge.title}
Difficulty: {challenge.difficulty}
ID: {challenge.question_id}
Link: {challenge.problem_link}
Success rate: {challenge.ac_rate}
Go for a shot!!!
"""
        return response_text

    def throw_up(self, user_id) -> None:
        study_bot.web_post.send_message(
            response_text="what is that?",
            user_id=user_id,
            file_url=f"{request.host_url}download/gtu.gif",
        )

    def _print_status(self, event) -> None:
        study_bot.web_post.send_message(
            response_text=pprint.pformat(self._sub_id),
            user_id=event.user_id,
        )
        study_bot.web_post.send_message(
            response_text=pprint.pformat(self._sub_list),
            user_id=event.user_id,
        )
        study_bot.web_post.send_message(
            response_text=pprint.pformat(self._sub_notes),
            user_id=event.user_id,
        )

    def register(self, event: chat_event.PostEvent, sub: bool):
        # check if sub
        username, userid = event.username, event.user_id
        is_sub: bool = True if event.user_id in self._sub_id else False
        output: str = ""
        # determin what to do
        if sub:
            if is_sub:
                logging.debug(
                    f"user:{event.username} is trying to subscribe but already is a subscriber."
                )
                output = 'You are already subscribed. if you need to unsubscribe, use "unsub"'
            else:
                today: datetime.datetime = datetime.datetime.today()
                self._sub_id.add(userid)
                self._sub_list[userid] = subscribe.SubInfo(
                    wait_for_reply=False,
                    wait_time=datetime.datetime.now(),
                    u_id=userid,
                    u_name=username,
                    sub_time=event.timestamp,
                    on_time=datetime.datetime(
                        year=today.year,
                        month=today.month,
                        day=today.day,
                        hour=10,
                        minute=30,
                    ),
                    idx_hour=0,
                )
                self._sub_notes[userid] = [""] * 10
                logging.info(
                    f"{username} subscribed, current sub list:{pprint.pformat(self._sub_list)}"
                )
                output = "Subscribe successful. see usage for functions"
        else:
            if is_sub:
                self._sub_id.remove(userid)
                self._sub_list.pop(userid)
                logging.info(
                    f"{username} unsubscribed, current sub list:{pprint.pformat(self._sub_list)}"
                )
                output = "Unubscribed successful."
            else:
                logging.debug(
                    f"user:{event.username} is not a subscriber but trying to unsubscribe."
                )
                output = 'You are not subscribed. if you need to subscribe, use "sub"'

        return output

    def angnome(self) -> None:
        # hourly reminder
        now: datetime.datetime = datetime.datetime.now()
        # if now.hour < 22 and now.hour > 8:
        if now:
            logging.info("Start angnome")
            remind_list: List[subscribe.SubInfo] = []
            for _uid, subinfo in self._sub_list.items():
                diff_time: float = (now - subinfo.on_time).total_seconds()
                logging.debug(
                    f"User:{subinfo.u_name}, idx_hour:{subinfo.idx_hour} total diff second:{diff_time}"
                )
                if (diff_time > 3600) and (diff_time % 3600 < 60):
                    remind_list.append(subinfo)
            logging.info(f"Found user needs to remind:{remind_list}")
            for subinfo in remind_list:
                study_bot.web_post.send_message(
                    response_text="This is your hourly reminder, what were you doing for the last hour?",
                    user_id=subinfo.u_id,
                )
                self._sub_list[subinfo.u_id].wait_for_reply = True
                self._sub_list[subinfo.u_id].idx_hour = int(
                    (now - subinfo.on_time).total_seconds() // 3600
                )
                logging.debug(
                    f"User:{subinfo.u_name} data after remind:{pprint.pformat(self._sub_list[subinfo.u_id])}"
                )
                logging.info(f"Reminded user:{subinfo.u_name} to log hour status")

    def clean_gnome(self) -> None:
        logging.debug("Start cleaning gnome")
        for uid in self._sub_id:
            today: datetime.datetime = datetime.datetime.today()
            self._sub_list[uid].on_time = datetime.datetime(
                year=today.year, month=today.month, day=today.day, hour=10, minute=30
            )
            self._sub_list[uid].idx_hour = 0
            self._sub_notes[uid] = [""] * 10
            logging.debug(f"user:{self._sub_list[uid].u_name} have been clear")
        logging.info("Finished cleaning all the gnomes.")

    def check_for_note(self, event: chat_event.PostEvent) -> str:
        is_sub: bool = True if event.user_id in self._sub_id else False
        if not is_sub:
            logging.debug(f"user:{event.username} is not sub")
            self.throw_up(event.user_id)
            return 'You are not subscribed yet, see "help" for usage'

        if self._sub_list[event.user_id].wait_for_reply:
            self._sub_notes[event.user_id][
                self._sub_list[event.user_id].idx_hour - 1
            ] += "\n" + event.text
            self._sub_list[event.user_id].wait_for_reply = False
            ret: str = f"Note taken for hour {self._sub_list[event.user_id].idx_hour}"
        else:
            words: list[str] = event.text.split()
            command: str = words[0]
            paras: List[str] = words[1:]
            self.throw_up(event.user_id)
            ret = (
                f'unknown command: {command}\nTry "help" for current available services'
            )
            ret += " " + "".join(paras)

        return ret

    def note(self, event: chat_event.PostEvent) -> str:
        """Append note on current time

        Args:
            event (chat_event.PostEvent): request event for this event

        Returns:
            str: request result
        """
        is_sub: bool = True if event.user_id in self._sub_id else False
        if not is_sub:
            return 'You are not subscribed yet, see "help" for usage'

        note: str = event.text.split("note")[1]
        ap_note: str = str(event.timestamp) + note
        self._sub_notes[event.user_id][self._sub_list[event.user_id].idx_hour] = (
            ap_note
            if not self._sub_notes[event.user_id][
                self._sub_list[event.user_id].idx_hour
            ]
            else (
                self._sub_notes[event.user_id][self._sub_list[event.user_id].idx_hour]
                + ap_note
            )
        )
        return f"On time:{self._sub_list[event.user_id].idx_hour + 1} log note:{note}"

    def amend(self, event: chat_event.PostEvent) -> str:
        is_sub: bool = True if event.user_id in self._sub_id else False
        if not is_sub:
            return 'You are not subscribed yet, see "help" for usage'

        # parse to get hour idx, log
        logging.debug(f"user:{event.username} request for amend")
        words_space: List[str] = event.text.split(" ")
        hour = int(words_space[1])
        log: str = " ".join(words_space[2:])
        # parse fail
        if (not isinstance(hour, int)) or 0 > hour or hour > 10:
            logging.warning(f"Amend command fail, with event:{event}")
            return f"Amend command fail, with hour:{hour} and log:{log}"
        else:
            # amend txt on command [idx-1]
            self._sub_notes[event.user_id][hour - 1] = log
            logging.info(f"user:{event.username} amended hour:{hour-1} log.")
            return f'Amend hour:{hour} log. use "log" to see the latest version'

    def _set_on_time(self, event: chat_event.PostEvent) -> str:
        words_space: List[str] = event.text.split(" ")
        set_datetime = datetime.datetime(
            int(words_space[1]),
            int(words_space[2]),
            int(words_space[3]),
            int(words_space[4]),
            int(words_space[5]),
        )

        self._sub_list[event.user_id].on_time = set_datetime
        return (
            f"Set user:{event.username} on time:{self._sub_list[event.user_id].on_time}"
        )

    def onboard(self, event: chat_event.PostEvent) -> str:
        logging.debug(f"user:{event.username} request to set on board time")
        is_sub: bool = True if event.user_id in self._sub_id else False
        now: datetime.datetime = datetime.datetime.now()
        if not is_sub:
            logging.debug(f"user:{event.username} is not sub")
            return 'You are not subscribed yet, see "help" for usage'

        self._sub_list[event.user_id].on_time = now
        self._sub_list[event.user_id].idx_hour = 0
        logging.info(f"user:{event.username} set on board time:{now}")
        return f"set on board time: {now.hour}:{now.minute}"

    def show_log(self, event: chat_event.PostEvent) -> None:
        is_sub: bool = True if event.user_id in self._sub_id else False
        if is_sub:
            word_count = 0
            for i in range(10):
                word_count += len(self._sub_notes[event.user_id][i])

            if word_count > 1500:
                study_bot.web_post.send_message(
                    response_text=(
                        "This is your latest report: \n"
                        f"You already on board for {self._sub_list[event.user_id].idx_hour} hours\n"
                        f"Your on time is set at {self._sub_list[event.user_id].on_time}\n"
                    ),
                    user_id=event.user_id,
                )
                for i in range(10):
                    study_bot.web_post.send_message(
                        response_text=f"Hour {i+1}.\n    "
                        + self._sub_notes[event.user_id][i]
                        + "\n",
                        user_id=event.user_id,
                    )

            else:
                report: str = ""
                for i in range(10):
                    report += (
                        f"Hour {i+1}.\n    " + self._sub_notes[event.user_id][i] + "\n"
                    )
                study_bot.web_post.send_message(
                    response_text=(
                        "This is your latest report: \n"
                        f"You already on board for {self._sub_list[event.user_id].idx_hour} hours\n"
                        f"Your on time is set at {self._sub_list[event.user_id].on_time}\n"
                        + report
                    ),
                    user_id=event.user_id,
                )
        else:
            study_bot.web_post.send_message(
                response_text='You are not subscribed yet, see "help" for usage',
                user_id=event.user_id,
            )
            logging.debug(f"user:{event.username} is not sub")


# server instance


app_autopal = AutoPal(__name__)


# anGnomeing

scheduler = BackgroundScheduler()
scheduler.add_job(
    name="DailyGnome",
    func=app_autopal.angnome,
    # trigger=CronTrigger(day_of_week="mon-fri", second=1),
    trigger=CronTrigger(second=1),
)

scheduler.add_job(
    name="ResetDailyGnome",
    func=app_autopal.clean_gnome,
    trigger=CronTrigger(day_of_week="mon-fri", hour=7, minute=30),
)


# routes


@app_autopal.route("/webhook", methods=["POST"])
def webhook() -> Dict[str, str]:
    # Parse URL-encoded form data
    form_data: ImmutableMultiDict[str, str] = request.form
    logging.debug(f"raw_request:{pprint.pformat(form_data)}")
    event = chat_event.BotEvent(
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

    ret: str = app_autopal.parse_service(event)

    return {"text": ret}


@app_autopal.route("/download/gtu.gif")
def download_gnome_throwup() -> Response:
    path = "/home/yaolin/Workspaces/python-synology-chatbot/synochat/assets/gtu_s.gif"
    return send_file(path, as_attachment=False)


if __name__ == "__main__":
    app_autopal.run(host="192.168.1.103", port=5009)
