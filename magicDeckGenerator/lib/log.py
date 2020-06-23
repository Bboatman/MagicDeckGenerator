import logging

class Log:
# Initializer / Instance Attributes
    def __init__(self, src, log_level):
        self.src = src
        format = "%(asctime)s: %(message)s"
        
        if (log_level == 0):
            level = logging.INFO
        elif (log_level == 1):
            level = logging.WARN
        elif (log_level == 2):
            level = logging.ERROR
        else:
            level = logging.CRITICAL

        logging.basicConfig(format=format, level=level,
                            datefmt="%H:%M:%S")

    def log(self, level, msg):
        if (level == 0):
            self.info(msg)
        elif (level == 1):
            self.warn(msg)
        elif (level == 2):
            self.error(msg)

    def info(self, msg):
        logging.info("%s : %s", self.src, msg)

    def warn(self, msg):
        logging.warn("%s : %s", self.src, msg)

    
    def error(self, msg):
        logging.error("%s : %s", self.src, msg)