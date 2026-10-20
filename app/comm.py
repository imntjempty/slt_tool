# -*- coding: utf-8 -*-
"""
通信通道：RS232 / TCP/IP / 仿真 三种模式。
封装连接、断开、命令收发、TCP/NDJSON 测试协议。
"""
import json
import socket
import time

try:
    import serial
    import serial.tools.list_ports
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False


class CommChannel:
    MODE_SIM = "SIM"
    MODE_SERIAL = "SERIAL"
    MODE_TCP = "TCP"

    def __init__(self, name=""):
        self.name = name
        self.mode = self.MODE_SIM
        self.ser = None
        self.sock = None
        self.connected = False

    # ---- 连接 ----
    def list_serial_ports(self):
        if not HAS_SERIAL:
            return []
        return [p.device for p in serial.tools.list_ports.comports()]

    def connect_sim(self):
        self.mode = self.MODE_SIM
        self.connected = True
        return True, f"[{self.name}] Sim connected"

    def connect_serial(self, port, baudrate=115200):
        try:
            self.ser = serial.Serial(port, baudrate, timeout=2)
            self.mode = self.MODE_SERIAL
            self.connected = True
            return True, f"[{self.name}] {port} @ {baudrate}"
        except Exception as e:
            return False, str(e)

    def connect_tcp(self, ip, port, timeout=3):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(timeout)
            self.sock.connect((ip, int(port)))
            self.mode = self.MODE_TCP
            self.connected = True
            return True, f"[{self.name}] {ip}:{port}"
        except Exception as e:
            return False, str(e)

    def disconnect(self):
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
            if self.sock:
                try:
                    self.sock.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                self.sock.close()
        except Exception:
            pass
        self.ser = None
        self.sock = None
        self.connected = False

    # ---- 基础命令 ----
    def send_cmd(self, cmd, expect_response=True, timeout=2.0):
        if self.mode == self.MODE_SIM:
            return "OK"
        if self.mode == self.MODE_SERIAL:
            self.ser.write((cmd + "\r\n").encode())
            if expect_response:
                self.ser.timeout = timeout
                return self.ser.readline().decode().strip()
            return ""
        # TCP 文本
        self.sock.sendall((cmd + "\r\n").encode())
        if expect_response:
            self.sock.settimeout(timeout)
            buf = b""
            while True:
                ch = self.sock.recv(1)
                if not ch:
                    break
                buf += ch
                if ch == b"\n":
                    break
            return buf.decode().strip()
        return ""

    # ---- TCP/NDJSON 协议 ----
    def _read_json_line(self, timeout=30.0):
        """读一行 JSON，超时/出错返回 None。"""
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
        """下发 TEST_START 并阻塞等待 TEST_DONE。返回 (passed, err_code)。"""
        if not self.sock:
            return False, "0xFFFF"
        try:
            self.sock.sendall(
                (json.dumps({"type": "TEST_START", "case": case_id}) + "\n").encode())
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
            elif mtype in ("TEST_STOPPED", "ERROR"):
                return False, "0xFFFF"

    def run_batch_tcp(self, cases, progress_cb=None, case_cb=None,
                      stop_check=None, pause_check=None, batch_timeout=600.0):
        """批量运行整个用例列表（TEST_RUN_ALL）。

        一次性下发整套用例给下位机，下位机本地排队执行；即使上位机崩溃断连，
        下位机仍会把整套跑完。逐个收集 TEST_DONE 直到 TEST_BATCH_DONE。
        case_cb(case_id, ok, err, aborted) 每完成一个用例回调一次。
        返回 (passed, failed, aborted)。
        """
        if not self.sock:
            return 0, 0, len(cases)
        try:
            self.sock.sendall(
                (json.dumps({"type": "TEST_RUN_ALL", "cases": cases}) + "\n").encode())
        except OSError:
            return 0, 0, len(cases)
        passed = failed = 0
        while True:
            # 暂停：阻塞在读取循环外（下位机仍在本地跑，恢复后读取积压数据）
            while pause_check and pause_check():
                time.sleep(0.2)
            if stop_check and stop_check():
                self.stop_test_tcp()
                break
            msg = self._read_json_line(timeout=batch_timeout)
            if msg is None:
                break  # 断连/超时 -> 剩余用例计为 abort
            mtype = msg.get("type", "")
            if mtype == "TEST_PROGRESS":
                if progress_cb:
                    progress_cb(msg.get("pct", 0), msg.get("msg", ""))
            elif mtype == "TEST_DONE":
                result = msg.get("result", "FAIL")
                ok = (result == "PASS")
                aborted = (result == "ABORT")
                err = "ABORTED" if aborted else msg.get("err", "0xFFFF")
                if case_cb:
                    case_cb(msg.get("case", ""), ok, err, aborted)
                if ok:
                    passed += 1
                elif not aborted:
                    failed += 1
            elif mtype == "TEST_BATCH_DONE":
                return (msg.get("pass", passed), msg.get("fail", failed),
                        msg.get("abort", len(cases) - passed - failed))
            elif mtype == "TEST_STOPPED":
                continue
        abort = len(cases) - passed - failed
        return passed, failed, abort

    def stop_test_tcp(self):
        """下发 TEST_STOP。"""
        if self.mode == self.MODE_TCP and self.connected:
            try:
                self.sock.sendall((json.dumps({"type": "TEST_STOP"}) + "\n").encode())
            except Exception:
                pass

    # ---- 固件烧录 / 升级 ----
    def send_fw(self, fw_type, data, version="", progress_cb=None, stop_check=None):
        """分块发送固件数据到下位机。

        协议: FW_BEGIN -> (FW_READY) -> 多块 FW_CHUNK -> (FW_CHUNK_OK) -> FW_END -> FW_DONE
        仿真模式直接模拟成功。返回 (ok, msg)。
        """
        import base64
        import hashlib
        if self.mode == self.MODE_SIM:
            if progress_cb:
                progress_cb(100, 100)
            return True, "模拟固件烧录完成"
        if not self.sock:
            return False, "未连接"
        size = len(data)
        sha = hashlib.sha256(data).hexdigest()
        try:
            self.sock.sendall((json.dumps(
                {"type": "FW_BEGIN", "file_type": fw_type, "size": size,
                 "sha256": sha, "version": version}) + "\n").encode())
        except OSError:
            return False, "连接已断开"
        m = self._read_json_line(timeout=10.0)
        if m is None or m.get("type") != "FW_READY":
            return False, "FW_BEGIN 无响应"
        chunk = 8192
        for off in range(0, size, chunk):
            if stop_check and stop_check():
                return False, "已中止"
            piece = data[off:off + chunk]
            try:
                self.sock.sendall((json.dumps(
                    {"type": "FW_CHUNK", "offset": off,
                     "data": base64.b64encode(piece).decode()}) + "\n").encode())
            except OSError:
                return False, "传输中断"
            m = self._read_json_line(timeout=15.0)
            if m is None or m.get("type") != "FW_CHUNK_OK":
                return False, "数据块无响应"
            if progress_cb:
                progress_cb(min(off + chunk, size), size)
        try:
            self.sock.sendall((json.dumps({"type": "FW_END"}) + "\n").encode())
        except OSError:
            return False, "传输中断"
        m = self._read_json_line(timeout=15.0)
        if m and m.get("type") == "FW_DONE":
            ok = m.get("ok", False)
            return ok, (f"烧录完成 size={m.get('size')}" if ok
                        else f"烧录失败: {m.get('err') or '校验不符'}")
        return False, "FW_END 无响应"
