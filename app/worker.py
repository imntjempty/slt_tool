# -*- coding: utf-8 -*-
"""
测试执行线程（每台机台一个）。
在 QThread 中异步执行选中用例，通过信号回传进度/结果。
- 仿真 / 串口：逐条执行
- TCP 实机：一次性下发整套用例（TEST_RUN_ALL），下位机本地排队跑到底
"""
import random
import threading
import time

from PyQt5.QtCore import QThread, pyqtSignal

from .comm import CommChannel


class TestWorker(QThread):
    log_signal = pyqtSignal(str, str)                    # (msg, level)
    progress_signal = pyqtSignal(int, int)               # (current, total)
    case_start_signal = pyqtSignal(str)                  # (case_id)
    case_result_signal = pyqtSignal(str, bool, str, int)  # (case_id, ok, err, loop)
    finished_signal = pyqtSignal(dict)                   # summary

    def __init__(self, selected_cases, board, sim_mode=True, loops=1, parent=None):
        super().__init__(parent)
        self.selected_cases = selected_cases
        self.board = board
        self.sim_mode = sim_mode
        self.loops = loops
        self._stop = False
        self._pause = threading.Event()

    def stop(self):
        self._stop = True

    def pause(self):
        self._pause.set()

    def resume(self):
        self._pause.clear()

    def _wait_if_paused(self):
        while self._pause.is_set() and not self._stop:
            time.sleep(0.2)

    def run(self):
        total = len(self.selected_cases)
        passed = failed = aborted = 0
        self.log_signal.emit("=" * 50, "info")
        self.log_signal.emit(
            f"开始测试 | 用例数={total} | 循环={self.loops} | "
            f"{'仿真' if self.sim_mode else '实机'}", "info")
        self.log_signal.emit("=" * 50, "info")

        is_tcp = (not self.sim_mode) and (self.board.mode == CommChannel.MODE_TCP)

        for loop in range(1, self.loops + 1):
            if self._stop:
                aborted += total - (passed + failed)
                self.log_signal.emit("*** 已中止 ***", "warn")
                break
            if self.loops > 1:
                self.log_signal.emit(f"--- 第 {loop}/{self.loops} 轮 ---", "info")

            if is_tcp:
                # TCP 实机：一次性下发整套，下位机本地排队执行
                self.log_signal.emit(f"[Chip{loop}] 下发整套 {total} 项测试 ...", "info")
                p, f, a = self.board.run_batch_tcp(
                    [c[0] for c in self.selected_cases],
                    progress_cb=lambda pct, msg: (self.log_signal.emit(
                        f"    [{pct}%] {msg}", "info") if msg else None),
                    case_cb=self._make_case_cb(loop),
                    stop_check=lambda: self._stop,
                    pause_check=lambda: self._pause.is_set() and not self._stop,
                )
                passed += p
                failed += f
                aborted += a
            else:
                # 仿真 / 串口：逐条执行
                for idx, (cid, desc, _opt) in enumerate(self.selected_cases, 1):
                    if self._stop:
                        aborted += total - (passed + failed)
                        self.log_signal.emit("*** 已中止 ***", "warn")
                        break
                    self._wait_if_paused()
                    if self._stop:
                        aborted += total - (passed + failed)
                        self.log_signal.emit("*** 已中止 ***", "warn")
                        break
                    self.progress_signal.emit(idx, total)
                    self.case_start_signal.emit(cid)
                    self.log_signal.emit(f"[Chip{loop}][{idx}/{total}] {desc} ...", "info")
                    ok, err = self._run_one(cid)
                    if self._stop:
                        aborted += 1
                        self.case_result_signal.emit(cid, False, "ABORTED", loop)
                        break
                    if ok:
                        passed += 1
                        self.log_signal.emit("  -> 通过 (0x0000)", "ok")
                        self.case_result_signal.emit(cid, True, "0x0000", loop)
                    else:
                        failed += 1
                        self.log_signal.emit(f"  -> 失败 ({err})", "error")
                        self.case_result_signal.emit(cid, False, err, loop)
            if self._stop:
                break

        summary = {"pass": passed, "fail": failed, "abort": aborted,
                   "total": total * self.loops}
        self.log_signal.emit(f"汇总: 通过={passed} 失败={failed} 中止={aborted}",
                             "ok" if failed == 0 else "warn")
        self.finished_signal.emit(summary)

    def _make_case_cb(self, loop):
        """TCP 批量模式下每个用例完成后的回调。统计由 run_batch_tcp 返回。"""
        def cb(cid, ok, err, aborted):
            self.case_result_signal.emit(cid, ok, err, loop)
        return cb

    def _run_one(self, cid):
        """仿真 / 串口逐条执行单个用例。"""
        if self.sim_mode:
            time.sleep(random.uniform(0.2, 0.8))
            if random.random() < 0.85:
                return True, "0x0000"
            return False, f"0x{random.randint(0x1000, 0xFFFF):04X}"
        # serial 文本协议
        resp = self.board.send_cmd(f"TEST {cid}", timeout=10)
        if "PASS" in resp.upper():
            return True, "0x0000"
        parts = resp.split()
        return False, parts[-1] if len(parts) > 1 else "0xFFFF"
