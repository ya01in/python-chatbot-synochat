import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import Flask, jsonify, request
from werkzeug.datastructures.structures import ImmutableMultiDict

from synochat.model import syno
from synochat.api.daily import RequestHandler, RequestParser
from synochat.service import study_bot, study_service

app = Flask(__name__)

scheduler = BackgroundScheduler()


HELP_NOTE = """
~~ APE TOGETHER STRONG ~~
help: show all commands
r <NAME>: throw rock at <NAME>
lc: get daily, send today's challenge via bot
n <strings>: take note with bot, this will send message content to you directly
"""


def daily_leetcode() -> None:
    # Code to be executed by the cron job
    challenge_info = RequestHandler.get_challenge_info()
    challenge = RequestParser.parse(challenge_info)
    study_service.web_post.send_message(
        response_text=f"""
Today's supplement: {challenge.title}
Difficulty: {challenge.difficulty}
ID: {challenge.question_id}
success rate: {challenge.ac_rate}
Go for a shot!!!
"""
    )


# Schedule the cron job to run every day at 9:30 AM
scheduler.add_job(
    func=daily_leetcode,
    trigger=CronTrigger(hour=9, minute=30),
)


def leetcode(user_id):
    challenge_info = RequestHandler.get_challenge_info()
    challenge = RequestParser.parse(challenge_info)
    study_bot.web_post.send_message(
        user_id=user_id,
        response_text=f"""
Today's supplement: {challenge.title}
Difficulty: {challenge.difficulty}
ID: {challenge.question_id}
Link: {challenge.problem_link}
Success rate: {challenge.ac_rate}
Go for a shot!!!
""",
    )


def throw_rock(target_name: str) -> None:
    study_service.web_post.send_message(response_text=f"@{target_name} rock!!!!")


def take_note(user_id, messages) -> None:
    study_bot.web_post.send_message(response_text=messages, user_id=user_id)


def parse_service(event: syno.PostEvent) -> str:
    words: list[str] = event.text.split()
    if len(words) == 1:
        logging.warning("only trigger found")
        return 'no command found, Stop playing with my stick ="='
    command = words[1]
    paras = words[2:]
    ret = ""
    match command:
        case "help":
            ret = HELP_NOTE
        case "r":
            throw_rock(paras[0])
            ret = f"{event.username} throw rock!"
        case "lc":
            leetcode(event.user_id)
            ret = f"{event.username} challenge sent, check your inbox"
        case "n":
            messages = " ".join(paras)
            try:
                take_note(event.user_id, messages)
            except:
                ret = "Failed to take note"
            ret = "Message note taken"
        case _:
            ret = f"unknown command: {command}"
            ret += " " + "".join(paras)
    logging.debug(f"parsed result:{ret}")
    return ret


@app.route("/webhook", methods=["POST"])
def webhook():
    # Parse URL-encoded form data
    form_data: ImmutableMultiDict[str, str] = request.form

    event = syno.PostEvent(**form_data)
    if not event:
        logging.error(f"empty event catched, may have a error? event:{event}")
    logging.debug(f"raw event:{event}")

    ret = parse_service(event)

    post_return = form_data.copy()

    return {"text": ret}


@app.route("/webhook_autopal", methods=["POST"])
def webhook_autopal():
    # Parse URL-encoded form data
    form_data: ImmutableMultiDict[str, str] = request.form

    event = syno.PostEvent(**form_data)
    if not event:
        logging.error(f"empty event catched, may have a error? event:{event}")
    logging.debug(f"raw event:{event}")

    ret = parse_service(event)

    post_return = form_data.copy()

    return {"text": ret}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5008)
