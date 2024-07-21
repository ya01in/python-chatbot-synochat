import pprint
import time
from typing import Dict

import requests

from model import lc


class Constant:
    """Class for organizing constants."""

    # website names
    LEETCODE = "LEETCODE"
    LEETCODE_API_ENDPOINT = "https://leetcode.com/graphql"
    DAILY_CODING_CHALLENGE_QUERY = """
    query questionOfToday {
        activeDailyCodingChallengeQuestion {
            date
            userStatus
            link
            question {
                acRate
                difficulty
                freqBar
                frontendQuestionId: questionFrontendId
                isFavor
                paidOnly: isPaidOnly
                status
                title
                titleSlug
                hasVideoSolution
                hasSolution
                topicTags {
                    name
                    id
                    slug
                }
            }
        }
    }
    """

    # http call retries
    HTTP_CALL_RETRIES = 3

    # default sleep duration
    DEFAULT_SLEEP = 3600


class RequestHandler:
    """Provides services for requesting leetcode API."""

    url = Constant.LEETCODE_API_ENDPOINT
    query = Constant.DAILY_CODING_CHALLENGE_QUERY
    max_retries = Constant.HTTP_CALL_RETRIES

    @classmethod
    def get_challenge_info(cls) -> Dict:
        """Get daily challenge info from leetcode API."""
        for iteration in range(cls.max_retries):
            try:
                response = requests.post(cls.url, json={"query": cls.query})
                return (
                    response.json()
                    .get("data")
                    .get("activeDailyCodingChallengeQuestion")
                )
            except Exception:
                time.sleep(((iteration + 1) * 10) * 60)
        raise SystemExit("Could not connect to the leetcode server.")


class RequestParser:
    """Parse responses of leetcode API."""

    @classmethod
    def parse(cls, challenge_info: Dict) -> lc.Challenge:
        """Parse API data ans update challenge model."""
        return cls._parse_challenge_info(challenge_info)

    @classmethod
    def _parse_challenge_info(cls, challenge_info) -> lc.Challenge:
        """Parse and update challenge model."""
        question = challenge_info.get("question")
        challenge = lc.Challenge()
        challenge.title = question.get("title")
        challenge.ac_rate = question.get("acRate")
        challenge.difficulty = question.get("difficulty")
        challenge.question_id = question.get("frontendQuestionId")
        challenge.date = challenge_info.get("date")
        challenge.title_slug = question.get("titleSlug")
        challenge.raw_tags = question.get("topicTags")
        return challenge


if __name__ == "__main__":
    challenge_info = RequestHandler.get_challenge_info()
    challenge = RequestParser.parse(challenge_info)
    pprint.pprint(challenge.title)
    pprint.pprint(challenge.difficulty)
    pprint.pprint(challenge.question_id)
    pprint.pprint(challenge.ac_rate)
