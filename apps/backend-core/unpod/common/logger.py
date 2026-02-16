from django.utils import timezone
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def print_log(*args):
    print(f"[{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}]", *args)


class UnpodLogger:
    def __init__(self, name):
        self.logging = logging.getLogger(name)

    def error(self, message):
        self.logging.error(message)

    def info(self, message):
        self.logging.info(message)

    def debug(self, message):
        self.logging.debug(message)

    def warning(self, message):
        self.logging.warning(message)
