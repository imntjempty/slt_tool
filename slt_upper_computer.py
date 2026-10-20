# -*- coding: utf-8 -*-
"""
SLT (System Level Test) Upper Computer Software - Multi-Station
=================================================================
Supports 4~6 test stations, each with independent connection & test execution.
"""

import sys
import os
import csv
import json
import time
import random
import socket
import threading
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QPushButton, QCheckBox, QComboBox, QLabel, QLineEdit,
    QTextEdit, QProgressBar, QTabWidget, QSpinBox, QDoubleSpinBox,
    QMessageBox, QStatusBar, QSplitter, QTableWidget, QTableWidgetItem,
    QHeaderView, QRadioButton, QFrame, QTreeWidget, QTreeWidgetItem,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QTextCursor

try:
    import serial
    import serial.tools.list_ports
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False

# ============================================================
# i18n: Chinese / English
# ============================================================
def _get_app_dir():
    # PyInstaller exe: use exe's directory; script: use script's directory
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

LANG_FILE = os.path.join(_get_app_dir(), ".lang")

def _load_lang():
    try:
        with open(LANG_FILE, "r") as f:
            return f.read().strip()
    except Exception:
        return "zh"

LANG = _load_lang()

def T(zh, en):
    return zh if LANG == "zh" else en

def set_lang(l):
    global LANG
    LANG = l
    try:
        with open(LANG_FILE, "w") as f:
            f.write(l)
    except Exception:
        pass

# ============================================================
TEST_CASES = [
    # (id, description, is_group=True means parent group)
    ("MBIST_GROUP",       "MBIST 内存自检",                           True),
    ("MBISR_CCD_SOC_HN", "  CCD SOC/HN-F BISR",                      False),
    ("MBIST_CCD_SOC_HN", "  CCD SOC/HN-F BIST",                       False),
    ("MBISR_N3",         "  N3 core BISR",                            False),
    ("MBIST_N3",         "  N3 core BIST",                            False),
    ("MBISR_PCD",        "  PCD BISR",                                False),
    ("MBIST_PCD",        "  PCD BIST",                                False),

    ("FW_BOOT_GROUP",     "Firmware Boot / 固件启动",                  True),
    ("FW_RSS",           "  RSS 固件启动",                            False),
    ("FW_SCP",           "  SCP 固件启动",                            False),
    ("FW_MCP",           "  MCP 固件启动",                            False),
    ("FW_BBL14",         "  bbl14 固件启动",                          False),
    ("FW_BL31",          "  bl31 固件启动",                           False),
    ("FW_UEFI",          "  UEFI 固件启动",                           False),
    ("FW_SECURE",        "  secure-firmware 启动",                     False),
    ("FW_LINUX",         "  Linux 系统启动",                          False),

    ("LOW_IO_GROUP",      "Low-speed IO / 低速IO",                     True),
    ("IO_MHU",           "  MHU 数据收发",                            False),
    ("IO_UART",          "  UART 日志输出",                           False),
    ("IO_I2C",           "  I2C / IPMI SSIF",                         False),
    ("IO_I3C",           "  I3C 读写",                               False),
    ("IO_ESPI",          "  eSPI 1/2/4线",                            False),
    ("IO_GPIO",          "  GPIO 开关机控制",                          False),

    ("DDR_GROUP",         "DDR Test",                                  True),
    ("DDR_BENCH",        "  性能基准测试",                            False),
    ("DDR_STRESS",       "  多任务并发与压力测试",                     False),
    ("DDR_EYE",          "  眼图与误码率测试",                         False),
    ("DDR_ECC",          "  ECC 测试",                               False),
    ("DDR_PWR",          "  动态功耗检测",                            False),
    ("DDR_RESET",        "  启动与复位测试",                           False),
    ("DDR_CROSS",        "  子系统交互测试",                           False),
    ("DDR_TIMING",       "  时序验证",                               False),
    ("DDR_BURNIN",       "  Burn-in 筛片",                           False),
    ("DDR_TRAIN",        "  Re-training",                           False),
    ("DDR_DIMM",         "  DIMM 兼容性测试",                          False),
    ("DDR_VOLT",         "  电压裕量测试",                            False),

    ("PCIE_GROUP",        "PCIe Test",                                True),
    ("PCIE_LINK",        "  链路训练与状态稳定性",                    False),
    ("PCIE_BW",          "  吞吐量与带宽压力",                        False),
    ("PCIE_STRESS",      "  长时间稳定性老化",                        False),
    ("PCIE_AER",         "  AER错误处理与容错",                       False),
    ("PCIE_INTR",        "  INTx/MSI/MSI-X压力",                     False),
    ("PCIE_ASPM",        "  ASPM电源管理与低功耗",                    False),
    ("PCIE_HOTPLUG",     "  热插拔与链路重训练",                      False),
    ("PCIE_CFG",         "  寄存器配置与兼容性",                       False),

    ("IRQ_GROUP",         "Interrupt / 中断",                          True),
    ("IRQ_PPI",          "  PPI 中断",                               False),
    ("IRQ_SGI",          "  SGI 中断",                               False),
    ("IRQ_SPI",          "  SPI 中断",                               False),
    ("IRQ_LPI",          "  LPI 中断",                               False),
    ("IRQ_GIC_C2C",      "  GIC 跨die中断",                          False),
    ("IRQ_GIC_S2S",      "  GIC 跨socket中断",                       False),
    ("IRQ_VSGI",         "  vSGI 中断",                              False),
    ("IRQ_VLPI",         "  vLPI 中断",                              False),

    ("RAS_GROUP",         "RAS-Extension",                            True),
    ("RAS_CMN",          "  CMN RAS",                                False),
    ("RAS_GIC",          "  GIC RAS",                                False),
    ("RAS_CORE",         "  CORE RAS",                               False),
    ("RAS_PCIE",         "  PCIe/CXL RAS",                           False),
    ("RAS_UCIE",         "  UCIe RAS",                               False),
    ("RAS_DDR",          "  DDR RAS",                                False),
    ("RAS_SMMU",         "  SMMU RAS",                               False),

    ("SEC_RUNTIME",       "Security Runtime",                          False),

    ("STAB_GROUP",        "Mixed Stability / 混合稳定性",              True),
    ("STAB_X265",        "  x265 视频编码",                           False),
    ("STAB_MYSQL",       "  MySQL 高并发",                            False),
    ("STAB_SPEC",        "  SpecCPU2017",                            False),
    ("STAB_MEM",         "  内存压测",                               False),
    ("STAB_CPU",         "  CPU 压测",                               False),
    ("STAB_NVME",        "  NVMe 压测",                              False),
    ("STAB_MIXED",       "  混合场景压测",                            False),

    ("POWER_THERMAL",     "Power & Thermal / 功耗热管理",              False),
]

NUM_STATIONS = 6

BIN_PASS  = "BIN0 - PASS"
BIN_FAIL  = "BIN1 - FAIL"
BIN_ABORT = "BIN2 - ABORT"
BINS = [BIN_PASS, BIN_FAIL, BIN_ABORT]


# ============================================================
# CommChannel: RS232 / TCP / Sim
# ============================================================
class CommChannel:
    MODE_SIM = "SIM"; MODE_SERIAL = "SERIAL"; MODE_TCP = "TCP"

    def __init__(self, name=""):
        self.name = name; self.mode = self.MODE_SIM
        self.ser = None; self.sock = None; self.connected = False

    def list_serial_ports(self):
        if not HAS_SERIAL: return []
        return [p.device for p in serial.tools.list_ports.comports()]

    def connect_sim(self):
        self.mode = self.MODE_SIM; self.connected = True
        return True, f"[{self.name}] Sim connected"

    def connect_serial(self, port, baudrate=115200):
        try:
            self.ser = serial.Serial(port, baudrate, timeout=2)
            self.mode = self.MODE_SERIAL; self.connected = True
            return True, f"[{self.name}] {port} @ {baudrate}"
        except Exception as e:
            return False, str(e)

    def connect_tcp(self, ip, port, timeout=3):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(timeout)
            self.sock.connect((ip, int(port)))
            self.mode = self.MODE_TCP; self.connected = True
            return True, f"[{self.name}] {ip}:{port}"
        except Exception as e:
            return False, str(e)

    def disconnect(self):
        try:
            if self.ser and self.ser.is_open: self.ser.close()
            if self.sock:
                try: self.sock.shutdown(socket.SHUT_RDWR)
                except Exception: pass
                self.sock.close()
        except Exception: pass
        self.ser = None; self.sock = None; self.connected = False

    def send_cmd(self, cmd, expect_response=True, timeout=2.0):
        if self.mode == self.MODE_SIM: return "OK"
        if self.mode == self.MODE_SERIAL:
            self.ser.write((cmd + "\r\n").encode())
            if expect_response:
                self.ser.timeout = timeout
                return self.ser.readline().decode().strip()
            return ""
        else:  # TCP
            self.sock.sendall((cmd + "\r\n").encode())
            if expect_response:
                self.sock.settimeout(timeout)
                buf = b""
                while True:
                    ch = self.sock.recv(1)
                    if not ch: break
                    buf += ch
                    if ch == b"\n": break
                return buf.decode().strip()
            return ""

    def _read_json_line(self, timeout=30.0):
        """Read one JSON line from TCP socket, return dict or None on timeout/error."""
        if not self.sock:
            return None
        try:
            self.sock.settimeout(timeout)
            buf = b""
            while True:
                ch = self.sock.recv(1)
                if not ch:
                    return None
                buf += ch
                if ch == b"\n":
                    try:
                        return json.loads(buf.decode().strip())
                    except json.JSONDecodeError:
                        return None
        except (socket.timeout, OSError):
            return None

    def run_test_tcp(self, case_id, progress_cb=None):
        """Send TEST_START over TCP/JSON protocol, block until TEST_DONE.
        progress_cb: optional callable(pct, msg)
        Returns (passed: bool, err_code: str).
        """
        if not self.sock:
            return False, "0xFFFF"
        try:
            self.sock.sendall((json.dumps({"type": "TEST_START", "case": case_id}) + "\n").encode())
        except OSError:
            return False, "0xFFFF"
        while True:
            msg = self._read_json_line(timeout=120.0)
            if msg is None:
                return False, "0xFFFF"
            mtype = msg.get("type", "")
            if mtype == "TEST_PROGRESS":
                if progress_cb:
                    progress_cb(msg.get("pct", 0), msg.get("msg", ""))
            elif mtype == "TEST_DONE":
                result = msg.get("result", "FAIL")
                err = msg.get("err", "0xFFFF")
                return (result == "PASS"), err
            elif mtype == "TEST_STOPPED":
                return False, "0xFFFF"
            elif mtype == "ERROR":
                return False, "0xFFFF"

    def stop_test_tcp(self):
        """Send TEST_STOP over TCP."""
        if self.mode == self.MODE_TCP and self.connected:
            try:
                self.sock.sendall((json.dumps({"type": "TEST_STOP"}) + "\n").encode())
            except Exception:
                pass


# ============================================================
# Test worker (per station)
# ============================================================
class TestWorker(QThread):
    log_signal         = pyqtSignal(str, str)
    progress_signal    = pyqtSignal(int, int)
    case_start_signal  = pyqtSignal(str)
    case_result_signal = pyqtSignal(str, bool, str, int)  # (case_id, ok, err, loop)
    finished_signal    = pyqtSignal(dict)

    def __init__(self, selected_cases, board: CommChannel, sim_mode=True, loops=1, parent=None):
        super().__init__(parent)
        self.selected_cases = selected_cases
        self.board = board; self.sim_mode = sim_mode; self.loops = loops
        self._stop = False
        self._pause = threading.Event()

    def stop(self): self._stop = True
    def pause(self): self._pause.set()
    def resume(self): self._pause.clear()

    def _wait_if_paused(self):
        """Block until resumed or stopped."""
        while self._pause.is_set() and not self._stop:
            time.sleep(0.2)

    def run(self):
        total = len(self.selected_cases)
        passed = failed = aborted = 0
        self.log_signal.emit("=" * 50, "info")
        self.log_signal.emit(f"开始测试 | 用例数={total} | 循环={self.loops} | "
                             f"{'仿真' if self.sim_mode else '实机'}", "info")
        self.log_signal.emit("=" * 50, "info")

        for loop in range(1, self.loops + 1):
            if self._stop:
                aborted += total - (passed + failed)
                self.log_signal.emit("*** 已中止 ***", "warn"); break
            if self.loops > 1:
                self.log_signal.emit(f"--- 第 {loop}/{self.loops} 轮 ---", "info")
            for idx, (cid, desc, _opt) in enumerate(self.selected_cases, 1):
                if self._stop:
                    aborted += total - (passed + failed)
                    self.log_signal.emit("*** 已中止 ***", "warn"); break
                self._wait_if_paused()
                if self._stop:
                    aborted += total - (passed + failed)
                    self.log_signal.emit("*** ABORTED ***", "warn"); break
                self.progress_signal.emit(idx, total)
                self.case_start_signal.emit(cid)
                self.log_signal.emit(f"[Chip{loop}][{idx}/{total}] {desc} ...", "info")
                ok, err = self._run_one(cid)
                if self._stop:
                    aborted += 1
                    self.case_result_signal.emit(cid, False, "ABORTED", loop); break
                if ok:
                    passed += 1
                    self.log_signal.emit(f"  -> 通过 (0x0000)", "ok")
                    self.case_result_signal.emit(cid, True, "0x0000", loop)
                else:
                    failed += 1
                    self.log_signal.emit(f"  -> 失败 ({err})", "error")
                    self.case_result_signal.emit(cid, False, err, loop)
            if self._stop: break

        summary = {"pass": passed, "fail": failed, "abort": aborted, "total": total * self.loops}
        self.log_signal.emit(f"汇总: 通过={passed} 失败={failed} 中止={aborted}",
                             "ok" if failed == 0 else "warn")
        self.finished_signal.emit(summary)

    def _run_one(self, cid):
        if self.sim_mode:
            time.sleep(random.uniform(0.2, 0.8))
            if random.random() < 0.85: return True, "0x0000"
            return False, f"0x{random.randint(0x1000, 0xFFFF):04X}"
        # real hardware: use JSON/TCP protocol
        if self.board.mode == CommChannel.MODE_TCP:
            def _cb(pct, msg):
                if msg:
                    self.log_signal.emit(f"    [{pct}%] {msg}", "info")
            return self.board.run_test_tcp(cid, progress_cb=_cb)
        else:
            # serial: simple text protocol
            resp = self.board.send_cmd(f"TEST {cid}", timeout=10)
            if "PASS" in resp.upper(): return True, "0x0000"
            parts = resp.split()
            return False, parts[-1] if len(parts) > 1 else "0xFFFF"


# ============================================================
# Connection panel (reusable)
# ============================================================
class ConnPanel(QGroupBox):
    conn_changed = pyqtSignal(bool)
    disconnect_requested = pyqtSignal()

    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.channel = CommChannel(title)
        self._build()

    def _build(self):
        g = QGridLayout(self)
        g.addWidget(QLabel(T("类型:", "Type:")), 0, 0)
        self.cmb_mode = QComboBox()
        self.cmb_mode.addItems([T("仿真模式", "Simulation"), T("RS232串口", "RS232"), T("TCP/IP网络", "TCP/IP")])
        self.cmb_mode.currentIndexChanged.connect(self._on_mode)
        g.addWidget(self.cmb_mode, 0, 1, 1, 2)

        self.lbl_port = QLabel(T("端口:", "Port:")); self.cmb_port = QComboBox()
        self.cmb_port.setMinimumWidth(90)
        btn_ref = QPushButton("↻")
        btn_ref.setFixedWidth(26)
        btn_ref.clicked.connect(self._refresh)
        self.lbl_baud = QLabel(T("波特率:", "Baud:"))
        self.cmb_baud = QComboBox()
        self.cmb_baud.addItems(["9600", "115200", "921600", "1500000"])
        self.cmb_baud.setCurrentText("115200")
        g.addWidget(self.lbl_port, 1, 0); g.addWidget(self.cmb_port, 1, 1)
        g.addWidget(btn_ref, 1, 2); g.addWidget(self.lbl_baud, 1, 3)
        g.addWidget(self.cmb_baud, 1, 4)

        self.lbl_ip = QLabel(T("IP地址:", "IP:")); self.le_ip = QLineEdit("192.168.1.100")
        self.lbl_tp = QLabel(T("TCP端口:", "TCP Port:")); self.spin_tp = QSpinBox()
        self.spin_tp.setRange(1, 65535); self.spin_tp.setValue(5001)
        g.addWidget(self.lbl_ip, 2, 0); g.addWidget(self.le_ip, 2, 1)
        g.addWidget(self.lbl_tp, 2, 3); g.addWidget(self.spin_tp, 2, 4)

        self.btn = QPushButton(T("连接", "Connect"))
        self.btn.setStyleSheet("font-weight:bold;background:#2ecc71;color:white;padding:4px 12px;border-radius:3px;")
        self.btn.clicked.connect(self._toggle)
        g.addWidget(self.btn, 3, 0, 1, 2)
        self.lbl_st = QLabel(T("● 未连接", "● OFF"))
        self.lbl_st.setStyleSheet("color:#e74c3c;font-weight:bold;")
        g.addWidget(self.lbl_st, 3, 2, 1, 3)
        self._on_mode(0)
        self._refresh()

    def _on_mode(self, idx):
        s = (idx == 1); n = (idx == 2)
        for w in (self.lbl_port, self.cmb_port, self.lbl_baud, self.cmb_baud): w.setVisible(s)
        for w in (self.lbl_ip, self.le_ip, self.lbl_tp, self.spin_tp): w.setVisible(n)

    def _refresh(self):
        self.cmb_port.clear()
        p = self.channel.list_serial_ports()
        self.cmb_port.addItems(p if p else ["(none)"])

    def _toggle(self):
        if not self.channel.connected:
            idx = self.cmb_mode.currentIndex()
            if idx == 0: ok, msg = self.channel.connect_sim()
            elif idx == 1: ok, msg = self.channel.connect_serial(self.cmb_port.currentText(), int(self.cmb_baud.currentText()))
            else: ok, msg = self.channel.connect_tcp(self.le_ip.text(), self.spin_tp.value())
            if ok:
                self.lbl_st.setText(T("● 已连接", "● ON")); self.lbl_st.setStyleSheet("color:#2ecc71;font-weight:bold;")
                self.btn.setText(T("断开", "Disconnect")); self.btn.setStyleSheet("font-weight:bold;background:#e67e22;color:white;padding:4px 12px;border-radius:3px;")
                self.cmb_mode.setEnabled(False)
                self.conn_changed.emit(True)
            else:
                QMessageBox.critical(self, T("错误", "Error"), msg)
        else:
            self.disconnect_requested.emit()
            self.channel.disconnect()
            self.lbl_st.setText(T("● 未连接", "● OFF")); self.lbl_st.setStyleSheet("color:#e74c3c;font-weight:bold;")
            self.btn.setText(T("连接", "Connect")); self.btn.setStyleSheet("font-weight:bold;background:#2ecc71;color:white;padding:4px 12px;border-radius:3px;")
            self.cmb_mode.setEnabled(True)
            self.conn_changed.emit(False)


# ============================================================
# Per-station panel
# ============================================================
class StationPanel(QWidget):
    log_to_global = pyqtSignal(str, str, str)  # (station, msg, level)
    status_changed = pyqtSignal(str, dict)     # (station_name, status_dict)

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
        self._build()

    def _build(self):
        h = QVBoxLayout(self)

        # connections
        conn_row = QHBoxLayout()
        self.p_handler = ConnPanel(T("Handler 控制箱", "Handler"))
        self.p_board = ConnPanel(T("Board 测试板", "Board"))
        self.p_board.disconnect_requested.connect(self._on_board_disconnect)
        conn_row.addWidget(self.p_handler)
        conn_row.addWidget(self.p_board)
        h.addLayout(conn_row)

        # middle: tree + right side
        mid = QSplitter(Qt.Horizontal)

        # left: test tree
        left = QGroupBox(T("测试用例", "Test Cases"))
        lv = QVBoxLayout(left)
        btn_row = QHBoxLayout()
        b_all = QPushButton(T("全选", "All")); b_all.clicked.connect(lambda: self._set_all(True))
        b_clr = QPushButton(T("清空", "Clear")); b_clr.clicked.connect(lambda: self._set_all(False))
        btn_row.addWidget(b_all); btn_row.addWidget(b_clr)
        lv.addLayout(btn_row)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([T("测试项", "Case"), T("状态", "Status")])
        self.tree.setColumnWidth(0, 220); self.tree.setColumnWidth(1, 70)
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Fixed)
        self.tree.setStyleSheet("QTreeWidget{font-size:12px;}QTreeWidget::item{height:22px;}")

        # Build tree: group items (opt=True) are parents, following items are children
        GROUP_IDS = {c[0] for c in TEST_CASES if c[2]}
        current_parent = None
        for cid, desc, is_group in TEST_CASES:
            if is_group:
                p = QTreeWidgetItem(self.tree, [desc, "--"])
                p.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
                p.setCheckState(0, Qt.Checked)  # groups checked by default
                f = p.font(0); f.setBold(True); p.setFont(0, f)
                self.case_item_map[cid] = p
                current_parent = p
            else:
                if current_parent is not None:
                    c = QTreeWidgetItem(current_parent, [desc, "--"])
                    c.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
                    c.setCheckState(0, Qt.Checked)
                    self.case_item_map[cid] = c
                else:
                    it = QTreeWidgetItem(self.tree, [desc, "--"])
                    it.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
                    it.setCheckState(0, Qt.Checked)
                    self.case_item_map[cid] = it
        # collapse all groups by default
        self.tree.collapseAll()
        lv.addWidget(self.tree)

        loop_row = QHBoxLayout()
        loop_row.addWidget(QLabel(T("本机台芯片目标数:", "Target Chips:")))
        self.spin_loop = QSpinBox(); self.spin_loop.setRange(1, 999); self.spin_loop.setValue(1)
        loop_row.addWidget(self.spin_loop); loop_row.addStretch()
        lv.addLayout(loop_row)
        mid.addWidget(left)

        # right: results table + bin
        right = QWidget()
        rv = QVBoxLayout(right)
        self.tbl = QTableWidget(0, 5)
        self.tbl.setHorizontalHeaderLabels([T("芯片", "Chip"), T("测试项", "Case"), T("描述", "Description"), T("结果", "Result"), T("错误码", "Error")])
        self.tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        rv.addWidget(self.tbl)

        bin_row = QHBoxLayout()
        self.bin_labels = {}
        for b in BINS:
            box = QGroupBox(b)
            bl = QVBoxLayout(box)
            lbl = QLabel("0"); lbl.setAlignment(Qt.AlignCenter)
            lbl.setFont(QFont("Arial", 20, QFont.Bold))
            clr = {"BIN0 - PASS": "#27ae60", "BIN1 - FAIL": "#e74c3c", "BIN2 - ABORT": "#f39c12"}[b]
            lbl.setStyleSheet(f"color:{clr};")
            bl.addWidget(lbl); self.bin_labels[b] = lbl
            bin_row.addWidget(box)
        rv.addLayout(bin_row)
        mid.addWidget(right)
        mid.setSizes([280, 500])
        h.addWidget(mid, 1)

        # bottom: start/stop + progress
        bot = QHBoxLayout()
        self.btn_start = QPushButton(T("▶ 开始", "▶ Start"))
        self.btn_start.setStyleSheet("font-weight:bold;background:#2ecc71;color:white;padding:6px 20px;border-radius:4px;")
        self.btn_start.clicked.connect(self.start_test)
        self.btn_pause = QPushButton(T("⏸ 暂停", "⏸ Pause"))
        self.btn_pause.setEnabled(False)
        self.btn_pause.setStyleSheet("font-weight:bold;background:#f39c12;color:white;padding:6px 16px;border-radius:4px;")
        self.btn_pause.clicked.connect(self.pause_test)
        self.btn_resume = QPushButton(T("⏵ 继续", "⏵ Resume"))
        self.btn_resume.setEnabled(False)
        self.btn_resume.setStyleSheet("font-weight:bold;background:#3498db;color:white;padding:6px 16px;border-radius:4px;")
        self.btn_resume.clicked.connect(self.resume_test)
        self.btn_stop = QPushButton(T("■ 停止", "■ Stop"))
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet("font-weight:bold;background:#e74c3c;color:white;padding:6px 20px;border-radius:4px;")
        self.btn_stop.clicked.connect(self.stop_test)
        bot.addWidget(self.btn_start); bot.addWidget(self.btn_pause); bot.addWidget(self.btn_resume); bot.addWidget(self.btn_stop)
        bot.addSpacing(20)
        bot.addWidget(QLabel(T("进度:", "Progress:")))
        self.progress = QProgressBar(); self.progress.setMinimumWidth(250)
        bot.addWidget(self.progress)
        self.lbl_cur = QLabel(T("空闲", "Idle")); self.lbl_cur.setStyleSheet("font-weight:bold;")
        bot.addWidget(self.lbl_cur)
        bot.addStretch()
        h.addLayout(bot)

    def _set_all(self, v):
        for it in self.case_item_map.values():
            it.setCheckState(0, Qt.Checked if v else Qt.Unchecked)

    def _get_selected(self):
        cmap = {c[0]: c for c in TEST_CASES}
        GROUP_IDS = {c[0] for c in TEST_CASES if c[2]}
        return [cmap[cid] for cid, it in self.case_item_map.items()
                if cid not in GROUP_IDS and it.checkState(0) == Qt.Checked]

    def _set_status(self, cid, txt, color):
        it = self.case_item_map.get(cid)
        if not it: return
        it.setText(1, txt)
        it.setForeground(1, QColor(color) if color else QColor("#2c3e50"))

    def start_test(self):
        if not self.p_board.channel.connected:
            QMessageBox.warning(self, T("未连接", "Not Connected"), f"{self.station_name}: {T('请先连接测试板!', 'connect Board first!')}")
            return
        sel = self._get_selected()
        if not sel:
            QMessageBox.warning(self, T("无测试项", "No Cases"), T("请至少勾选一个测试用例!", "Select at least one case!"))
            return

        # wait for old worker if any
        try:
            if self.worker and self.worker.isRunning():
                self.worker.stop()
                self.worker.wait(3000)
        except RuntimeError:
            self.worker = None

        self.tbl.setRowCount(0)
        self.bin_counts = {BIN_PASS: 0, BIN_FAIL: 0, BIN_ABORT: 0}
        self.chip_bin = {"total": 0, "bin0": 0, "bin1": 0, "bin2": 0}
        self._loop_has_fail = False
        self._loop_has_abort = False
        for b, l in self.bin_labels.items(): l.setText("0")
        self.progress.setValue(0)
        for cid in self.case_item_map: self._set_status(cid, "--", None)

        sim = (self.p_board.channel.mode == CommChannel.MODE_SIM)
        loops = self.spin_loop.value()
        self.worker = TestWorker(sel, self.p_board.channel, sim_mode=sim, loops=loops)
        self.worker.log_signal.connect(lambda m, lv: self.log_to_global.emit(self.station_name, m, lv))
        self.worker.progress_signal.connect(self._on_prog)
        self.worker.case_start_signal.connect(lambda c: self._set_status(c, "RUN", "#f39c12"))
        self.worker.case_result_signal.connect(self._on_result)
        self.worker.finished_signal.connect(self._on_done)
        # proper thread cleanup
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

        self.btn_start.setEnabled(False); self.btn_stop.setEnabled(True)
        self.btn_pause.setEnabled(True); self.btn_resume.setEnabled(False)
        self.lbl_cur.setText(T("测试中...", "Running..."))

    def pause_test(self):
        try:
            if self.worker and self.worker.isRunning():
                self.worker.pause()
                self.btn_pause.setEnabled(False); self.btn_resume.setEnabled(True)
                self.lbl_cur.setText(T("已暂停", "Paused"))
                self.log_to_global.emit(self.station_name, T("已暂停", "PAUSED"), "warn")
        except RuntimeError:
            self.worker = None

    def resume_test(self):
        try:
            if self.worker and self.worker.isRunning():
                self.worker.resume()
                self.btn_pause.setEnabled(True); self.btn_resume.setEnabled(False)
                self.lbl_cur.setText(T("测试中...", "Running..."))
                self.log_to_global.emit(self.station_name, T("继续测试", "RESUMED"), "info")
        except RuntimeError:
            self.worker = None

    def _on_board_disconnect(self):
        # stop running test before closing socket
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
                # tell board to stop via TCP if connected
                self.p_board.channel.stop_test_tcp()
                self.log_to_global.emit(self.station_name, T("已请求停止...", "Stop requested..."), "warn")
        except RuntimeError:
            self.worker = None

    def _on_prog(self, cur, total):
        self.progress.setMaximum(total); self.progress.setValue(cur)
        self.lbl_cur.setText(f"[{cur}/{total}]")

    def _on_result(self, cid, ok, err, loop=1):
        desc = {c[0]: c[1] for c in TEST_CASES}.get(cid, cid)
        if err == "ABORTED": self._set_status(cid, T("中止", "ABORT"), "#f39c12")
        elif ok: self._set_status(cid, T("通过", "PASS"), "#27ae60")
        else: self._set_status(cid, T("失败", "FAIL"), "#e74c3c")

        # track per-loop chip BIN
        if loop != self._current_loop:
            # new loop started, close out previous loop
            if self._current_loop > 0:
                self.chip_bin["total"] += 1
                if self._loop_has_abort: self.chip_bin["bin2"] += 1
                elif self._loop_has_fail: self.chip_bin["bin1"] += 1
                else: self.chip_bin["bin0"] += 1
            self._current_loop = loop
            self._loop_has_fail = False
            self._loop_has_abort = False
        if not ok:
            if err == "ABORTED": self._loop_has_abort = True
            else: self._loop_has_fail = True

        r = self.tbl.rowCount(); self.tbl.insertRow(r)
        self.tbl.setItem(r, 0, QTableWidgetItem(f"Chip{loop}"))
        self.tbl.setItem(r, 1, QTableWidgetItem(cid))
        self.tbl.setItem(r, 2, QTableWidgetItem(desc))
        ri = QTableWidgetItem("PASS" if ok else "FAIL")
        ri.setForeground(QColor("#27ae60") if ok else QColor("#e74c3c"))
        self.tbl.setItem(r, 3, ri)
        self.tbl.setItem(r, 4, QTableWidgetItem(err))

        if ok: self.bin_counts[BIN_PASS] += 1
        elif err == "ABORTED": self.bin_counts[BIN_ABORT] += 1
        else: self.bin_counts[BIN_FAIL] += 1
        for b, l in self.bin_labels.items(): l.setText(str(self.bin_counts[b]))

        self.status_changed.emit(self.station_name, {
            "pass": self.bin_counts[BIN_PASS], "fail": self.bin_counts[BIN_FAIL],
            "abort": self.bin_counts[BIN_ABORT], "current": cid,
            "running": True,
            "chip_total": self.chip_bin["total"],
            "chip_bin0": self.chip_bin["bin0"],
            "chip_bin1": self.chip_bin["bin1"],
            "chip_bin2": self.chip_bin["bin2"],
        })

    def _on_done(self, summary):
        self.btn_start.setEnabled(True); self.btn_stop.setEnabled(False)
        self.btn_pause.setEnabled(False); self.btn_resume.setEnabled(False)
        self.lbl_cur.setText(T("完成", "Done"))
        # close out last loop's chip BIN
        if self._current_loop > 0:
            self.chip_bin["total"] += 1
            if self._loop_has_abort: self.chip_bin["bin2"] += 1
            elif self._loop_has_fail: self.chip_bin["bin1"] += 1
            else: self.chip_bin["bin0"] += 1
            self._current_loop = 0
        self.status_changed.emit(self.station_name, {
            "pass": summary["pass"], "fail": summary["fail"],
            "abort": summary["abort"], "current": "--", "running": False,
            "chip_total": self.chip_bin["total"],
            "chip_bin0": self.chip_bin["bin0"],
            "chip_bin1": self.chip_bin["bin1"],
            "chip_bin2": self.chip_bin["bin2"],
        })


# ============================================================
# Main Window
# ============================================================
class MainWin(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(T("SLT 多机台测试上位机", "SLT Multi-Station Tester"))
        self.resize(1400, 900)
        self.stations = {}

        # log file
        self.log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(self.log_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(self.log_dir, f"slt_multi_{ts}.log")
        self._fh = open(self.log_file, "a", encoding="utf-8")

        central = QWidget(); self.setCentralWidget(central)
        v = QVBoxLayout(central)

        # global buttons
        top = QHBoxLayout()
        self.btn_all_start = QPushButton(T("▶ 全部开始", "▶ START ALL"))
        self.btn_all_start.setStyleSheet("font-size:14px;font-weight:bold;background:#2ecc71;color:white;padding:8px 30px;border-radius:5px;")
        self.btn_all_start.clicked.connect(self._start_all)
        self.btn_all_stop = QPushButton(T("■ 全部停止", "■ STOP ALL"))
        self.btn_all_stop.setStyleSheet("font-size:14px;font-weight:bold;background:#e74c3c;color:white;padding:8px 30px;border-radius:5px;")
        self.btn_all_stop.clicked.connect(self._stop_all)
        top.addWidget(self.btn_all_start); top.addWidget(self.btn_all_stop)
        top.addStretch()
        # language switcher
        top.addWidget(QLabel(T("语言:", "Lang:")))
        self.cmb_lang = QComboBox()
        self.cmb_lang.addItem("简体中文", "zh")
        self.cmb_lang.addItem("English", "en")
        self.cmb_lang.setCurrentIndex(0 if LANG == "zh" else 1)
        self.cmb_lang.setStyleSheet("padding:4px 12px;")
        self.cmb_lang.currentIndexChanged.connect(self._on_lang_changed)
        top.addWidget(self.cmb_lang)
        v.addLayout(top)

        # tabs: dashboard + stations
        self.tabs = QTabWidget()
        self.dashboard = self._build_dashboard()
        self.tabs.addTab(self.dashboard, T("  总览  ", "  Dashboard  "))
        for i in range(1, NUM_STATIONS + 1):
            name = f"{T('机台', 'Station')} {i}"
            sp = StationPanel(name)
            sp.log_to_global.connect(self._global_log)
            sp.status_changed.connect(self._update_dash)
            self.stations[name] = sp
            self.tabs.addTab(sp, f"  {name}  ")
        # tabs + log separated by splitter (draggable)
        splitter_v = QSplitter(Qt.Vertical)
        splitter_v.addWidget(self.tabs)

        # global log at bottom
        gb = QGroupBox(T("全局日志", "Global Log"))
        gl = QVBoxLayout(gb)
        self.txt_log = QTextEdit(); self.txt_log.setReadOnly(True)
        self.txt_log.setFont(QFont("Courier New", 9))
        gl.addWidget(self.txt_log)
        splitter_v.addWidget(gb)
        splitter_v.setStretchFactor(0, 3)
        splitter_v.setStretchFactor(1, 1)
        splitter_v.setSizes([600, 200])
        v.addWidget(splitter_v, 1)

        self._log(T("系统启动", "Session started"), "info")

    def _build_dashboard(self):
        w = QWidget(); l = QVBoxLayout(w)
        self.tbl_dash = QTableWidget(0, 8)
        self.tbl_dash.setHorizontalHeaderLabels([
            T("机台", "Station"), T("连接", "Conn"), T("当前测试项", "Current"),
            T("芯片总数", "Chips"), T("BIN0 良品", "BIN0 Good"),
            T("BIN1 不良", "BIN1 Bad"), T("BIN2 中止", "BIN2 Abort"),
            T("状态", "Status")
        ])
        self.tbl_dash.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_dash.verticalHeader().setVisible(False)
        for i in range(NUM_STATIONS):
            r = self.tbl_dash.rowCount(); self.tbl_dash.insertRow(r)
            self.tbl_dash.setItem(r, 0, QTableWidgetItem(f"{T('机台', 'Station')} {i+1}"))
            self.tbl_dash.setItem(r, 1, QTableWidgetItem("--"))
            self.tbl_dash.setItem(r, 2, QTableWidgetItem("--"))
            for c in (3, 4, 5, 6): self.tbl_dash.setItem(r, c, QTableWidgetItem("0"))
            st = QTableWidgetItem(T("空闲", "IDLE")); st.setForeground(QColor("#95a5a6"))
            self.tbl_dash.setItem(r, 7, st)
        l.addWidget(self.tbl_dash)
        return w

    def _update_dash(self, name, status):
        idx = int(name.split()[-1]) - 1
        conn = T("已连接", "ON") if self.stations[name].p_board.channel.connected else T("未连接", "OFF")
        self.tbl_dash.item(idx, 1).setText(conn)
        self.tbl_dash.item(idx, 2).setText(status.get("current", "--"))
        self.tbl_dash.item(idx, 3).setText(str(status.get("chip_total", 0)))
        self.tbl_dash.item(idx, 4).setText(str(status.get("chip_bin0", 0)))
        self.tbl_dash.item(idx, 5).setText(str(status.get("chip_bin1", 0)))
        self.tbl_dash.item(idx, 6).setText(str(status.get("chip_bin2", 0)))
        st = self.tbl_dash.item(idx, 7)
        if status.get("running"):
            st.setText(T("测试中", "RUNNING")); st.setForeground(QColor("#f39c12"))
        elif status.get("chip_bin1", 0) > 0 or status.get("fail", 0) > 0:
            st.setText(T("失败", "FAIL")); st.setForeground(QColor("#e74c3c"))
        else:
            st.setText(T("空闲", "IDLE")); st.setForeground(QColor("#95a5a6"))

    def _start_all(self):
        for name, sp in self.stations.items():
            if sp.p_board.channel.connected:
                sp.start_test()
            else:
                self._log(f"{name}: {T('测试板未连接，已跳过', 'Board not connected, skipped')}", "warn")

    def _stop_all(self):
        for sp in self.stations.values():
            sp.stop_test()

    def _on_lang_changed(self, idx):
        new = self.cmb_lang.itemData(idx)
        if new == LANG:
            return
        set_lang(new)
        QMessageBox.information(self, T("提示", "Info"),
            T("语言已切换，请手动重启程序", "Language changed, please restart manually"))
        QApplication.quit()

    def _global_log(self, station, msg, level):
        ts = datetime.now().strftime("%H:%M:%S")
        colors = {"info": "#2c3e50", "ok": "#27ae60", "warn": "#f39c12", "error": "#e74c3c"}
        c = colors.get(level, "#2c3e50")
        self.txt_log.append(
            f'<span style="color:#95a5a6">[{ts}]</span> '
            f'<span style="color:#3498db;font-weight:bold">[{station}]</span> '
            f'<span style="color:{c}">{msg}</span>')
        self.txt_log.moveCursor(QTextCursor.End)
        try:
            self._fh.write(f"[{ts}] [{station}] {msg}\n"); self._fh.flush()
        except Exception: pass

    def _log(self, msg, level="info"):
        self._global_log("SYS", msg, level)

    def closeEvent(self, e):
        try: self._fh.close()
        except Exception: pass
        e.accept()


def excepthook(typ, val, tb):
    import traceback
    err = "".join(traceback.format_exception(typ, val, tb))
    print(err, file=sys.stderr)
    try:
        QMessageBox.critical(None, "Error", err[-2000:])
    except Exception: pass


def main():
    sys.excepthook = excepthook
    # high DPI support (must be before QApplication)
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(
        "QWidget{font-size:13px;}"
        "QComboBox{font-size:13px; padding:3px; min-height:20px;}"
        "QComboBox QAbstractItemView{font-size:13px; selection-background-color:#3498db;}"
        "QComboBox QAbstractItemView::item{min-height:24px; padding:4px;}"
        "QSpinBox{font-size:13px;} QLineEdit{font-size:13px;}"
        "QMenu{font-size:13px;}"
    )
    w = MainWin()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
