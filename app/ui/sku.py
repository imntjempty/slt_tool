# -*- coding: utf-8 -*-
"""
SKU 统计 Tab：加载 sku.ui，按 SKU 聚合各机台芯片 BIN 统计。
"""
import os

from PyQt5.QtWidgets import QWidget, QTableWidgetItem
from PyQt5.QtGui import QColor

from ..i18n import T
from .. import config as _cfg

UI_PATH = os.path.join(_cfg.get_ui_dir(), "sku.ui")


class SkuTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._load_ui()
        self._init_table()

    def _load_ui(self):
        from PyQt5 import uic
        uic.loadUi(UI_PATH, self)

    def _init_table(self):
        self.tbl_sku.setHorizontalHeaderLabels([
            "SKU", T("芯片总数", "Chips"), T("BIN0 良品", "BIN0 Good"),
            T("BIN1 不良", "BIN1 Bad"), T("BIN2 中止", "BIN2 Abort"),
            T("良率", "Yield"),
        ])
        h = self.tbl_sku.horizontalHeader()
        h.setSectionResizeMode(h.Stretch)
        self.tbl_sku.verticalHeader().setVisible(False)
        self.tbl_sku.setSelectionMode(self.tbl_sku.NoSelection)

    def refresh(self, stations):
        """聚合所有机台，按 SKU 汇总。stations: {name: StationPanel}"""
        agg = {}
        for name, sp in stations.items():
            sku = (sp.cmb_sku.currentText() or "").strip() or "N/A"
            d = agg.setdefault(sku, {"chips": 0, "bin0": 0, "bin1": 0, "bin2": 0})
            d["chips"] += sp.chip_bin["total"]
            d["bin0"] += sp.chip_bin["bin0"]
            d["bin1"] += sp.chip_bin["bin1"]
            d["bin2"] += sp.chip_bin["bin2"]
        self.tbl_sku.setRowCount(0)
        for sku in sorted(agg.keys()):
            d = agg[sku]
            r = self.tbl_sku.rowCount()
            self.tbl_sku.insertRow(r)
            self.tbl_sku.setItem(r, 0, QTableWidgetItem(sku))
            self.tbl_sku.setItem(r, 1, QTableWidgetItem(str(d["chips"])))
            b0 = QTableWidgetItem(str(d["bin0"]))
            b0.setForeground(QColor("#27ae60"))
            self.tbl_sku.setItem(r, 2, b0)
            b1 = QTableWidgetItem(str(d["bin1"]))
            b1.setForeground(QColor("#e74c3c"))
            self.tbl_sku.setItem(r, 3, b1)
            b2 = QTableWidgetItem(str(d["bin2"]))
            b2.setForeground(QColor("#f39c12"))
            self.tbl_sku.setItem(r, 4, b2)
            if d["chips"] > 0:
                self.tbl_sku.setItem(r, 5, QTableWidgetItem(f"{d['bin0'] / d['chips'] * 100:.1f}%"))
            else:
                self.tbl_sku.setItem(r, 5, QTableWidgetItem("--"))
