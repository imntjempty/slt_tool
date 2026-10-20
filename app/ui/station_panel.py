# -*- coding: utf-8 -*-
"""
机台面板：加载 station_panel.ui，管理单台机台的连接、测试执行与结果展示。
"""
import os

from PyQt5.QtWidgets import QWidget, QMessageBox, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont

from ..comm import CommChannel
from ..config import BINS, BIN_PASS, BIN_FAIL, BIN_ABORT, BIN_COLORS
from ..i18n import T
from ..test_cases import TEST_CASES, GROUP_IDS, DESC_MAP
from ..worker import TestWorker
from .. import config as _cfg

_QSizePolicy = QSizePolicy

from .conn_panel import ConnPanel

UI_PATH = os.path.join(_cfg.get_ui_dir(), "station_panel.ui")


class StationPanel(QWidget):
    log_to_global = pyqtSignal(str, str, str)   # (station, msg, level)
    status_changed = pyqtSignal(str, dict)      # (station_name, status_dict)

    def __init__(self, station_name, parent=None):
        super().__init__(parent)
        self.station_name = station_name
        self.worker = None
        self.case_item_map = {}
        self.bin_counts = {BIN_PASS: 0, BIN_FAIL: 0, BIN_ABORT: 0}
        self.chip_bin = {"total": 0, "bin0": 0, "bin1": 0, "bin2": 0}
        self._loop_has_fail = False
        self._loop_has_abort = False
        self._current_loop = 0
        self.last_summary = None
        self._load_ui()
        self._setup_conns()
        self._build_tree()
        self._setup_table()
        self._style()
        self._bind()

    # ---- 加载 .ui 并填充连接面板 ----
    def _load_ui(self):
        from PyQt5 import uic
        uic.loadUi(UI_PATH, self)

    def _setup_conns(self):
        self.p_handler = ConnPanel(T("Handler 控制箱", "Handler"))
        self.p_board = ConnPanel(T("Board 测试板", "Board"))
        self.p_board.disconnect_requested.connect(self._on_board_disconnect)
        self.slot_handler_layout.addWidget(self.p_handler)
        self.slot_board_layout.addWidget(self.p_board)
        # 占位 groupbox 去掉边框感，让内嵌 ConnPanel 显示
        self.slot_handler.setTitle("")
        self.slot_board.setTitle("")

    # ---- 测试用例树 ----
    def _build_tree(self):
        self.tree_cases.setHeaderLabels([T("测试项", "Case"), T("状态", "Status")])
        self.tree_cases.setColumnWidth(0, 220)
        self.tree_cases.setColumnWidth(1, 70)
        self.tree_cases.header().setSectionResizeMode(0, self.tree_cases.header().ResizeToContents)
        self.tree_cases.setStyleSheet(
            f"QTreeWidget{{font-size:{int(12*_cfg.UI_SCALE)}px;}}"
            f"QTreeWidget::item{{height:{int(22*_cfg.UI_SCALE)}px;}}")
        current_parent = None
        for cid, desc, is_group in TEST_CASES:
            if is_group:
                p = self._new_tree_item(None, [desc, "--"], bold=True)
                self.case_item_map[cid] = p
                current_parent = p
            else:
                if current_parent is not None:
                    c = self._new_tree_item(current_parent, [desc, "--"])
                else:
                    c = self._new_tree_item(None, [desc, "--"])
                self.case_item_map[cid] = c
        self.tree_cases.collapseAll()

    def _new_tree_item(self, parent, texts, bold=False):
        from PyQt5.QtWidgets import QTreeWidgetItem
        if parent is not None:
            item = QTreeWidgetItem(parent, texts)
        else:
            item = QTreeWidgetItem(texts)
            self.tree_cases.addTopLevelItem(item)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
        item.setCheckState(0, Qt.Checked)
        if bold:
            f = item.font(0)
            f.setBold(True)
            item.setFont(0, f)
        return item

    # ---- 结果表 & BIN ----
    def _setup_table(self):
        self.tbl_results.setHorizontalHeaderLabels(
            [T("芯片", "Chip"), T("测试项", "Case"), T("描述", "Description"),
             T("结果", "Result"), T("错误码", "Error")])
        self.tbl_results.horizontalHeader().setSectionResizeMode(
            0, self.tbl_results.horizontalHeader().ResizeToContents)
        self.tbl_results.horizontalHeader().setSectionResizeMode(
            self.tbl_results.horizontalHeader().Stretch)
        # BIN 标签样式
        self.bin_labels = {
            BIN_PASS: self.bin_lbl_pass,
            BIN_FAIL: self.bin_lbl_fail,
            BIN_ABORT: self.bin_lbl_abort,
        }
        for b, lbl in self.bin_labels.items():
            lbl.setFont(QFont("Arial", int(20 * _cfg.UI_SCALE), QFont.Bold))
            lbl.setStyleSheet(f"color:{BIN_COLORS[b]};")

    def _style(self):
        sc = _cfg.UI_SCALE
        self.btn_start.setStyleSheet(
            f"font-weight:bold;background:#2ecc71;color:white;padding:{6*sc:.0f}px {20*sc:.0f}px;border-radius:{4*sc:.0f}px;")
        self.btn_pause.setStyleSheet(
            f"font-weight:bold;background:#f39c12;color:white;padding:{6*sc:.0f}px {16*sc:.0f}px;border-radius:{4*sc:.0f}px;")
        self.btn_resume.setStyleSheet(
            f"font-weight:bold;background:#3498db;color:white;padding:{6*sc:.0f}px {16*sc:.0f}px;border-radius:{4*sc:.0f}px;")
        self.btn_stop.setStyleSheet(
            f"font-weight:bold;background:#e74c3c;color:white;padding:{6*sc:.0f}px {20*sc:.0f}px;border-radius:{4*sc:.0f}px;")
        # 顶部控制按钮横向拉伸，避免过窄
        for b in (self.btn_start, self.btn_pause, self.btn_resume, self.btn_stop):
            b.setSizePolicy(_QSizePolicy.Expanding, _QSizePolicy.Fixed)
        self.lbl_cur.setStyleSheet("font-weight:bold;")
        # 左右用 stretch 而非固定像素，随窗口自适应：测试项:结果表 = 1:2
        self.midSplitter.setStretchFactor(0, 1)
        self.midSplitter.setStretchFactor(1, 2)

    def _bind(self):
        self.btn_select_all.clicked.connect(lambda: self._set_all(True))
        self.btn_clear_all.clicked.connect(lambda: self._set_all(False))
        self.btn_start.clicked.connect(self.start_test)
        self.btn_pause.clicked.connect(self.pause_test)
        self.btn_resume.clicked.connect(self.resume_test)
        self.btn_stop.clicked.connect(self.stop_test)

    # ---- 勾选工具 ----
    def _set_all(self, v):
        for it in self.case_item_map.values():
            it.setCheckState(0, Qt.Checked if v else Qt.Unchecked)

    def _get_selected(self):
        cmap = {c[0]: c for c in TEST_CASES}
        return [cmap[cid] for cid, it in self.case_item_map.items()
                if cid not in GROUP_IDS and it.checkState(0) == Qt.Checked]

    def _set_status(self, cid, txt, color):
        it = self.case_item_map.get(cid)
        if not it:
            return
        it.setText(1, txt)
        it.setForeground(1, QColor(color) if color else QColor("#2c3e50"))

    # ---- 测试控制 ----
    def start_test(self):
        if not self.p_board.channel.connected:
            QMessageBox.warning(
                self, T("未连接", "Not Connected"),
                f"{self.station_name}: {T('请先连接测试板!', 'connect Board first!')}")
            return
        sel = self._get_selected()
        if not sel:
            QMessageBox.warning(
                self, T("无测试项", "No Cases"),
                T("请至少勾选一个测试用例!", "Select at least one case!"))
            return

        try:
            if self.worker and self.worker.isRunning():
                self.worker.stop()
                self.worker.wait(3000)
        except RuntimeError:
            self.worker = None

        self.tbl_results.setRowCount(0)
        self.bin_counts = {BIN_PASS: 0, BIN_FAIL: 0, BIN_ABORT: 0}
        self.chip_bin = {"total": 0, "bin0": 0, "bin1": 0, "bin2": 0}
        self._loop_has_fail = False
        self._loop_has_abort = False
        for lbl in self.bin_labels.values():
            lbl.setText("0")
        self.progress_bar.setValue(0)
        for cid in self.case_item_map:
            self._set_status(cid, "--", None)

        sim = (self.p_board.channel.mode == CommChannel.MODE_SIM)
        loops = self.spin_loop.value()
        self.worker = TestWorker(sel, self.p_board.channel, sim_mode=sim, loops=loops)
        self.worker.log_signal.connect(
            lambda m, lv: self.log_to_global.emit(self.station_name, m, lv))
        self.worker.progress_signal.connect(self._on_prog)
        self.worker.case_start_signal.connect(
            lambda c: self._set_status(c, T("运行", "RUN"), "#f39c12"))
        self.worker.case_result_signal.connect(self._on_result)
        self.worker.finished_signal.connect(self._on_done)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_pause.setEnabled(True)
        self.btn_resume.setEnabled(False)
        self.lbl_cur.setText(T("测试中...", "Running..."))
        # 测试进行中锁定可改控件，防止误操作
        self._set_testing_ui(True)

    def pause_test(self):
        try:
            if self.worker and self.worker.isRunning():
                self.worker.pause()
                self.btn_pause.setEnabled(False)
                self.btn_resume.setEnabled(True)
                self.lbl_cur.setText(T("已暂停", "Paused"))
                self.log_to_global.emit(self.station_name, T("已暂停", "PAUSED"), "warn")
        except RuntimeError:
            self.worker = None

    def resume_test(self):
        try:
            if self.worker and self.worker.isRunning():
                self.worker.resume()
                self.btn_pause.setEnabled(True)
                self.btn_resume.setEnabled(False)
                self.lbl_cur.setText(T("测试中...", "Running..."))
                self.log_to_global.emit(self.station_name, T("继续测试", "RESUMED"), "info")
        except RuntimeError:
            self.worker = None

    def _on_board_disconnect(self):
        try:
            if self.worker and self.worker.isRunning():
                self.worker.stop()
                self.worker.wait(3000)
        except RuntimeError:
            self.worker = None

    def stop_test(self):
        try:
            if self.worker and self.worker.isRunning():
                self.worker.stop()
                self.p_board.channel.stop_test_tcp()
                self.log_to_global.emit(
                    self.station_name, T("已请求停止...", "Stop requested..."), "warn")
        except RuntimeError:
            self.worker = None

    # ---- 信号处理 ----
    def _on_prog(self, cur, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(cur)
        self.lbl_cur.setText(f"[{cur}/{total}]")

    def _on_result(self, cid, ok, err, loop=1):
        desc = DESC_MAP.get(cid, cid)
        if err == "ABORTED":
            self._set_status(cid, T("中止", "ABORT"), "#f39c12")
        elif ok:
            self._set_status(cid, T("通过", "PASS"), "#27ae60")
        else:
            self._set_status(cid, T("失败", "FAIL"), "#e74c3c")

        # 芯片级 BIN 判定
        if loop != self._current_loop:
            if self._current_loop > 0:
                self._close_chip_bin()
            self._current_loop = loop
            self._loop_has_fail = False
            self._loop_has_abort = False
        if not ok:
            if err == "ABORTED":
                self._loop_has_abort = True
            else:
                self._loop_has_fail = True

        r = self.tbl_results.rowCount()
        self.tbl_results.insertRow(r)
        self.tbl_results.setItem(r, 0, self._item(f"Chip{loop}"))
        self.tbl_results.setItem(r, 1, self._item(cid))
        self.tbl_results.setItem(r, 2, self._item(desc))
        ri = self._item("PASS" if ok else "FAIL")
        ri.setForeground(QColor("#27ae60") if ok else QColor("#e74c3c"))
        self.tbl_results.setItem(r, 3, ri)
        self.tbl_results.setItem(r, 4, self._item(err))

        if ok:
            self.bin_counts[BIN_PASS] += 1
        elif err == "ABORTED":
            self.bin_counts[BIN_ABORT] += 1
        else:
            self.bin_counts[BIN_FAIL] += 1
        for b, lbl in self.bin_labels.items():
            lbl.setText(str(self.bin_counts[b]))

        self._emit_status(cid, running=True)

    @staticmethod
    def _item(text):
        from PyQt5.QtWidgets import QTableWidgetItem
        return QTableWidgetItem(text)

    def _close_chip_bin(self):
        self.chip_bin["total"] += 1
        if self._loop_has_abort:
            self.chip_bin["bin2"] += 1
        elif self._loop_has_fail:
            self.chip_bin["bin1"] += 1
        else:
            self.chip_bin["bin0"] += 1

    def _emit_status(self, current, running):
        self.status_changed.emit(self.station_name, {
            "pass": self.bin_counts[BIN_PASS],
            "fail": self.bin_counts[BIN_FAIL],
            "abort": self.bin_counts[BIN_ABORT],
            "current": current,
            "running": running,
            "chip_total": self.chip_bin["total"],
            "chip_bin0": self.chip_bin["bin0"],
            "chip_bin1": self.chip_bin["bin1"],
            "chip_bin2": self.chip_bin["bin2"],
        })

    def _set_testing_ui(self, testing):
        """测试中锁定：测试项勾选、芯片目标数、全选/清空、连接面板。"""
        self.spin_loop.setEnabled(not testing)
        self.btn_select_all.setEnabled(not testing)
        self.btn_clear_all.setEnabled(not testing)
        # 树：保留显示，禁用勾选交互
        if testing:
            for it in self.case_item_map.values():
                it.setFlags(it.flags() & ~Qt.ItemIsUserCheckable)
        else:
            for it in self.case_item_map.values():
                it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
        self.p_handler.set_test_lock(testing)
        self.p_board.set_test_lock(testing)

    def _on_done(self, summary):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_pause.setEnabled(False)
        self.btn_resume.setEnabled(False)
        self.lbl_cur.setText(T("完成", "Done"))
        self.last_summary = dict(summary)
        # 测试结束恢复可改控件
        self._set_testing_ui(False)
        if self._current_loop > 0:
            self._close_chip_bin()
            self._current_loop = 0
        self._emit_status("--", running=False)
