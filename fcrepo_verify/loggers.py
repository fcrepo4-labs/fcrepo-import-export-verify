import logging


class Loggers:
    def __init__(self, console, console_only, file_only):
        self.console = console
        self.console_only = console_only
        self.file_only = file_only


def createLoggers(level, logfilename):
    '''Creates and configures a Loggers object which contains three loggers:
        console - logs to both the console and the log file
        console_only - logs only to the console
        file_only - only logs to the file'''

    # create console logger
    console = logging.getLogger("output")
    console.setLevel(level)

    # create console handler and set level to debug
    console_handler = logging.StreamHandler()
    file_handler = logging.FileHandler(filename=logfilename, mode="w")

    # set level
    # console_handler.setLevel(logging.INFO)
    # file_handler.setLevel(logging.DEBUG)

    # create formatters
    console_formatter = logging.Formatter("%(asctime)s %(levelname)-8s "
                                          "%(message)s")
    file_formatter = logging.Formatter("%(asctime)s %(levelname)-8s "
                                       "%(module)-12s : %(lineno)d =>  "
                                       "%(message)s")

    # add formatter to console_handler
    console_handler.setFormatter(console_formatter)
    file_handler.setFormatter(file_formatter)
    # add console_handler to logger
    console.addHandler(console_handler)
    console.addHandler(file_handler)

    # create console only logger
    console_only = logging.getLogger("console_only")
    console_only.setLevel(logging.DEBUG)
    console_only.addHandler(console_handler)

    # create file only logger
    file_only = logging.getLogger("file_only")
    file_only.setLevel(level)
    file_only.addHandler(file_handler)

    loggers = Loggers(console, console_only, file_only)

    return loggers
