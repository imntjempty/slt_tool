# -*- coding: utf-8 -*-
"""离屏冒烟测试：验证 .ui 加载、控件存在、测试流程、总览更新。"""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

app = QApplication([])
from app.ui.main_window import MainWindow
from app.ui.conn_panel import ConnPanel
from app.ui.station_panel import StationPanel

win = MainWindow()
win.show()

# 1. 控件加载检查
required_main = ["btn_all_start", "btn_all_pause", "btn_all_resume", "btn_all_stop",
                 "cmb_lang", "tabs", "txt_log", "splitter_v"]
for name in required_main:
    assert hasattr(win, name), f"主窗口缺控件 {name}"
print("[OK] 主窗口控件齐全")

# 1a. 全部机台未连接时弹窗提示
from PyQt5.QtWidgets import QMessageBox as _QMB
_warned = []
_orig_warning = _QMB.warning
_QMB.warning = lambda *a, **k: _warned.append(k)
for _nm, _sp in win.stations.items():
    _sp.p_board.channel.connected = False
win._start_all()
_QMB.warning = _orig_warning
assert len(_warned) == 1, f"全部未连接应弹窗, 实际 {len(_warned)}"
print("[OK] 全部机台未连接弹窗提示 正常")

# 1b. 总览全局统计控件
dash = win.dashboard
for name in ["grp_global", "val_g_chips", "val_g_bin0", "val_g_bin1", "val_g_bin2", "val_g_yield"]:
    assert hasattr(dash, name), f"总览缺控件 {name}"
print("[OK] 总览全局统计控件齐全")

# 1c. 固件 / SKU Tab 控件
assert hasattr(win, "firmware") and hasattr(win, "sku_tab"), "缺固件/SKU Tab"
fw = win.firmware
for name in ["list_stations", "cmb_fw_type", "le_fw_path", "btn_browse",
             "btn_fw_start", "btn_fw_stop", "progress_fw", "txt_fw_log"]:
    assert hasattr(fw, name), f"固件Tab缺控件 {name}"
print("[OK] 固件Tab控件齐全")
sku = win.sku_tab
assert hasattr(sku, "tbl_sku"), "SKU Tab缺控件"
for nm in win.stations:
    assert hasattr(win.stations[nm], "cmb_sku"), f"{nm} 缺 cmb_sku"
print("[OK] SKU Tab控件齐全 + 机台 SKU 下拉齐全")

# 1e. 固件 Tab 机台复选框选中 + 版本识别
from PyQt5.QtCore import Qt as _Qt
assert fw.list_stations.count() >= 6, "固件机台列表项数错误"
it0 = fw.list_stations.item(0)
assert it0.flags() & _Qt.ItemIsUserCheckable, "机台项应可勾选"
it0.setCheckState(_Qt.Checked)
assert fw._get_selected() == ["机台 1"], fw._get_selected()
assert fw._detect_version("/x/boot_v1.2.3.bin") == "1.2.3", fw._detect_version("/x/boot_v1.2.3.bin")
assert hasattr(fw, "le_fw_ver"), "缺固件版本输入框"
print("[OK] 固件Tab 复选框选中 + 版本识别 正常")

# 1f. 固件 Tab 连接接口选择 + 连接状态
for name in ["cmb_fw_conn_mode", "le_fw_ip", "sp_fw_port", "btn_fw_conn",
             "lbl_fw_conn_status"]:
    assert hasattr(fw, name), f"固件连接缺控件 {name}"
assert fw.cmb_fw_conn_mode.currentText() == "仿真"
assert "仿真" in fw.lbl_fw_conn_status.text(), fw.lbl_fw_conn_status.text()
# 临时起一个下位机 daemon，验证 TCP 连接状态
from slt_board_daemon import SLTBoardDaemon
import threading as _th
import time as _t
_d = SLTBoardDaemon("127.0.0.1", 5010)
_th.Thread(target=_d.serve, daemon=True).start()
_t.sleep(0.3)
fw.list_stations.item(0).setCheckState(_Qt.Unchecked)   # 取消机台1
fw.list_stations.item(5).setCheckState(_Qt.Checked)     # 机台6
fw.sp_fw_port.setValue(5010)
fw.cmb_fw_conn_mode.setCurrentIndex(1)
assert not fw.le_fw_ip.isHidden(), "TCP 模式应显示 IP"
fw._toggle_conn()
assert fw.fw_channels["机台 6"].connected, "机台6 应已连接"
assert "已连接" in fw.lbl_fw_conn_status.text(), fw.lbl_fw_conn_status.text()
print(f"[OK] 固件连接接口选择 + 连接状态: {fw.lbl_fw_conn_status.text()}")

# 1d. SKU 聚合逻辑
win.stations["机台 1"].cmb_sku.setCurrentText("SKU-A")
win.stations["机台 2"].cmb_sku.setCurrentText("SKU-A")
win.stations["机台 1"].chip_bin = {"total": 4, "bin0": 3, "bin1": 1, "bin2": 0}
win.stations["机台 2"].chip_bin = {"total": 6, "bin0": 5, "bin1": 1, "bin2": 0}
sku.refresh(win.stations)
assert sku.tbl_sku.rowCount() >= 1
row_sku = sku.tbl_sku.item(0, 0).text()
print(f"[OK] SKU 聚合: 首行 SKU={row_sku} 芯片={sku.tbl_sku.item(0,1).text()} "
      f"BIN0={sku.tbl_sku.item(0,2).text()} 良率={sku.tbl_sku.item(0,5).text()}")

st = win.stations["机台 1"]
required_st = ["p_handler", "p_board", "tree_cases", "tbl_results",
               "btn_start", "btn_pause", "btn_resume", "btn_stop",
               "spin_loop", "progress_bar", "bin_lbl_pass", "bin_lbl_fail", "bin_lbl_abort"]
for name in required_st:
    assert hasattr(st, name), f"机台缺控件 {name}"
print("[OK] 机台面板控件齐全")

# 2. 连接面板控件
cp = ConnPanel("Test")
for name in ["cmb_mode", "cmb_port", "cmb_baud", "le_ip", "spin_tcp_port",
             "btn_connect", "lbl_status", "btn_refresh"]:
    assert hasattr(cp, name), f"连接面板缺控件 {name}"
print("[OK] 连接面板控件齐全")

# 3. 测试用例树应有叶子项
leaf_count = sum(1 for cid in st.case_item_map if cid not in __import__("app.test_cases", fromlist=["GROUP_IDS"]).GROUP_IDS)
print(f"[OK] 测试用例树叶子项数={leaf_count}")

# 4. 仿真模式跑一轮
st.p_board.channel.connect_sim()
st._set_all(True)
st.start_test()
st.worker.wait(20000)
for _ in range(20):
    app.processEvents()
assert "通过" in st.progress_bar.format() or "pass" in st.progress_bar.format(), st.progress_bar.format()
print(f"[OK] 测试结束，结果行数={st.tbl_results.rowCount()}, BIN0={st.bin_lbl_pass.text()}, "
      f"进度格式={st.progress_bar.format()}")

# 5. 总览更新
dash = win.dashboard
row0 = dash.tbl_dash.item(0, 3).text()
print(f"[OK] 总览第一行芯片总数={row0}")

# 5b. 全局 BIN 汇总逻辑（模拟两台机台完成数据）
dash._states[0].update({"chip_total": 10, "chip_bin0": 8, "chip_bin1": 1, "chip_bin2": 1})
dash._states[1].update({"chip_total": 5, "chip_bin0": 4, "chip_bin1": 1, "chip_bin2": 0})
dash._update_global()
assert dash.val_g_chips.text() == "15", f"全局芯片总数={dash.val_g_chips.text()}"
assert dash.val_g_bin0.text() == "12"
assert dash.val_g_bin1.text() == "2"
assert dash.val_g_bin2.text() == "1"
print(f"[OK] 全局 BIN 统计: 芯片={dash.val_g_chips.text()} BIN0={dash.val_g_bin0.text()} "
      f"BIN1={dash.val_g_bin1.text()} BIN2={dash.val_g_bin2.text()} 良率={dash.val_g_yield.text()}")

# 5c. 测试中控件锁定逻辑
st._set_testing_ui(True)
assert not st.spin_loop.isEnabled(), "测试中芯片目标数应禁用"
assert not st.btn_select_all.isEnabled(), "测试中全选应禁用"
assert not st.btn_clear_all.isEnabled(), "测试中清空应禁用"
assert not st.p_board.btn_connect.isEnabled(), "测试中连接按钮应禁用"
first_item = next(iter(st.case_item_map.values()))
assert not (first_item.flags() & Qt.ItemIsUserCheckable), "测试中树勾选应禁用"
st._set_testing_ui(False)
assert st.spin_loop.isEnabled(), "结束后应恢复"
assert st.p_board.btn_connect.isEnabled(), "结束后连接应恢复"
assert (first_item.flags() & Qt.ItemIsUserCheckable), "结束后树勾选应恢复"
print("[OK] 测试中控件锁定/恢复 正常")

# 6. 语言下拉（仅验证控件存在，不真正切换，避免污染 .lang）
print("[OK] 语言下拉存在，当前语言=" + __import__("app.i18n", fromlist=["LANG"]).LANG)

print("=== 全部通过 ===")

# 5d. 全局目标/已完成/待测芯片数
from app.config import NUM_STATIONS as _NS
for i in range(_NS):
    dash._states[i]["target"] = 0
dash._states[0]["target"] = 10
dash._states[1]["target"] = 5
dash._states[0]["chip_total"] = 3
dash._states[1]["chip_total"] = 2
dash._update_global()
assert dash.val_g_target.text() == "15", dash.val_g_target.text()
assert dash.val_g_done.text() == "5", dash.val_g_done.text()
assert dash.val_g_remain.text() == "10", dash.val_g_remain.text()
print(f"[OK] 目标/已完成/待测: 目标={dash.val_g_target.text()} "
      f"已完成={dash.val_g_done.text()} 待测={dash.val_g_remain.text()}")
# set_target 接口：未开始的机台目标不计入全局
dash.set_target(2, 20)
assert dash.val_g_target.text() == "15", f"未开始机台目标不应计入: {dash.val_g_target.text()}"
print("[OK] 未开始机台(机台3)目标不计入全局 正常")
# 该机台开始测试后计入
dash._states[2]["chip_total"] = 1
dash._update_global()
assert dash.val_g_target.text() == "35", dash.val_g_target.text()
print("[OK] 机台开始后目标计入全局 正常")
