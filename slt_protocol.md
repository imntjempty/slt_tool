# SLT 通信协议规范 (TCP/IP)

## 1. 概述

上位机 (PC) 与下位机 (DUT Linux Board) 之间通过 TCP Socket 通信。
- **传输层**：TCP
- **端口**：5001（可配置）
- **编码**：UTF-8
- **帧格式**：NDJSON —— 每条消息是一行 JSON，以 `\n` 结尾

```
上位机 PC  ──── TCP:5001 ────  DUT Linux Board
            JSON line per message
```

## 2. 消息通用格式

每条消息是一个 JSON 对象，必须以 `\n` 结尾：

```json
{"type": "<消息类型>", ...其他字段}
```

## 3. PC → Board 命令

| type | 字段 | 说明 |
|------|------|------|
| `PING` | — | 心跳探测 |
| `TEST_LIST` | — | 查询板卡支持的测试用例列表 |
| `TEST_START` | `case`: string | 启动指定单个测试用例 |
| `TEST_RUN_ALL` | `cases`: [string] | **一次性下发整套用例**，下位机本地排队执行到底 |
| `TEST_STOP` | — | 中止当前正在跑的用例（并停止批量队列） |
| `GET_STATUS` | — | 查询当前板卡状态 |
| `FW_BEGIN` | `file_type`, `size`, `sha256` | 开始固件烧录会话 |
| `FW_CHUNK` | `offset`, `data`(base64) | 发送一块固件数据 |
| `FW_END` | — | 结束烧录并校验固件 |

**示例：**
```json
{"type": "PING"}
{"type": "TEST_START", "case": "DDR_TEST"}
{"type": "TEST_RUN_ALL", "cases": ["FW_BOOT","DDR_TEST","PCIE_TEST"]}
{"type": "TEST_STOP"}
{"type": "GET_STATUS"}
{"type": "FW_BEGIN", "file_type": "kernel", "size": 51200, "sha256": "6ff0b2..."}
{"type": "FW_CHUNK", "offset": 0, "data": "AAAA..."}
{"type": "FW_END"}
```

## 4. Board → PC 响应

| type | 字段 | 说明 |
|------|------|------|
| `PONG` | `version`, `uptime_s` | 心跳响应 |
| `TEST_LIST_RSP` | `cases`: [string] | 支持的用例列表 |
| `TEST_STARTED` | `case` | 开始执行某用例 |
| `TEST_PROGRESS` | `case`, `pct`, `msg` | 进度更新（0~100） |
| `TEST_DONE` | `case`, `result`, `err`, `duration_s` | 用例结束 |
| `TEST_STOPPED` | `case` | 已中止 |
| `TEST_BATCH_DONE` | `pass`, `fail`, `abort` | 整套用例全部执行完成后的统计 |
| `STATUS_RSP` | `state`, `current_case` | state: `IDLE`/`RUNNING`/`ERROR` |
| `FW_READY` | — | 固件会话就绪，可开始发送数据块 |
| `FW_CHUNK_OK` | `offset` | 已接收一块固件数据 |
| `FW_DONE` | `ok`, `size`, `path` | 固件烧录结束并校验结果 |
| `FW_ERROR` | `msg` | 固件传输错误 |
| `ERROR` | `msg` | 错误 |

**result 取值**：`PASS` / `FAIL` / `ABORT`
**err 格式**：`"0x0000"` 表示通过，其他为错误码（hex 字符串）；`ABORT` 用例 err 为 `"0xFFFF"`

**示例：**
```json
{"type": "PONG", "version": "1.0.0", "uptime_s": 3600}
{"type": "TEST_LIST_RSP", "cases": ["FW_BOOT","DDR_TEST","PCIE_TEST"]}
{"type": "TEST_STARTED", "case": "DDR_TEST"}
{"type": "TEST_PROGRESS", "case": "DDR_TEST", "pct": 50, "msg": "running pattern 3/6..."}
{"type": "TEST_DONE", "case": "DDR_TEST", "result": "PASS", "err": "0x0000", "duration_s": 12.3}
{"type": "TEST_BATCH_DONE", "pass": 3, "fail": 0, "abort": 0}
{"type": "STATUS_RSP", "state": "IDLE", "current_case": null}
{"type": "FW_READY"}
{"type": "FW_CHUNK_OK", "offset": 8192}
{"type": "FW_DONE", "ok": true, "size": 51200, "path": "/tmp/slt_fw_kernel.bin"}
```

## 4.2 固件烧录流程（FW_BEGIN / FW_CHUNK / FW_END）

上位机选固件文件后分块（8KB）发送：

1. 上位机发 `FW_BEGIN {file_type, size, sha256}` → 下位机回 `FW_READY`
2. 上位机逐块发 `FW_CHUNK {offset, data(base64)}` → 下位机回 `FW_CHUNK_OK`，按 offset 写入接收缓冲
3. 上位机发 `FW_END` → 下位机校验字节数并写入 `/tmp/slt_fw_<file_type>.bin`，回 `FW_DONE {ok, size, path}`

- 支持多台机台并行烧录（每台独立 TCP 连接）
- 仿真模式下位机由上位机本地模拟，直接返回成功

## 4.1 批量执行模式（TEST_RUN_ALL）与崩溃续跑

- 上位机在开始一轮测试时，通过 `TEST_RUN_ALL` **一次性下发整套用例列表**。
- 下位机在本地线程中**逐个执行**整个列表（每用例仍发 `TEST_STARTED`/`TEST_PROGRESS`/`TEST_DONE`），全部完成后发 `TEST_BATCH_DONE` 携带 `pass/fail/abort` 统计。
- **上位机崩溃断连后，下位机的批量执行线程不受影响，会继续把剩余用例跑完**（无需再接收指令），跑完在 `TEST_BATCH_DONE` 时发送（若连接已断，发送失败不影响执行）。
- 上位机发送 `TEST_STOP` 时，下位机置停止标志：当前用例中止（记 `abort`），后续未执行用例全部记 `abort`，随后仍发 `TEST_BATCH_DONE`。

## 5. 错误码定义

| 错误码 | 含义 |
|--------|------|
| `0x0000` | 通过 |
| `0x1001` | 固件启动失败 |
| `0x2001` | DDR training fail |
| `0x2002` | DDR pattern error |
| `0x3001` | PCIe link down |
| `0x3002` | PCIe training fail |
| `0x4001` | IRQ count mismatch |
| `0x5001` | RAS error injected |
| `0x6001` | Security runtime check fail |
| `0x7001` | Thermal overtemp |
| `0x7002` | Power rail voltage out of range |
| `0xFFFF` | 未知错误 |

## 6. 超时与重连

- PC 发送命令后等待响应超时 **5 秒**
- 测试执行中的结果推送不设超时（由 PC 侧 Stop 控制）
- TCP 断开后 PC 自动重连，重连间隔 3 秒
