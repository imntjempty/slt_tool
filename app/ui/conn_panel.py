# -*- coding: utf-8 -*-
"""
连接面板：加载 conn_panel.ui，管理三种模式的连接/断开。
"""
import os

from PyQt5.QtWidgets import QGroupBox, QMessageBox, QSizePolicy
from PyQt5.QtCore import pyqtSignal

from ..comm import CommChannel
from ..i18n import T
from .. import config

_QSizePolicy = QSizePolicy

UI_PATH = os.path.join(config.get_ui_dir(), "conn_panel.ui")


class ConnPanel(QGroupBox):
    conn_changed = pyqtSignal(bool)
    disconnect_requested = pyqtSignal()

    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self._panel_title = title
        self.channel = CommChannel(title)
        self._load_ui()
        self._init_style()
        self._bind()
        self._on_mode(0)
        self._refresh_ports()

    def _load_ui(self):
        from PyQt5 import uic
        uic.loadUi(UI_PATH, self)
        self.setTitle(self._panel_title)

    # ---- 初始样式 ----
    def _init_style(self):
        sc = config.UI_SCALE
        self.btn_connect.setStyleSheet(
            f"font-weight:bold;background:#2ecc71;color:white;padding:{4*sc:.0f}px {12*sc:.0f}px;border-radius:{3*sc:.0f}px;")
        self.lbl_status.setStyleSheet("color:#e74c3c;font-weight:bold;")
        self.cmb_baud.setCurrentText("115200")
        self.spin_tcp_port.setValue(config.DEFAULT_TCP_PORT)
        # 输入类控件横向拉伸，占满面板，避免留白
        for w in (self.cmb_mode, self.cmb_port, self.cmb_baud,
                  self.le_ip, self.spin_tcp_port, self.btn_connect):
            w.setSizePolicy(_QSizePolicy.Expanding, w.sizePolicy().verticalPolicy())

    def _bind(self):
        self.cmb_mode.currentIndexChanged.connect(self._on_mode)
        self.btn_refresh.clicked.connect(self._refresh_ports)
        self.btn_connect.clicked.connect(self._toggle)

    # ---- 模式切换 ----
    def _on_mode(self, idx):
        is_serial = (idx == 1)
        is_tcp = (idx == 2)
        for w in (self.lbl_port, self.cmb_port, self.lbl_baud, self.cmb_baud):
            w.setVisible(is_serial)
        for w in (self.lbl_ip, self.le_ip, self.lbl_tcp_port, self.spin_tcp_port):
            w.setVisible(is_tcp)

    def set_test_lock(self, lock):
        """测试进行中锁定连接操作，防止误断连。lock=True 表示锁定。"""
        for w in (self.btn_connect, self.cmb_mode, self.cmb_port, self.cmb_baud,
                  self.le_ip, self.spin_tcp_port, self.btn_refresh):
            w.setEnabled(not lock)

    def _refresh_ports(self):
        self.cmb_port.clear()
        ports = self.channel.list_serial_ports()
        self.cmb_port.addItems(ports if ports else ["(none)"])

    # ---- 连接/断开 ----
    def _toggle(self):
        if not self.channel.connected:
            idx = self.cmb_mode.currentIndex()
            if idx == 0:
                ok, msg = self.channel.connect_sim()
            elif idx == 1:
                ok, msg = self.channel.connect_serial(
                    self.cmb_port.currentText(), int(self.cmb_baud.currentText()))
            else:
                ok, msg = self.channel.connect_tcp(self.le_ip.text(), self.spin_tcp_port.value())
            if ok:
                self.lbl_status.setText(T("● 已连接", "● ON"))
                self.lbl_status.setStyleSheet("color:#2ecc71;font-weight:bold;")
                self.btn_connect.setText(T("断开", "Disconnect"))
                self.btn_connect.setStyleSheet(
                    f"font-weight:bold;background:#e67e22;color:white;padding:{4*config.UI_SCALE:.0f}px {12*config.UI_SCALE:.0f}px;border-radius:{3*config.UI_SCALE:.0f}px;")
                self.cmb_mode.setEnabled(False)
                self.conn_changed.emit(True)
            else:
                QMessageBox.critical(self, T("错误", "Error"), msg)
        else:
            self.disconnect_requested.emit()
            self.channel.disconnect()
            self.lbl_status.setText(T("● 未连接", "● OFF"))
            self.lbl_status.setStyleSheet("color:#e74c3c;font-weight:bold;")
            self.btn_connect.setText(T("连接", "Connect"))
            self.btn_connect.setStyleSheet(
                f"font-weight:bold;background:#2ecc71;color:white;padding:{4*config.UI_SCALE:.0f}px {12*config.UI_SCALE:.0f}px;border-radius:{3*config.UI_SCALE:.0f}px;")
            self.cmb_mode.setEnabled(True)
            self.conn_changed.emit(False)
