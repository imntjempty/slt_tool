# -*- coding: utf-8 -*-
"""
全局配置与常量。
"""
import os
import sys

# 机台数量（增减该常量即可）
NUM_STATIONS = 6

# 默认 TCP 端口
DEFAULT_TCP_PORT = 5001
# 默认 IP 前缀（机台 i -> 192.168.1.{100+i}）
DEFAULT_IP_BASE = "192.168.1.100"

# Bin 定义
BIN_PASS = "BIN0 - PASS"
BIN_FAIL = "BIN1 - FAIL"
BIN_ABORT = "BIN2 - ABORT"
BINS = [BIN_PASS, BIN_FAIL, BIN_ABORT]

BIN_COLORS = {BIN_PASS: "#27ae60", BIN_FAIL: "#e74c3c", BIN_ABORT: "#f39c12"}

# 界面缩放因子：根据主屏分辨率在 run.py 启动时计算，供字号与控件尺寸缩放
UI_SCALE = 1.0


def set_ui_scale(s):
    global UI_SCALE
    UI_SCALE = s


def get_app_dir():
    """应用目录：PyInstaller 打包后为 exe 目录，否则为项目根目录。"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_ui_dir():
    """.ui 文件所在目录。"""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ui")


def get_log_dir():
    """日志目录（运行程序当前目录下 logs）。"""
    return os.path.join(os.getcwd(), "logs")
