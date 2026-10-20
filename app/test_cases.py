# -*- coding: utf-8 -*-
"""
测试用例定义（树形分组）。
每条: (id, 描述, is_group)
  - is_group=True 表示这是一个父分组，后续子项属于它
  - is_group=False 表示叶子测试项
MBIST 为必测项。
"""

TEST_CASES = [
    # MBIST（必测）
    ("MBIST_GROUP",       "MBIST 内存自检",                           True),
    ("MBISR_CCD_SOC_HN", "  CCD SOC/HN-F BISR",                      False),
    ("MBIST_CCD_SOC_HN", "  CCD SOC/HN-F BIST",                       False),
    ("MBISR_N3",         "  N3 core BISR",                            False),
    ("MBIST_N3",         "  N3 core BIST",                            False),
    ("MBISR_PCD",        "  PCD BISR",                                False),
    ("MBIST_PCD",        "  PCD BIST",                                False),

    # Firmware Boot
    ("FW_BOOT_GROUP",     "Firmware Boot / 固件启动",                  True),
    ("FW_RSS",           "  RSS 固件启动",                            False),
    ("FW_SCP",           "  SCP 固件启动",                            False),
    ("FW_MCP",           "  MCP 固件启动",                            False),
    ("FW_BBL14",         "  bbl14 固件启动",                          False),
    ("FW_BL31",          "  bl31 固件启动",                           False),
    ("FW_UEFI",          "  UEFI 固件启动",                           False),
    ("FW_SECURE",        "  secure-firmware 启动",                     False),
    ("FW_LINUX",         "  Linux 系统启动",                          False),

    # Low-speed IO
    ("LOW_IO_GROUP",      "Low-speed IO / 低速IO",                     True),
    ("IO_MHU",           "  MHU 数据收发",                            False),
    ("IO_UART",          "  UART 日志输出",                           False),
    ("IO_I2C",           "  I2C / IPMI SSIF",                         False),
    ("IO_I3C",           "  I3C 读写",                               False),
    ("IO_ESPI",          "  eSPI 1/2/4线",                            False),
    ("IO_GPIO",          "  GPIO 开关机控制",                          False),

    # DDR
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

    # PCIe
    ("PCIE_GROUP",        "PCIe Test",                                True),
    ("PCIE_LINK",        "  链路训练与状态稳定性",                    False),
    ("PCIE_BW",          "  吞吐量与带宽压力",                        False),
    ("PCIE_STRESS",      "  长时间稳定性老化",                        False),
    ("PCIE_AER",         "  AER错误处理与容错",                       False),
    ("PCIE_INTR",        "  INTx/MSI/MSI-X压力",                     False),
    ("PCIE_ASPM",        "  ASPM电源管理与低功耗",                    False),
    ("PCIE_HOTPLUG",     "  热插拔与链路重训练",                      False),
    ("PCIE_CFG",         "  寄存器配置与兼容性",                       False),

    # Interrupt
    ("IRQ_GROUP",         "Interrupt / 中断",                          True),
    ("IRQ_PPI",          "  PPI 中断",                               False),
    ("IRQ_SGI",          "  SGI 中断",                               False),
    ("IRQ_SPI",          "  SPI 中断",                               False),
    ("IRQ_LPI",          "  LPI 中断",                               False),
    ("IRQ_GIC_C2C",      "  GIC 跨die中断",                          False),
    ("IRQ_GIC_S2S",      "  GIC 跨socket中断",                       False),
    ("IRQ_VSGI",         "  vSGI 中断",                              False),
    ("IRQ_VLPI",         "  vLPI 中断",                              False),

    # RAS
    ("RAS_GROUP",         "RAS-Extension",                            True),
    ("RAS_CMN",          "  CMN RAS",                                False),
    ("RAS_GIC",          "  GIC RAS",                                False),
    ("RAS_CORE",         "  CORE RAS",                               False),
    ("RAS_PCIE",         "  PCIe/CXL RAS",                           False),
    ("RAS_UCIE",         "  UCIe RAS",                               False),
    ("RAS_DDR",          "  DDR RAS",                                False),
    ("RAS_SMMU",         "  SMMU RAS",                               False),

    # Security Runtime
    ("SEC_RUNTIME",       "Security Runtime",                          False),

    # Mixed Stability
    ("STAB_GROUP",        "Mixed Stability / 混合稳定性",              True),
    ("STAB_X265",        "  x265 视频编码",                           False),
    ("STAB_MYSQL",       "  MySQL 高并发",                            False),
    ("STAB_SPEC",        "  SpecCPU2017",                            False),
    ("STAB_MEM",         "  内存压测",                               False),
    ("STAB_CPU",         "  CPU 压测",                               False),
    ("STAB_NVME",        "  NVMe 压测",                              False),
    ("STAB_MIXED",       "  混合场景压测",                            False),

    # Power & Thermal
    ("POWER_THERMAL",     "Power & Thermal / 功耗热管理",              False),
]

# 分组 ID 集合
GROUP_IDS = {c[0] for c in TEST_CASES if c[2]}
# 叶子（可执行）ID 集合
CASE_IDS = {c[0] for c in TEST_CASES if not c[2]}
# ID -> 描述 映射
DESC_MAP = {c[0]: c[1] for c in TEST_CASES}
