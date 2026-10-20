# -*- coding: utf-8 -*-
"""
总览面板：加载 dashboard.ui，展示所有机台状态、芯片 BIN 统计与全局 BIN 汇总。
"""
import os

from PyQt5.QtWidgets import QWidget, QTableWidgetItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

from ..config import NUM_STATIONS
from ..i18n import T
from .. import config as _cfg

UI_PATH = os.path.join(_cfg.get_ui_dir(), "dashboard.ui")


class Dashboard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._states = {}  # idx -> 最新状态字典
        self._load_ui()
        self._init_rows()
        self._init_global()

    def _load_ui(self):
        from PyQt5 import uic
        uic.loadUi(UI_PATH, self)

    def _init_rows(self):
        self.tbl_dash.setHorizontalHeaderLabels([
            T("机台", "Station"), T("连接", "Conn"), T("当前测试项", "Current"),
            T("芯片总数", "Chips"), T("BIN0 良品", "BIN0 Good"),
            T("BIN1 不良", "BIN1 Bad"), T("BIN2 中止", "BIN2 Abort"),
            T("状态", "Status"),
        ])
        h = self.tbl_dash.horizontalHeader()
        h.setSectionResizeMode(h.Stretch)
        # 表格行均匀撑满整个区域，比例更饱满
        self.tbl_dash.verticalHeader().setVisible(False)
        self.tbl_dash.verticalHeader().setSectionResizeMode(self.tbl_dash.verticalHeader().Stretch)
        self.tbl_dash.setSelectionMode(self.tbl_dash.NoSelection)
        self.tbl_dash.setRowCount(0)
        for i in range(NUM_STATIONS):
            r = self.tbl_dash.rowCount()
            self.tbl_dash.insertRow(r)
            self.tbl_dash.setItem(r, 0, QTableWidgetItem(f"{T('机台', 'Station')} {i+1}"))
            self.tbl_dash.setItem(r, 1, QTableWidgetItem("--"))
            self.tbl_dash.setItem(r, 2, QTableWidgetItem("--"))
            for c in (3, 4, 5, 6):
                self.tbl_dash.setItem(r, c, QTableWidgetItem("0"))
            st = QTableWidgetItem(T("空闲", "IDLE"))
            st.setForeground(QColor("#95a5a6"))
            self.tbl_dash.setItem(r, 7, st)
            self._states[i] = {"target": 0, "chip_total": 0, "chip_bin0": 0,
                               "chip_bin1": 0, "chip_bin2": 0, "fail": 0,
                               "running": False, "connected": False, "current": "--"}

    def _init_global(self):
        sc = _cfg.UI_SCALE
        self.g_labels = {
            "target": self.val_g_target,
            "done": self.val_g_done,
            "remain": self.val_g_remain,
            "chips": self.val_g_chips,
            "bin0": self.val_g_bin0,
            "bin1": self.val_g_bin1,
            "bin2": self.val_g_bin2,
            "yield": self.val_g_yield,
        }
        colors = {"target": "#2980b9", "done": "#27ae60", "remain": "#f39c12",
                  "chips": "#2c3e50", "bin0": "#27ae60", "bin1": "#e74c3c",
                  "bin2": "#f39c12", "yield": "#2980b9"}
        for k, lbl in self.g_labels.items():
            lbl.setFont(QFont("Arial", int(20 * sc), QFont.Bold))
            lbl.setStyleSheet(f"color:{colors[k]};")
        self._update_global()

    def set_target(self, idx, target):
        """更新某机台的目标芯片数（来自机台 spin_loop）。"""
        self._states[idx]["target"] = max(0, int(target))
        self._update_global()

    def update_row(self, idx, status):
        """idx: 机台索引(0-based)。status: 机台上报的状态字典。"""
        self._states[idx].update(status)
        s = self._states[idx]
        conn = T("已连接", "ON") if s.get("connected") else T("未连接", "OFF")
        self.tbl_dash.item(idx, 1).setText(conn)
        self.tbl_dash.item(idx, 2).setText(s.get("current", "--"))
        self.tbl_dash.item(idx, 3).setText(str(s.get("chip_total", 0)))
        self.tbl_dash.item(idx, 4).setText(str(s.get("chip_bin0", 0)))
        self.tbl_dash.item(idx, 5).setText(str(s.get("chip_bin1", 0)))
        self.tbl_dash.item(idx, 6).setText(str(s.get("chip_bin2", 0)))
        st = self.tbl_dash.item(idx, 7)
        if s.get("running"):
            st.setText(T("测试中", "RUNNING"))
            st.setForeground(QColor("#f39c12"))
        elif s.get("chip_bin1", 0) > 0 or s.get("fail", 0) > 0:
            st.setText(T("失败", "FAIL"))
            st.setForeground(QColor("#e74c3c"))
        elif s.get("chip_total", 0) > 0:
            st.setText(T("完成", "DONE"))
            st.setForeground(QColor("#27ae60"))
        else:
            st.setText(T("空闲", "IDLE"))
            st.setForeground(QColor("#95a5a6"))
        self._update_global()

    # ---- 全局 BIN 汇总 ----
    def _update_global(self):
        # 目标芯片只统计已开始测试的机台（正在测试或已有完成芯片）
        started = [s for s in self._states.values()
                   if s.get("running") or s.get("chip_total", 0) > 0]
        target = sum(s.get("target", 0) for s in started)
        done = sum(s.get("chip_total", 0) for s in self._states.values())
        remain = max(0, target - done)
        total = done
        bin0 = sum(s.get("chip_bin0", 0) for s in self._states.values())
        bin1 = sum(s.get("chip_bin1", 0) for s in self._states.values())
        bin2 = sum(s.get("chip_bin2", 0) for s in self._states.values())
        self.g_labels["target"].setText(str(target))
        self.g_labels["done"].setText(str(done))
        self.g_labels["remain"].setText(str(remain))
        self.g_labels["chips"].setText(str(total))
        self.g_labels["bin0"].setText(str(bin0))
        self.g_labels["bin1"].setText(str(bin1))
        self.g_labels["bin2"].setText(str(bin2))
        if total > 0:
            self.g_labels["yield"].setText(f"{bin0 / total * 100:.1f}%")
        else:
            self.g_labels["yield"].setText("--")
