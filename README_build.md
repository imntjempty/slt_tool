# SLT Test Tool - Windows 打包说明

## 项目结构（模块化 + Designer .ui）

```
SLT_Tools/
├── run.py                    # ★ 程序入口（python run.py）
├── requirements.txt
├── build_windows.bat         # ★ Windows 一键打包
├── ui/                       # ★ PyQt Designer 界面 (.ui 格式)
│   ├── main_window.ui        #   主窗口
│   ├── conn_panel.ui         #   连接面板
│   ├── station_panel.ui      #   机台面板
│   └── dashboard.ui          #   总览
├── app/                      # 业务逻辑模块
│   ├── config.py             #   常量配置
│   ├── i18n.py               #   中英双语
│   ├── test_cases.py         #   测试用例定义
│   ├── comm.py               #   通信通道(RS232/TCP/仿真)
│   ├── worker.py             #   测试执行线程
│   ├── logger.py             #   日志+写保护
│   └── ui/                   #   UI 控制器
│       ├── main_window.py
│       ├── conn_panel.py
│       ├── station_panel.py
│       └── dashboard.py
```

> 界面用 **Qt Designer** 编辑 `ui/*.ui`（XML），运行时代码用 `uic.loadUi` 加载，改布局不用动代码。

## 方法一：一键脚本（推荐）

1. 把**整个项目文件夹**（`run.py`、`app/`、`ui/`、`build_windows.bat`）拷到 Windows
2. 确保装了 Python 3.8+（勾选 Add to PATH）
3. 双击 `build_windows.bat`
4. 生成的 exe 在 `dist\SLT_Test_Tool.exe`

## 方法二：手动命令

```cmd
pip install PyQt5 pyserial pyinstaller

python -m PyInstaller --noconfirm --windowed --onefile ^
    --name "SLT_Test_Tool" --add-data "ui;ui" run.py
```

## 参数说明

| 参数 | 作用 |
|---|---|
| `--windowed` | 不弹黑色控制台窗口 |
| `--onefile` | 打包成单个 exe |
| `--add-data "ui;ui"` | 把 `.ui` 界面文件一起打进 exe（**必填**，否则界面空白） |
| `--name` | exe 文件名 |
| `--noconfirm` | 自动覆盖旧产物 |

> 注意用 `python -m PyInstaller`，不要直接用 `pyinstaller` 命令（环境变量可能未注册）。

## 常见问题

- **杀毒软件报毒**：PyInstaller 打包容易被误报，加白名单即可
- **exe 体积大**：正常，PyQt5 约 40-60MB
- **需要图标**：加 `--icon=your_icon.ico`
- **改了 .ui 不生效**：确保 `--add-data "ui;ui"` 且入口是 `run.py`
