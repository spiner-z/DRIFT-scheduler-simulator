from datetime import datetime

class Logger:
    def __init__(self, debug_mode: bool = True):
        self.debug_mode = debug_mode

    def _log(self, level: str, msg: str):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{now}] [{level}] {msg}")

    def debug(self, msg: str):
        if self.debug_mode:
            self._log("DEBUG", msg)

    def info(self, msg: str):
        self._log("INFO", msg)

    def warning(self, msg: str):
        self._log("WARNING", msg)

    def error(self, msg: str):
        self._log("ERROR", msg)

debug_mode = False
logger = Logger(debug_mode)