# -*- coding: utf-8 -*-
"""
多语言支持：中文 / 英文。
语言选择持久化到 .lang 文件（exe 或项目根目录）。
"""
import os

from . import config

LANG_FILE = os.path.join(config.get_app_dir(), ".lang")


def _load_lang():
    try:
        with open(LANG_FILE, "r") as f:
            return f.read().strip()
    except Exception:
        return "zh"


LANG = _load_lang()


def T(zh, en):
    """按当前语言返回中文或英文文案。"""
    return zh if LANG == "zh" else en


def set_lang(l):
    global LANG
    LANG = l
    try:
        with open(LANG_FILE, "w") as f:
            f.write(l)
    except Exception:
        pass
