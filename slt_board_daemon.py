#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SLT Board Daemon - runs on DUT Linux board.
Listens on TCP:5001, executes test cases, reports results back to upper PC.

Usage:
    python3 slt_board_daemon.py [--port 5001]

Each test case is a Python function decorated with @register_test.
Replace the actual test logic with real hardware checks.
"""

import sys
import os
import json
import time
import socket
import threading
import argparse
import traceback
from datetime import datetime

# ============================================================
# Test Registry
# ============================================================
TESTS = {}          # case_id -> test_function
CURRENT_TEST = {"case": None, "running": False, "stop": False}
STATE = {"state": "IDLE", "current_case": None}

def register_test(case_id, desc=""):
    def decorator(func):
        TESTS[case_id] = {"func": func, "desc": desc}
        return func
    return decorator


# ============================================================
# Test Cases - replace with real DUT checks
# ============================================================
def _run_cmd(cmd, timeout=30):
    """Run a shell command, return (exit_code, stdout)."""
    import subprocess
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip()
    except subprocess.TimeoutExpired:
        return -1, "TIMEOUT"
    except Exception as e:
        return -1, str(e)


def _sim_step(progress_cb, steps=5, delay=0.3):
    """Helper: simulate progress steps, check stop flag."""
    for i in range(1, steps + 1):
        if CURRENT_TEST["stop"]:
            return False, "0xFFFF"
        progress_cb(int(i * 100 / steps), f"step {i}/{steps}...")
        time.sleep(delay)
    return True, "0x0000"


# ---- MBIST ----
@register_test("MBISR_CCD_SOC_HN", "CCD SOC/HN-F BISR")
def test_mbisr_ccd(progress_cb):
    progress_cb(50, "running BISR...")
    time.sleep(0.3)
    return True, "0x0000"

@register_test("MBIST_CCD_SOC_HN", "CCD SOC/HN-F BIST")
def test_mbist_ccd(progress_cb):
    progress_cb(50, "running BIST pattern...")
    time.sleep(0.3)
    return True, "0x0000"

@register_test("MBISR_N3", "N3 core BISR")
def test_mbisr_n3(progress_cb):
    progress_cb(50, "N3 BISR...")
    time.sleep(0.3)
    return True, "0x0000"

@register_test("MBIST_N3", "N3 core BIST")
def test_mbist_n3(progress_cb):
    progress_cb(50, "N3 BIST...")
    time.sleep(0.3)
    return True, "0x0000"

@register_test("MBISR_PCD", "PCD BISR")
def test_mbisr_pcd(progress_cb):
    progress_cb(50, "PCD BISR...")
    time.sleep(0.3)
    return True, "0x0000"

@register_test("MBIST_PCD", "PCD BIST")
def test_mbist_pcd(progress_cb):
    progress_cb(50, "PCD BIST...")
    time.sleep(0.3)
    return True, "0x0000"


# ---- Firmware Boot ----
@register_test("FW_RSS", "RSS firmware boot")
def test_fw_rss(progress_cb):
    progress_cb(50, "checking RSS boot...")
    time.sleep(0.3)
    return True, "0x0000"

@register_test("FW_SCP", "SCP firmware boot")
def test_fw_scp(progress_cb):
    progress_cb(50, "checking SCP boot...")
    time.sleep(0.3)
    return True, "0x0000"

@register_test("FW_MCP", "MCP firmware boot")
def test_fw_mcp(progress_cb):
    progress_cb(50, "checking MCP boot...")
    time.sleep(0.3)
    return True, "0x0000"

@register_test("FW_BBL14", "bbl14 boot")
def test_fw_bbl14(progress_cb):
    progress_cb(50, "checking bbl14...")
    time.sleep(0.3)
    return True, "0x0000"

@register_test("FW_BL31", "bl31 boot")
def test_fw_bl31(progress_cb):
    progress_cb(50, "checking bl31...")
    time.sleep(0.3)
    return True, "0x0000"

@register_test("FW_UEFI", "UEFI boot")
def test_fw_uefi(progress_cb):
    progress_cb(50, "checking UEFI...")
    time.sleep(0.3)
    return True, "0x0000"

@register_test("FW_SECURE", "secure-firmware boot")
def test_fw_secure(progress_cb):
    progress_cb(50, "checking secure firmware...")
    time.sleep(0.3)
    return True, "0x0000"

@register_test("FW_LINUX", "Linux boot")
def test_fw_linux(progress_cb):
    progress_cb(30, "checking kernel...")
    rc, out = _run_cmd("uname -r")
    progress_cb(60, f"kernel: {out}")
    time.sleep(0.3)
    rc, out = _run_cmd("dmesg | grep -i 'error' | head -5")
    if rc == 0 and out:
        return False, "0x1001"
    progress_cb(100, "Linux boot OK")
    return True, "0x0000"


# ---- Low-speed IO ----
@register_test("IO_MHU", "MHU data send/recv")
def test_io_mhu(progress_cb):
    return _sim_step(progress_cb)

@register_test("IO_UART", "UART log output")
def test_io_uart(progress_cb):
    return _sim_step(progress_cb)

@register_test("IO_I2C", "I2C / IPMI SSIF")
def test_io_i2c(progress_cb):
    return _sim_step(progress_cb)

@register_test("IO_I3C", "I3C read/write")
def test_io_i3c(progress_cb):
    return _sim_step(progress_cb)

@register_test("IO_ESPI", "eSPI 1/2/4 wire")
def test_io_espi(progress_cb):
    return _sim_step(progress_cb)

@register_test("IO_GPIO", "GPIO power control")
def test_io_gpio(progress_cb):
    return _sim_step(progress_cb)


# ---- DDR ----
@register_test("DDR_BENCH", "DDR performance benchmark")
def test_ddr_bench(progress_cb):
    return _sim_step(progress_cb, steps=8, delay=0.2)

@register_test("DDR_STRESS", "DDR multi-task stress")
def test_ddr_stress(progress_cb):
    return _sim_step(progress_cb, steps=10, delay=0.2)

@register_test("DDR_EYE", "DDR eye/ber test")
def test_ddr_eye(progress_cb):
    return _sim_step(progress_cb)

@register_test("DDR_ECC", "DDR ECC test")
def test_ddr_ecc(progress_cb):
    return _sim_step(progress_cb)

@register_test("DDR_PWR", "DDR power monitoring")
def test_ddr_pwr(progress_cb):
    return _sim_step(progress_cb)

@register_test("DDR_RESET", "DDR reset/reboot")
def test_ddr_reset(progress_cb):
    return _sim_step(progress_cb)

@register_test("DDR_CROSS", "DDR cross-subsystem")
def test_ddr_cross(progress_cb):
    return _sim_step(progress_cb)

@register_test("DDR_TIMING", "DDR timing verification")
def test_ddr_timing(progress_cb):
    return _sim_step(progress_cb)

@register_test("DDR_BURNIN", "DDR burn-in")
def test_ddr_burnin(progress_cb):
    return _sim_step(progress_cb, steps=10, delay=0.2)

@register_test("DDR_TRAIN", "DDR re-training")
def test_ddr_train(progress_cb):
    return _sim_step(progress_cb)

@register_test("DDR_DIMM", "DIMM compatibility")
def test_ddr_dimm(progress_cb):
    return _sim_step(progress_cb)

@register_test("DDR_VOLT", "DDR voltage margin")
def test_ddr_volt(progress_cb):
    return _sim_step(progress_cb)


# ---- PCIe ----
@register_test("PCIE_LINK", "PCIe link training")
def test_pcie_link(progress_cb):
    return _sim_step(progress_cb)

@register_test("PCIE_BW", "PCIe bandwidth throughput")
def test_pcie_bw(progress_cb):
    return _sim_step(progress_cb, steps=8, delay=0.2)

@register_test("PCIE_STRESS", "PCIe long-duration stress")
def test_pcie_stress(progress_cb):
    return _sim_step(progress_cb, steps=10, delay=0.2)

@register_test("PCIE_AER", "PCIe AER error handling")
def test_pcie_aer(progress_cb):
    return _sim_step(progress_cb)

@register_test("PCIE_INTR", "PCIe INTx/MSI/MSI-X")
def test_pcie_intr(progress_cb):
    return _sim_step(progress_cb)

@register_test("PCIE_ASPM", "PCIe ASPM power mgmt")
def test_pcie_aspm(progress_cb):
    return _sim_step(progress_cb)

@register_test("PCIE_HOTPLUG", "PCIe hotplug")
def test_pcie_hotplug(progress_cb):
    return _sim_step(progress_cb)

@register_test("PCIE_CFG", "PCIe config space")
def test_pcie_cfg(progress_cb):
    return _sim_step(progress_cb)


# ---- Interrupt ----
@register_test("IRQ_PPI", "PPI interrupt")
def test_irq_ppi(progress_cb):
    return _sim_step(progress_cb)

@register_test("IRQ_SGI", "SGI interrupt")
def test_irq_sgi(progress_cb):
    return _sim_step(progress_cb)

@register_test("IRQ_SPI", "SPI interrupt")
def test_irq_spi(progress_cb):
    return _sim_step(progress_cb)

@register_test("IRQ_LPI", "LPI interrupt")
def test_irq_lpi(progress_cb):
    return _sim_step(progress_cb)

@register_test("IRQ_GIC_C2C", "GIC cross-die")
def test_irq_gic_c2c(progress_cb):
    return _sim_step(progress_cb)

@register_test("IRQ_GIC_S2S", "GIC cross-socket")
def test_irq_gic_s2s(progress_cb):
    return _sim_step(progress_cb)

@register_test("IRQ_VSGI", "vSGI interrupt")
def test_irq_vsgi(progress_cb):
    return _sim_step(progress_cb)

@register_test("IRQ_VLPI", "vLPI interrupt")
def test_irq_vlpi(progress_cb):
    return _sim_step(progress_cb)


# ---- RAS ----
@register_test("RAS_CMN", "CMN RAS")
def test_ras_cmn(progress_cb):
    return _sim_step(progress_cb)

@register_test("RAS_GIC", "GIC RAS")
def test_ras_gic(progress_cb):
    return _sim_step(progress_cb)

@register_test("RAS_CORE", "CORE RAS")
def test_ras_core(progress_cb):
    return _sim_step(progress_cb)

@register_test("RAS_PCIE", "PCIe/CXL RAS")
def test_ras_pcie(progress_cb):
    return _sim_step(progress_cb)

@register_test("RAS_UCIE", "UCIe RAS")
def test_ras_ucie(progress_cb):
    return _sim_step(progress_cb)

@register_test("RAS_DDR", "DDR RAS")
def test_ras_ddr(progress_cb):
    return _sim_step(progress_cb)

@register_test("RAS_SMMU", "SMMU RAS")
def test_ras_smmu(progress_cb):
    return _sim_step(progress_cb)


# ---- Security Runtime ----
@register_test("SEC_RUNTIME", "Security Runtime")
def test_sec_runtime(progress_cb):
    progress_cb(50, "checking security firmware...")
    time.sleep(0.5)
    return True, "0x0000"


# ---- Mixed Stability ----
@register_test("STAB_X265", "x265 video encode")
def test_stab_x265(progress_cb):
    return _sim_step(progress_cb, steps=8, delay=0.2)

@register_test("STAB_MYSQL", "MySQL stress")
def test_stab_mysql(progress_cb):
    return _sim_step(progress_cb, steps=8, delay=0.2)

@register_test("STAB_SPEC", "SpecCPU2017")
def test_stab_spec(progress_cb):
    return _sim_step(progress_cb, steps=10, delay=0.2)

@register_test("STAB_MEM", "Memory stress")
def test_stab_mem(progress_cb):
    return _sim_step(progress_cb, steps=8, delay=0.2)

@register_test("STAB_CPU", "CPU stress")
def test_stab_cpu(progress_cb):
    return _sim_step(progress_cb, steps=8, delay=0.2)

@register_test("STAB_NVME", "NVMe stress")
def test_stab_nvme(progress_cb):
    return _sim_step(progress_cb, steps=8, delay=0.2)

@register_test("STAB_MIXED", "Mixed scenario")
def test_stab_mixed(progress_cb):
    return _sim_step(progress_cb, steps=10, delay=0.2)


# ---- Power & Thermal ----
@register_test("POWER_THERMAL", "Power & Thermal")
def test_power_thermal(progress_cb):
    progress_cb(30, "reading temperature...")
    rc, out = _run_cmd("cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null || echo 'N/A'")
    progress_cb(60, f"temp: {out}")
    time.sleep(0.3)
    progress_cb(100, "power/thermal OK")
    return True, "0x0000"


# ============================================================
# TCP Server
# ============================================================
class SLTBoardDaemon:
    def __init__(self, host="0.0.0.0", port=5001):
        self.host = host
        self.port = port
        self.server_sock = None
        self.client_sock = None
        self.running = False
        self.fw_state = {}   # 固件接收状态

    def log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {msg}", flush=True)

    def send_json(self, obj):
        if not self.client_sock:
            return
        try:
            data = (json.dumps(obj) + "\n").encode("utf-8")
            self.client_sock.sendall(data)
        except Exception as e:
            self.log(f"send error: {e}")

    def progress_cb(self, pct, msg=""):
        case = CURRENT_TEST["case"]
        self.send_json({"type": "TEST_PROGRESS", "case": case, "pct": pct, "msg": msg})

    def _execute_case(self, case_id):
        """执行单个用例（供单条 TEST_START 与批量 TEST_RUN_ALL 复用）。
        返回 (ok, err, aborted)，aborted 表示因 STOP 中止。"""
        CURRENT_TEST["case"] = case_id
        CURRENT_TEST["running"] = True
        CURRENT_TEST["stop"] = False
        STATE["state"] = "RUNNING"
        STATE["current_case"] = case_id

        self.send_json({"type": "TEST_STARTED", "case": case_id})
        self.log(f"START {case_id}")

        t0 = time.time()
        try:
            func = TESTS[case_id]["func"]
            ok, err = func(self.progress_cb)
        except Exception as e:
            self.log(f"EXCEPTION: {traceback.format_exc()}")
            ok, err = False, "0xFFFF"
        duration = round(time.time() - t0, 2)

        aborted = bool(CURRENT_TEST["stop"])
        result = "ABORT" if aborted else ("PASS" if ok else "FAIL")
        self.send_json({
            "type": "TEST_DONE", "case": case_id,
            "result": result, "err": err, "duration_s": duration
        })
        self.log(f"DONE  {case_id} -> {result} ({err}) {duration}s")

        CURRENT_TEST["running"] = False
        CURRENT_TEST["case"] = None
        STATE["state"] = "IDLE"
        STATE["current_case"] = None
        return ok, err, aborted

    def run_test(self, case_id):
        """执行单个用例（兼容单条 TEST_START 协议）。"""
        if case_id not in TESTS:
            self.send_json({"type": "ERROR", "msg": f"unknown case: {case_id}"})
            return
        self._execute_case(case_id)

    def run_batch(self, cases):
        """批量执行整个用例列表：上位机一次性下发后，本地排队跑到底，
        即使上位机崩溃断连也继续执行剩余用例。全部完成发 TEST_BATCH_DONE。"""
        passed = failed = abort = 0
        for case in cases:
            if CURRENT_TEST["stop"]:
                abort += 1
                continue
            if case not in TESTS:
                self.send_json({"type": "ERROR", "msg": f"unknown case: {case}"})
                failed += 1
                continue
            ok, err, aborted = self._execute_case(case)
            if aborted:
                abort += 1
            elif ok:
                passed += 1
            else:
                failed += 1
        self.send_json({"type": "TEST_BATCH_DONE", "pass": passed,
                        "fail": failed, "abort": abort})
        self.log(f"BATCH_DONE pass={passed} fail={failed} abort={abort}")

    def handle_cmd(self, cmd):
        """Parse and handle one JSON command."""
        ctype = cmd.get("type", "")

        if ctype == "PING":
            self.send_json({"type": "PONG", "version": "1.0.0",
                            "uptime_s": int(time.time() - self.boot_time)})

        elif ctype == "TEST_LIST":
            self.send_json({"type": "TEST_LIST_RSP", "cases": list(TESTS.keys())})

        elif ctype == "TEST_START":
            case = cmd.get("case", "")
            if CURRENT_TEST["running"]:
                self.send_json({"type": "ERROR", "msg": f"busy, running {CURRENT_TEST['case']}"})
                return
            threading.Thread(target=self.run_test, args=(case,), daemon=True).start()

        elif ctype == "TEST_RUN_ALL":
            cases = cmd.get("cases", [])
            if not cases:
                self.send_json({"type": "ERROR", "msg": "no cases given"})
                return
            if CURRENT_TEST["running"]:
                self.send_json({"type": "ERROR", "msg": f"busy, running {CURRENT_TEST['case']}"})
                return
            CURRENT_TEST["stop"] = False
            threading.Thread(target=self.run_batch, args=(cases,), daemon=True).start()

        elif ctype == "TEST_STOP":
            if CURRENT_TEST["running"]:
                CURRENT_TEST["stop"] = True
                self.send_json({"type": "TEST_STOPPED", "case": CURRENT_TEST["case"]})

        elif ctype == "GET_STATUS":
            self.send_json({"type": "STATUS_RSP",
                            "state": STATE["state"],
                            "current_case": STATE["current_case"]})

        # ---- 固件烧录 / 升级 ----
        elif ctype == "FW_BEGIN":
            ftype = cmd.get("file_type", "fw")
            size = cmd.get("size", 0)
            sha = cmd.get("sha256", "")
            ver = cmd.get("version", "")
            self.fw_state = {"type": ftype, "size": size, "sha": sha, "buf": bytearray()}
            self.log(f"FW_BEGIN {ftype} ver={ver} size={size}")
            self.send_json({"type": "FW_READY"})

        elif ctype == "FW_CHUNK":
            buf = self.fw_state.get("buf")
            if buf is None:
                self.send_json({"type": "FW_ERROR", "msg": "no fw session"})
                return
            try:
                import base64
                data = base64.b64decode(cmd.get("data", ""))
            except Exception as e:
                self.send_json({"type": "FW_ERROR", "msg": f"bad chunk: {e}"})
                return
            offset = cmd.get("offset", 0)
            if len(buf) < offset + len(data):
                buf.extend(b"\x00" * (offset + len(data) - len(buf)))
            buf[offset:offset + len(data)] = data
            self.send_json({"type": "FW_CHUNK_OK", "offset": offset + len(data)})

        elif ctype == "FW_END":
            buf = self.fw_state.get("buf", bytearray())
            actual = bytes(buf)
            expect = self.fw_state.get("size", len(actual))
            ok = (len(actual) == expect)
            path = f"/tmp/slt_fw_{self.fw_state.get('type', 'fw')}.bin"
            err = ""
            if ok:
                try:
                    with open(path, "wb") as f:
                        f.write(actual)
                    self.log(f"FW_DONE {path} size={len(actual)}")
                except Exception as e:
                    ok = False
                    err = str(e)
            self.send_json({"type": "FW_DONE", "ok": ok, "size": len(actual),
                            "path": path if ok else "", "err": err})
            self.fw_state = {}
        else:
            self.send_json({"type": "ERROR", "msg": f"unknown cmd: {ctype}"})

    def serve(self):
        self.boot_time = time.time()
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_sock.bind((self.host, self.port))
        self.server_sock.listen(1)
        self.running = True
        self.log(f"SLT Board Daemon listening on {self.host}:{self.port}")
        self.log(f"Registered {len(TESTS)} test cases: {list(TESTS.keys())}")

        while self.running:
            try:
                self.client_sock, addr = self.server_sock.accept()
                self.log(f"Connected from {addr}")
                buf = ""
                while self.running:
                    data = self.client_sock.recv(4096)
                    if not data:
                        break
                    buf += data.decode("utf-8")
                    while "\n" in buf:
                        line, buf = buf.split("\n", 1)
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            cmd = json.loads(line)
                            self.handle_cmd(cmd)
                        except json.JSONDecodeError as e:
                            self.send_json({"type": "ERROR", "msg": f"bad json: {e}"})
                self.log("Client disconnected")
                self.client_sock = None
            except Exception as e:
                if self.running:
                    self.log(f"accept error: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5001)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()
    daemon = SLTBoardDaemon(args.host, args.port)
    daemon.serve()


if __name__ == "__main__":
    main()
