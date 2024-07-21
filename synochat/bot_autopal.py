import logging

from service_conf import BOT_CONF_AUTOPAL
from service import autopal

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    autopal.scheduler.start()
    autopal.app_autopal.run(host=BOT_CONF_AUTOPAL["ip"], port=BOT_CONF_AUTOPAL["port"])
