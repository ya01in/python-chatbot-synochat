import logging

from synochat.service_conf import STUDY_CONF
from synochat.service import study

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    study.scheduler.start()
    study.app.run(host=STUDY_CONF["ip"], port=STUDY_CONF["port"])
