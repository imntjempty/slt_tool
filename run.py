# -*- coding: utf-8 -*-
"""
SLT 多机台上位机 —— 程序入口。
运行: python run.py
"""
import os
import sys
import traceback

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QMessageBox

from app.ui.main_window import MainWindow
from app import config as _cfg


def excepthook(typ, val, tb):
    err = "".join(traceback.format_exception(typ, val, tb))
    print(err, file=sys.stderr)
    try:
        QMessageBox.critical(None, "Error", err[-2000:])
    except Exception:
        pass


def _compute_scale(app):
    """按主屏逻辑宽度计算界面缩放因子，适配高分屏/大分辨率。"""
    try:
        w = app.primaryScreen().logicalSize().width()
    except Exception:
        w = 1400
    base = 1400.0  # 基准设计宽度
    sc = w / base
    sc = min(max(sc, 0.9), 2.5)
    return round(sc, 2)


def main():
    sys.excepthook = excepthook
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    sc = _compute_scale(app)
    _cfg.set_ui_scale(sc)

    # 全局字体按缩放因子放大（高分屏下保证可读）
    f = app.font()
    base_pt = f.pointSizeF() if f.pointSizeF() > 0 else 10.0
    f.setPointSizeF(base_pt * sc)
    f.setFamily("Microsoft YaHei" if sys.platform.startswith("win") else f.family())
    app.setFont(f)

    # 全局 QSS：字号与控件尺寸随 UI_SCALE 缩放
    fs = 13 * sc
    app.setStyleSheet(
        f"QWidget{{font-size:{fs:.0f}px;}}"
        f"QComboBox{{font-size:{fs:.0f}px; padding:{3*sc:.0f}px; min-height:{20*sc:.0f}px;}}"
        f"QComboBox QAbstractItemView{{font-size:{fs:.0f}px; selection-background-color:#3498db;}}"
        f"QComboBox QAbstractItemView::item{{min-height:{24*sc:.0f}px; padding:{4*sc:.0f}px;}}"
        f"QSpinBox{{font-size:{fs:.0f}px;}} QLineEdit{{font-size:{fs:.0f}px;}}"
        f"QMenu{{font-size:{fs:.0f}px;}}"
        f"QPushButton{{font-size:{fs:.0f}px;}} QLabel{{font-size:{fs:.0f}px;}}"
        f"QTableWidget{{font-size:{fs:.0f}px;}} QTreeWidget{{font-size:{fs:.0f}px;}}"
    )
    win = MainWindow()
    # 默认最大化，配合字号缩放与布局拉伸，适配不同分辨率
    win.showMaximized()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
