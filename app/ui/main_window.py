# -*- coding: utf-8 -*-
"""
主窗口：加载 main_window.ui，管理总览 + 多机台 Tab + 全局日志 + 语言切换。
"""
import os
from datetime import datetime

from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QTextCursor

from ..config import NUM_STATIONS
from ..i18n import T, LANG, set_lang
from ..logger import LogManager
from .. import config as _cfg

from .dashboard import Dashboard
from .station_panel import StationPanel
from .firmware import FirmwareTab
from .sku import SkuTab

UI_PATH = os.path.join(_cfg.get_ui_dir(), "main_window.ui")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.stations = {}
        self.logger = LogManager()
        self._load_ui()
        self._build_tabs()
        self._style()
        self._log(T("系统启动", "Session started"), "info")

    def _load_ui(self):
        from PyQt5 import uic
        uic.loadUi(UI_PATH, self)
        # 默认语言选中
        self.cmb_lang.setCurrentIndex(0 if LANG == "zh" else 1)
        self.cmb_lang.currentIndexChanged.connect(self._on_lang_changed)
        self.btn_all_start.clicked.connect(self._start_all)
        self.btn_all_pause.clicked.connect(self._pause_all)
        self.btn_all_resume.clicked.connect(self._resume_all)
        self.btn_all_stop.clicked.connect(self._stop_all)
        self.splitter_v.setStretchFactor(0, 3)
        self.splitter_v.setStretchFactor(1, 1)
        self.splitter_v.setSizes([600, 200])

    def _style(self):
        sc = _cfg.UI_SCALE
        self.btn_all_start.setStyleSheet(
            f"font-size:{int(14*sc)}px;font-weight:bold;background:#2ecc71;color:white;padding:{8*sc:.0f}px {30*sc:.0f}px;border-radius:{5*sc:.0f}px;")
        self.btn_all_stop.setStyleSheet(
            f"font-size:{int(14*sc)}px;font-weight:bold;background:#e74c3c;color:white;padding:{8*sc:.0f}px {30*sc:.0f}px;border-radius:{5*sc:.0f}px;")
        self.btn_all_pause.setStyleSheet(
            f"font-size:{int(14*sc)}px;font-weight:bold;background:#f39c12;color:white;padding:{8*sc:.0f}px {26*sc:.0f}px;border-radius:{5*sc:.0f}px;")
        self.btn_all_resume.setStyleSheet(
            f"font-size:{int(14*sc)}px;font-weight:bold;background:#3498db;color:white;padding:{8*sc:.0f}px {26*sc:.0f}px;border-radius:{5*sc:.0f}px;")
        self.cmb_lang.setStyleSheet(f"padding:{4*sc:.0f}px {12*sc:.0f}px;")
        self.txt_log.setReadOnly(True)
        self.txt_log.setFont(QFont("Courier New", max(9, int(9 * sc))))
        # 顶部按钮横向拉伸，避免过窄/留白
        from PyQt5.QtWidgets import QSizePolicy
        for b in (self.btn_all_start, self.btn_all_pause,
                  self.btn_all_resume, self.btn_all_stop):
            b.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        # 语言下拉固定宽度随字号自然增长

    def _build_tabs(self):
        self.dashboard = Dashboard()
        self.tabs.addTab(self.dashboard, T("  总览  ", "  Dashboard  "))
        for i in range(1, NUM_STATIONS + 1):
            name = f"{T('机台', 'Station')} {i}"
            sp = StationPanel(name)
            sp.log_to_global.connect(self._global_log)
            sp.status_changed.connect(self._update_dash)
            # 芯片目标数变化时同步到总览全局统计
            idx = i - 1
            sp.spin_loop.valueChanged.connect(
                lambda v, i0=idx: self.dashboard.set_target(i0, v))
            self.dashboard.set_target(idx, sp.spin_loop.value())
            self.stations[name] = sp
            self.tabs.addTab(sp, f"  {name}  ")
        # 固件烧录 Tab
        self.firmware = FirmwareTab(self.stations)
        self.tabs.addTab(self.firmware, T("  固件升级  ", "  Firmware  "))
        # SKU 统计 Tab
        self.sku_tab = SkuTab()
        self.tabs.addTab(self.sku_tab, T("  SKU 统计  ", "  SKU  "))

    # ---- 总览更新 ----
    def _update_dash(self, name, status):
        idx = int(name.split()[-1]) - 1
        status["connected"] = self.stations[name].p_board.channel.connected
        self.dashboard.update_row(idx, status)
        self.sku_tab.refresh(self.stations)
        self._maybe_finish_notify()

    def _maybe_finish_notify(self):
        """所有机台测试都结束后，弹出汇总提示。"""
        running = any(self.dashboard._states[i].get("running")
                      for i in self.dashboard._states)
        had = getattr(self, "_had_running", False)
        self._had_running = running
        if had and not running:
            self._show_finish_summary()

    def _show_finish_summary(self):
        lines = [T("全部测试完成", "All tests finished")]
        lines.append("-" * 30)
        for name, sp in self.stations.items():
            if sp.last_summary:
                s = sp.last_summary
                lines.append(
                    f"{name}: {T('通过', 'Pass')}={s.get('pass', 0)} "
                    f"{T('失败', 'Fail')}={s.get('fail', 0)} "
                    f"{T('中止', 'Abort')}={s.get('abort', 0)}")
        lines.append("-" * 30)
        d = self.dashboard
        lines.append(f"{T('芯片总数', 'Chips')}={d.val_g_chips.text()} "
                     f"BIN0={d.val_g_bin0.text()} BIN1={d.val_g_bin1.text()} "
                     f"BIN2={d.val_g_bin2.text()} "
                     f"{T('良率', 'Yield')}={d.val_g_yield.text()}")
        QMessageBox.information(self, T("测试完成", "Test Finished"), "\n".join(lines))

    # ---- 全部开始 / 停止 ----
    def _start_all(self):
        connected = [name for name, sp in self.stations.items()
                     if sp.p_board.channel.connected]
        if not connected:
            QMessageBox.warning(
                self, T("提示", "Info"),
                T("所有机台测试板均未连接，无法开始测试!\n请先在各机台页建立连接。",
                  "All stations disconnected, cannot start!\nConnect boards first."))
            return
        for name, sp in self.stations.items():
            if sp.p_board.channel.connected:
                sp.start_test()
            else:
                self._log(f"{name}: {T('测试板未连接，已跳过', 'Board not connected, skipped')}", "warn")

    def _stop_all(self):
        for sp in self.stations.values():
            sp.stop_test()

    def _pause_all(self):
        for sp in self.stations.values():
            sp.pause_test()

    def _resume_all(self):
        for sp in self.stations.values():
            sp.resume_test()

    # ---- 语言切换 ----
    def _on_lang_changed(self, idx):
        new = self.cmb_lang.itemData(idx)
        if new is None:
            new = "en" if idx == 1 else "zh"
        if new == LANG:
            return
        set_lang(new)
        QMessageBox.information(
            self, T("提示", "Info"),
            T("语言已切换，请手动重启程序", "Language changed, please restart manually"))
        from PyQt5.QtWidgets import QApplication
        QApplication.quit()

    # ---- 日志 ----
    def _global_log(self, station, msg, level):
        ts = datetime.now().strftime("%H:%M:%S")
        colors = {"info": "#2c3e50", "ok": "#27ae60", "warn": "#f39c12", "error": "#e74c3c"}
        c = colors.get(level, "#2c3e50")
        self.txt_log.append(
            f'<span style="color:#95a5a6">[{ts}]</span> '
            f'<span style="color:#3498db;font-weight:bold">[{station}]</span> '
            f'<span style="color:{c}">{msg}</span>')
        self.txt_log.moveCursor(QTextCursor.End)
        self.logger.write(f"[{ts}] [{station}] {msg}")

    def _log(self, msg, level="info"):
        self._global_log("SYS", msg, level)

    def closeEvent(self, e):
        self.logger.close()
        e.accept()
