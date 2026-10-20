# -*- coding: utf-8 -*-
"""Generate architecture / UI layout / operation-flow images for the docs.
Requires Pillow (PIL). Auto-installs if missing.
Run:  python make_doc_images.py
"""
import os
import sys
import subprocess


def _ensure_pillow():
    try:
        import PIL  # noqa
        return
    except ImportError:
        pass
    print("缺少 Pillow 库，正在自动安装（python -m pip install Pillow）...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
        import PIL  # noqa
        print("Pillow 安装成功。")
    except Exception as e:
        print(f"自动安装失败：{e}")
        print("请手动执行：  python -m pip install Pillow  后重新运行本脚本")
        sys.exit(1)


_ensure_pillow()

from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
os.makedirs(OUT, exist_ok=True)
FONT_CANDIDATES = {
    "regular": [
        # Linux
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/arphic/uming.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc",
        # Windows
        os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts", "msyh.ttc"),
        os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts", "simhei.ttf"),
        os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts", "simsun.ttc"),
        os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts", "Deng.ttf"),
    ],
    "bold": [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc",
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc",
        os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts", "msyhbd.ttc"),
        os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts", "simhei.ttf"),
    ],
}


def _find_font(kind):
    for p in FONT_CANDIDATES[kind]:
        if os.path.exists(p):
            return p
    for p in FONT_CANDIDATES["regular" if kind == "bold" else "bold"]:
        if os.path.exists(p):
            return p
    return None


FONT = _find_font("regular")
FONT_B = _find_font("bold") or FONT
if not FONT:
    print("警告：未找到中文字体，将使用默认字体（中文可能显示为方框）。")

def font(sz, bold=False):
    if FONT:
        return ImageFont.truetype(FONT_B if bold else FONT, sz)
    return ImageFont.load_default()

# palette
INK    = (43, 62, 80)      # dark slate
BLUE   = (33, 105, 196)
LGREY  = (238, 242, 247)
MGREY  = (200, 210, 220)
GREEN  = (39, 174, 96)
RED    = (231, 76, 60)
AMBER  = (243, 156, 18)
WHITE  = (255, 255, 255)
LBLUE  = (229, 241, 255)

def rrect(d, box, r, fill=None, outline=None, width=2):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)

def center_text(d, cx, cy, txt, fnt, fill=INK, box=None, anchor="center"):
    w, h = d.textbbox((0, 0), txt, font=fnt)[2:4]
    if box:  # constrain inside box
        bw, bh = box[2]-box[0], box[3]-box[1]
        if w > bw or h > bh:
            return
    if anchor == "la":
        d.text((cx, cy - h/2), txt, font=fnt, fill=fill)
    else:
        d.text((cx - w/2, cy - h/2), txt, font=fnt, fill=fill)

def text_anchor(d, x, y, txt, fnt, fill=INK, anchor="la"):
    w, h = d.textbbox((0, 0), txt, font=fnt)[2:4]
    if anchor == "la": px, py = x, y
    elif anchor == "ra": px, py = x - w, y
    else: px, py = x - w/2, y
    d.text((px, py), txt, font=fnt, fill=fill)

# ============================================================
# Fig 1: System architecture
# ============================================================
S = 2  # supersample scale
W, H = 1500, 920
img = Image.new("RGB", (W*S, H*S), WHITE)
d = ImageDraw.Draw(img)
f_title = font(40, True); f_h2 = font(30, True); f_body = font(25)
f_small = font(20); f_box = font(26, True)

# --- upper PC block ---
pc = [90, 90, 1410, 640]
rrect(d, [x*S for x in pc], 16, fill=LGREY, outline=BLUE, width=4*S)
center_text(d, (pc[0]+pc[2])/2*S, 70*S, "上位机 PC（PyQt5 多机台）", f_title, BLUE)
# top bar
topbar = [pc[0]+30, 120, pc[2]-30, 175]
rrect(d, [x*S for x in topbar], 10, fill=WHITE, outline=MGREY, width=2*S)
center_text(d, (topbar[0]+topbar[2])/2*S, (topbar[1]+topbar[3])/2*S,
            "[ 全部开始 ]  [ 全部停止 ]                      语言: [ 中文 ▼ ]", f_body)
# tabs
tabs = [pc[0]+30, 195, pc[2]-30, 245]
rrect(d, [x*S for x in tabs], 10, fill=WHITE, outline=MGREY, width=2*S)
center_text(d, (tabs[0]+tabs[2])/2*S, (tabs[1]+tabs[3])/2*S,
            "总览 | 机台1 | 机台2 | 机台3 | 机台4 | 机台5 | 机台6", f_body)
# station row: handler + board channel
y0 = 265
ch_bw = 600
# handler
hb = [pc[0]+30, y0, pc[0]+30+ch_bw, y0+170]
rrect(d, [x*S for x in hb], 12, fill=LBLUE, outline=BLUE, width=2*S)
center_text(d, (hb[0]+hb[2])/2*S, (hb[1]+40)*S, "每台机台: Handler 通道", f_box, BLUE)
center_text(d, (hb[0]+hb[2])/2*S, (hb[1]+95)*S, "电源 / 温控 / 机械臂", f_body)
center_text(d, (hb[0]+hb[2])/2*S, (hb[1]+140)*S, "RS232 / TCP / 仿真", f_small, MGREY)
# board
bb = [pc[2]-30-ch_bw, y0, pc[2]-30, y0+170]
rrect(d, [x*S for x in bb], 12, fill=LBLUE, outline=BLUE, width=2*S)
center_text(d, (bb[0]+bb[2])/2*S, (bb[1]+40)*S, "每台机台: Board 通道", f_box, BLUE)
center_text(d, (bb[0]+bb[2])/2*S, (bb[1]+95)*S, "测试用例下发", f_body)
center_text(d, (bb[0]+bb[2])/2*S, (bb[1]+140)*S, "RS232 / TCP / 仿真", f_small, MGREY)
# independent note between
center_text(d, (pc[0]+pc[2])/2*S, (y0+85)*S, "独立互不干扰", f_body, MGREY)
# log bar
lg = [pc[0]+30, y0+190, pc[2]-30, y0+235]
rrect(d, [x*S for x in lg], 8, fill=WHITE, outline=MGREY, width=2*S)
center_text(d, (lg[0]+lg[2])/2*S, (lg[1]+lg[3])/2*S, "底部: 全局日志（可拖拽调整大小）", f_small, MGREY)

# down arrows
from PIL import ImageDraw as ID
def down_arrow(cx, y_top, y_bot, color=BLUE, w=4*S):
    ax = cx*S
    d.line([(ax, y_top*S), (ax, (y_bot-18)*S)], fill=color, width=w)
    d.polygon([(ax-14*S, (y_bot-18)*S), (ax+14*S, (y_bot-18)*S), (ax, y_bot*S)], fill=color)

# arrows from pc bottom to handler / board
down_arrow(300, 635, 700, BLUE)
down_arrow(1200, 635, 700, BLUE)
# from board further down to daemon
down_arrow(1200, 755, 800, GREEN)

# lower hardware blocks
hw_h = [120, 680, 480, 760]
rrect(d, [x*S for x in hw_h], 10, fill=WHITE, outline=INK, width=3*S)
center_text(d, (hw_h[0]+hw_h[2])/2*S, (hw_h[1]+hw_h[3])/2*S, "SLT Handler（供电/ATC/机械臂）", f_box)
hw_b = [1020, 680, 1380, 760]
rrect(d, [x*S for x in hw_b], 10, fill=WHITE, outline=INK, width=3*S)
center_text(d, (hw_b[0]+hw_b[2])/2*S, (hw_b[1]+hw_b[3])/2*S, "SLT 测试板（DUT 待测芯片）", f_box)
# daemon
dm = [1080, 800, 1320, 870]
rrect(d, [x*S for x in dm], 10, fill=GREEN, outline=GREEN, width=3*S)
center_text(d, (dm[0]+dm[2])/2*S, (dm[1]+dm[3])/2*S, "下位机 daemon", f_box, WHITE)
center_text(d, (dm[0]+dm[2])/2*S, (dm[1]+dm[3])/2*S + 26*S, "TCP:5001", f_small, WHITE)

# connection labels
center_text(d, 300*S, 668*S, "RS232 / TCP", f_small, BLUE)
center_text(d, 1200*S, 668*S, "RS232 / TCP（NDJSON）", f_small, BLUE)
center_text(d, 1200*S, 780*S, "TCP:5001", f_small, GREEN)

img = img.resize((W, H), Image.LANCZOS)
img.save(f"{OUT}/slt_arch.png")
print("saved arch", img.size)

# ============================================================
# Fig 2: UI layout
# ============================================================
W, H = 1500, 1000
img = Image.new("RGB", (W*S, H*S), WHITE)
d = ImageDraw.Draw(img)
center_text(d, W/2*S, 45*S, "主窗口 UI 布局", f_title, INK)

# main window frame
mw = [60, 85, 1440, 955]
rrect(d, [x*S for x in mw], 14, fill=LGREY, outline=INK, width=3*S)

# top bar
tb = [mw[0]+20, mw[1]+20, mw[2]-20, mw[1]+72]
rrect(d, [x*S for x in tb], 8, fill=WHITE, outline=MGREY, width=2*S)
center_text(d, (tb[0]+tb[2])/2*S, (tb[1]+tb[3])/2*S, "[▶ 全部开始] [■ 全部停止]                    语言: [简体中文 ▼]", f_body)

# tabs
tab = [mw[0]+20, mw[1]+84, mw[2]-20, mw[1]+130]
rrect(d, [x*S for x in tab], 8, fill=WHITE, outline=MGREY, width=2*S)
center_text(d, (tab[0]+tab[2])/2*S, (tab[1]+tab[3])/2*S, "总览 | 机台1 | 机台2 | 机台3 | 机台4 | 机台5 | 机台6", f_body)

# conn panels
cy0 = mw[1]+146; chh = 120; cw = 640
ph = [mw[0]+20, cy0, mw[0]+20+cw, cy0+chh]
rrect(d, [x*S for x in ph], 10, fill=LBLUE, outline=BLUE, width=2*S)
center_text(d, (ph[0]+20)*S, (ph[1]+28)*S, "Handler 控制箱", f_box, BLUE, anchor="la")
center_text(d, (ph[0]+ph[2])/2*S, (ph[1]+70)*S, "类型: [RS232▼]  端口: [COM3▼]  波特率: [115200▼]", f_body)
center_text(d, (ph[0]+ph[2])/2*S, (ph[1]+102)*S, "[连接]  ● 已连接", f_body, GREEN)
pb = [mw[2]-20-cw, cy0, mw[2]-20, cy0+chh]
rrect(d, [x*S for x in pb], 10, fill=LBLUE, outline=BLUE, width=2*S)
center_text(d, (pb[0]+20)*S, (pb[1]+28)*S, "Board 测试板", f_box, BLUE, anchor="la")
center_text(d, (pb[0]+pb[2])/2*S, (pb[1]+70)*S, "类型: [TCP/IP▼]  IP: [192.168.1.101]  端口: [5001]", f_body)
center_text(d, (pb[0]+pb[2])/2*S, (pb[1]+102)*S, "[连接]  ● 已连接", f_body, GREEN)

# middle: tree (left) + results (right)
my0 = cy0 + chh + 16; mh = 420; tree_w = 470
tree = [mw[0]+20, my0, mw[0]+20+tree_w, my0+mh]
rrect(d, [x*S for x in tree], 10, fill=WHITE, outline=MGREY, width=2*S)
center_text(d, (tree[0]+20)*S, (tree[1]+30)*S, "测试用例   [全选] [清空]", f_box, anchor="la")
lines = ["▸ MBIST 内存自检（必测）", "▸ Firmware Boot / 固件启动", "▸ Low-speed IO / 低速IO",
         "▸ DDR Test", "▸ PCIe Test", "▸ Interrupt / 中断", "▸ RAS-Extension",
         "▸ Security Runtime", "▸ Mixed Stability", "▸ Power & Thermal"]
for i, ln in enumerate(lines):
    center_text(d, (tree[0]+40)*S, (tree[1]+75+i*34)*S, ln, f_body, anchor="la")
center_text(d, (tree[0]+40)*S, (tree[1]+mh-36)*S, "本机台芯片目标数: [ 1 ]", f_box, anchor="la")

res = [tree[2]+16, my0, mw[2]-20, my0+mh]
rrect(d, [x*S for x in res], 10, fill=WHITE, outline=MGREY, width=2*S)
center_text(d, (res[0]+20)*S, (res[1]+30)*S, "结果表  芯片 | 测试项 | 描述 | 结果 | 错误码", f_box, anchor="la")
# table header
hdr_y = res[1]+56
center_text(d, (res[0]+100)*S, hdr_y*S, "Chip1", f_small)
center_text(d, (res[0]+260)*S, hdr_y*S, "DDR_BENCH", f_small)
center_text(d, (res[0]+430)*S, hdr_y*S, "PASS", f_small, GREEN)
center_text(d, (res[0]+520)*S, hdr_y*S, "0x0000", f_small)
d.line([(res[0]*S, (hdr_y+18)*S), (res[2]*S, (hdr_y+18)*S)], fill=MGREY, width=1*S)
for i in range(3):
    center_text(d, (res[0]+100)*S, (hdr_y+40+i*32)*S, f"Chip1", f_small)
    center_text(d, (res[0]+260)*S, (hdr_y+40+i*32)*S, "DDR_STRESS", f_small)
    center_text(d, (res[0]+430)*S, (hdr_y+40+i*32)*S, "PASS", f_small, GREEN)
    center_text(d, (res[0]+520)*S, (hdr_y+40+i*32)*S, "0x0000", f_small)
# bin stats
bins_y = res[3]-70
bins = ["BIN0-PASS", "BIN1-FAIL", "BIN2-ABORT"]
bcol = [GREEN, RED, AMBER]
for i, (b, c) in enumerate(zip(bins, bcol)):
    bx = [res[0]+20+i*200, bins_y, res[0]+190+i*200, bins_y+48]
    rrect(d, [x*S for x in bx], 8, fill=WHITE, outline=c, width=2*S)
    center_text(d, (bx[0]+bx[2])/2*S, (bx[1]+bx[3])/2*S, b, f_body, c)

# bottom buttons
by0 = my0 + mh + 16; bh2 = 60
bbx = [mw[0]+20, by0, mw[2]-20, by0+bh2]
rrect(d, [x*S for x in bbx], 10, fill=WHITE, outline=MGREY, width=2*S)
center_text(d, (bbx[0]+bbx[2])/2*S, (bbx[1]+bbx[3])/2*S,
            "[▶ 开始] [⏸ 暂停] [⏵ 继续] [■ 停止]   进度: [████░░░░░░] 测试中...", f_body)

# bottom log
ly0 = by0 + bh2 + 14
logb = [mw[0]+20, ly0, mw[2]-20, mw[3]-16]
rrect(d, [x*S for x in logb], 10, fill=WHITE, outline=MGREY, width=2*S)
center_text(d, (logb[0]+20)*S, (logb[1]+26)*S, "全局日志（可上下拖动调整大小）", f_box, anchor="la")
center_text(d, (logb[0]+20)*S, (logb[1]+62)*S, "10:01:02  机台6  RAS_UCIE  通过  0x0000", f_small, MGREY, anchor="la")
center_text(d, (logb[0]+20)*S, (logb[1]+92)*S, "10:01:05  机台2  DDR_BENCH 通过  0x0000", f_small, MGREY, anchor="la")

img = img.resize((W, H), Image.LANCZOS)
img.save(f"{OUT}/slt_ui_layout.png")
print("saved ui_layout", img.size)

# ============================================================
# Fig 3: Operation flow (production worker)
# ============================================================
W, H = 1500, 320
img = Image.new("RGB", (W*S, H*S), WHITE)
d = ImageDraw.Draw(img)
steps = ["① 连接机台", "② 勾选测试项", "③ 填芯片数", "④ 点开始", "⑤ 看总览结果", "⑥ 异常找工程师"]
notes = ["Handler+Board\n都连上", "默认已全选\n一般不用动", "本机台\n目标芯片数", "▶ 开始\n(可暂停/继续)", "BIN0/BIN1\n统计", "BIN1偏高\n就停下"]
n = len(steps)
sw, gap = 240, 24
total_w = n*sw + (n-1)*gap
x0 = (W - total_w)//2
for i in range(n):
    x = x0 + i*(sw+gap)
    box = [x, 90, x+sw, 230]
    rrect(d, [x*S for x in box], 14, fill=LBLUE, outline=BLUE, width=3*S)
    center_text(d, (x+sw/2)*S, 118*S, steps[i], f_box, BLUE)
    # note
    lines_n = notes[i].split("\n")
    yy = 162
    for ln in lines_n:
        center_text(d, (x+sw/2)*S, yy*S, ln, f_small, INK)
        yy += 30
    if i < n-1:
        ax = (x+sw)*S; cx = (x+sw+gap/2)*S
        d.line([(ax, 160*S), (cx-14*S, 160*S)], fill=MGREY, width=4*S)
        d.polygon([(cx, 160*S), (cx-16*S, 148*S), (cx-16*S, 172*S)], fill=MGREY)

img = img.resize((W, H), Image.LANCZOS)
img.save(f"{OUT}/slt_flow.png")
print("saved flow", img.size)
