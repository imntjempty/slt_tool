# -*- coding: utf-8 -*-
"""
日志管理器：写入运行目录 ./logs/，测试结束后设为只读保护（444）。
"""
import os
import stat
from datetime import datetime

from . import config


class LogManager:
    def __init__(self):
        self.log_dir = config.get_log_dir()
        os.makedirs(self.log_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.path = os.path.join(self.log_dir, f"slt_multi_{ts}.log")
        self._fh = open(self.path, "a", encoding="utf-8")

    def write(self, msg):
        try:
            self._fh.write(msg + "\n")
            self._fh.flush()
        except Exception:
            pass

    def close(self):
        """关闭并设为只读，防止误删误改。"""
        try:
            self._fh.close()
        except Exception:
            pass
        try:
            os.chmod(self.path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        except Exception:
            pass
