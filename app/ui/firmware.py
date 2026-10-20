# -*- coding: utf-8 -*-
"""
固件烧录/升级 Tab：加载 firmware.ui，向选中机台下位机分块烧录固件。
"""
import os
import re

from PyQt5.QtWidgets import QWidget, QFileDialog, QMessageBox
from PyQt5.QtCore import pyqtSignal, QThread, Qt
from PyQt5.QtGui import QColor

from ..i18n import T
from ..comm import CommChannel
from ..config import NUM_STATIONS
from .. import config as _cfg

UI_PATH = os.path.join(_cfg.get_ui_dir(), "firmware.ui")

# 从文件名识别固件版本，如 xxx_v1.2.3.bin / xxx-1.0.bin
_VER_RE = re.compile(r"[vV]?(\d+\.\d+(?:\.\d+)?)")


class FwWorker(QThread):
    log_sig = pyqtSignal(str, str)          # (station, msg)
    prog_sig = pyqtSignal(str, int, int)    # (station, cur, total)
    done_sig = pyqtSignal()

    def __init__(self, entries, fw_type, version, data, parent=None):
        super().__init__(parent)
        self.entries = entries   # [(name, channel), ...]
        self.fw_type = fw_type
        self.version = version
        self.data = data
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        for name, ch in self.entries:
            if self._stop:
                self.log_sig.emit(name, T("已中止", "ABORTED"))
                break
            self.log_sig.emit(name, T("开始烧录...", "flashing..."))
            ok, msg = ch.send_fw(
                self.fw_type, self.data, version=self.version,
                progress_cb=lambda cur, total, n=name: self.prog_sig.emit(n, cur, total),
                stop_check=lambda: self._stop)
            self.log_sig.emit(name, msg)
        self.done_sig.emit()


class FirmwareTab(QWidget):
    def __init__(self, stations, parent=None):
        super().__init__(parent)
        self.stations = stations
        self.worker = None
        self._load_ui()
        self._init_stations()
        self._style()
        self._bind()

    def _load_ui(self):
        from PyQt5 import uic
        uic.loadUi(UI_PATH, self)

    def _init_stations(self):
        """机台列表每项带复选框，勾选即选中，状态一目了然。"""
        from PyQt5.QtWidgets import QListWidgetItem
        self.list_stations.clear()
        for i in range(1, NUM_STATIONS + 1):
            it = QListWidgetItem(f"{T('机台', 'Station')} {i}")
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setCheckState(Qt.Unchecked)
            self.list_stations.addItem(it)

    def _style(self):
        sc = _cfg.UI_SCALE
        self.btn_fw_start.setStyleSheet(
            f"font-weight:bold;background:#e67e22;color:white;padding:{6*sc:.0f}px {18*sc:.0f}px;border-radius:{4*sc:.0f}px;")
        self.btn_fw_stop.setStyleSheet(
            f"font-weight:bold;background:#e74c3c;color:white;padding:{6*sc:.0f}px {18*sc:.0f}px;border-radius:{4*sc:.0f}px;")
        self.txt_fw_log.setReadOnly(True)
        # 复选框模式，不依赖选中高亮
        self.list_stations.setSelectionMode(self.list_stations.NoSelection)

    def _bind(self):
        self.btn_browse.clicked.connect(self._browse)
        self.btn_fw_start.clicked.connect(self._start)
        self.btn_fw_stop.clicked.connect(self._stop)

    def _log(self, station, msg):
        self.txt_fw_log.append(f"[{station}] {msg}")

    def _browse(self):
        # 用 Qt 非原生对话框，避免产线环境原生文件对话框兼容问题
        path, _ = QFileDialog.getOpenFileName(
            self, T("选择固件文件", "Select firmware"),
            "", T("固件文件 (*.bin *.img *.fw);;所有文件 (*)"),
            options=QFileDialog.DontUseNativeDialog)
        if path:
            self.le_fw_path.setText(path)
            ver = self._detect_version(path)
            if ver:
                self.le_fw_ver.setText(ver)

    @staticmethod
    def _detect_version(path):
        m = _VER_RE.search(os.path.basename(path))
        return m.group(1) if m else ""

    def _get_selected(self):
        selected = []
        for i in range(self.list_stations.count()):
            it = self.list_stations.item(i)
            if it.checkState() == Qt.Checked:
                name = it.text().strip()
                if name in self.stations:
                    selected.append(name)
        return selected

    def _start(self):
        names = self._get_selected()
        if not names:
            QMessageBox.warning(self, T("提示", "Info"),
                                T("请勾选目标机台!", "Check target station(s)!"))
            return
        path = self.le_fw_path.text().strip()
        if not path or not os.path.isfile(path):
            QMessageBox.warning(self, T("提示", "Info"),
                                T("请选择有效的固件文件!", "Select a valid firmware file!"))
            return
        try:
            with open(path, "rb") as f:
                data = f.read()
        except Exception as e:
            QMessageBox.critical(self, T("错误", "Error"), str(e))
            return
        if not data:
            QMessageBox.warning(self, T("提示", "Info"), T("固件文件为空!", "Firmware empty!"))
            return

        version = self.le_fw_ver.text().strip() or "-"
        entries = []
        for name in names:
            sp = self.stations[name]
            entries.append((name, sp.p_board.channel))

        fw_type = self.cmb_fw_type.currentText().lower()
        self.worker = FwWorker(entries, fw_type, version, data)
        self.worker.log_sig.connect(self._log)
        self.worker.prog_sig.connect(self._on_prog)
        self.worker.done_sig.connect(self._on_done)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

        self.btn_fw_start.setEnabled(False)
        self.btn_fw_stop.setEnabled(True)
        self.lbl_fw_status.setText(T("烧录中...", "Flashing..."))
        self._log(T("全局", "ALL"),
                  T("固件类型={0} 版本={1} 目标机台={2}",
                    "fw={0} ver={1} targets={2}").format(
                      self.cmb_fw_type.currentText(), version, ",".join(names)))

    def _stop(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()

    def _on_prog(self, station, cur, total):
        self.progress_fw.setMaximum(max(total, 1))
        self.progress_fw.setValue(cur)
        self.lbl_fw_status.setText(f"{station} [{cur}/{total}]")

    def _on_done(self):
        self.btn_fw_start.setEnabled(True)
        self.btn_fw_stop.setEnabled(False)
        self.progress_fw.setValue(0)
        self.lbl_fw_status.setText(T("完成", "Done"))
