import logging

class Log:
# Initializer / Instance Attributes
    def __init__(self, src, log_level):
        self.src = src
        format = "%(asctime)s: %(message)s"
        level = logging.INFO
        if (log_level > 0):
            level = logging.WARN
        if (log_level > 1):
            level = logging.ERROR

        logging.basicConfig(format=format, level=level,
                            datefmt="%H:%M:%S")

    def log(self, level, msg):
        if (level == 0):
            self.info(msg)
        if (level == 1):
            self.warn(msg)
        if (level == 2):
            self.error(msg)

    def info(self, msg):
        logging.info("%s : %s", self.src, msg)

    def warn(self, msg):
        log.warn("%s : %s", self.src, msg)

    
    def error(self, msg):
        log.error("%s : %s", self.src, msg)