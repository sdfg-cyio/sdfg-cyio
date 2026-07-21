#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日看板娘自动更新脚本
- 从 nekos.best 抓取白天/夜晚两张图，下载到 assets/ 目录
- 随机抽取一条运势文案
- 写入 README.md 的占位标记之间（引用本地图片）
- API 失败则保持昨日内容不变
"""

import json
import os
import re
import random
import datetime
import sys

import urllib.request
import urllib.error

# ============== 配置区 ==============
API_BASE = "https://nekos.best/api/v2"
DAY_CATEGORY = "neko"         # 浅色模式：猫娘
NIGHT_CATEGORY = "kitsune"    # 深色模式：狐娘
USER_AGENT = "github-profile-bot/1.0 (https://github.com/github-actions)"
TIMEOUT = 15
README_PATH = "README.md"
ASSETS_DIR = "assets"
DAY_FILE = "day.png"
NIGHT_FILE = "night.png"

# ============== 运势文案池 ==============
FORTUNES = [
    # —— 技术梗 ——
    ("大吉 🌟", "今天写的代码一次通过，没有任何 bug！"),
    ("大吉 🌟", "产品经理今天请假，需求不会变更。"),
    ("中吉", "适合重构祖传代码的一天。"),
    ("中吉", "Stack Overflow 上的第一个回答就是正解。"),
    ("中吉", "今天不会有 merge conflict。"),
    ("小吉", "记得提交代码前先跑一遍测试。"),
    ("小吉", "别在周五下午部署。"),
    ("末吉", "小心命名冲突，记得看 diff。"),
    ("末吉", "今天别碰那个能跑就别动的文件。"),
    ("凶 ⚠️", "今天写的代码明天可能要重写。"),

    # —— 生活向 ——
    ("大吉 🌟", "适合出门走走，别光对着屏幕。"),
    ("中吉", "今天记得喝水，每小时一杯。"),
    ("中吉", "早睡早起，精神百倍。"),
    ("小吉", "给家人朋友打个电话吧。"),
    ("小吉", "整理一下桌面，心情也会变好。"),
    ("末吉", "今天少喝点咖啡。"),

    # —— 二次元梗 ——
    ("大吉 🌟", "今天的你，比昨天更 kawaii。"),
    ("中吉", "yyds，今天也是被纸片人治愈的一天。"),
    ("中吉", "追番进度 +1，人生进度 +0。"),
    ("小吉", "今天适合补完一部番。"),
    ("小吉", "别忘了你的老婆/老公还在等你看她/他。"),
    ("末吉", "今天不要立 flag。"),
]


def fetch_and_download(category, save_path):
    """从 nekos.best 抓取一张图并下载到本地，返回 (success, artist)"""
    api_url = f"{API_BASE}/{category}"
    req = urllib.request.Request(api_url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, ValueError) as e:
        print(f"[WARN] 请求 {category} API 失败: {e}")
        return False, None

    try:
        result = data["results"][0]
        img_url = result["url"]
        artist = result.get("artist_name") or "未知画师"
    except (KeyError, IndexError) as e:
        print(f"[WARN] 解析 {category} 响应失败: {e}")
        return False, None

    # 下载图片到本地
    img_req = urllib.request.Request(img_url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(img_req, timeout=TIMEOUT) as resp:
            img_data = resp.read()
        os.makedirs(ASSETS_DIR, exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(img_data)
        print(f"[OK] 已下载 {category}: {save_path} ({len(img_data)} bytes)")
        return True, artist
    except urllib.error.URLError as e:
        print(f"[WARN] 下载 {category} 图片失败: {e}")
        return False, None


def build_block(artist, fortune, today_str):
    """生成写入 README 的整段内容（引用本地图片）"""
    luck, msg = fortune
    return f"""<!--ANIME-START-->
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/{NIGHT_FILE}">
  <source media="(prefers-color-scheme: light)" srcset="assets/{DAY_FILE}">
  <img src="assets/{DAY_FILE}" width="280" align="right" alt="今日看板娘"/>
</picture>

### 🌸 今日看板娘 · {today_str}

**今日运势：{luck}**
{msg}

画师：{artist}
*每天 0 点由 GitHub Actions 自动更新 | 切换深色模式看看？*
<!--ANIME-END-->"""


def main():
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    day_path = os.path.join(ASSETS_DIR, DAY_FILE)
    night_path = os.path.join(ASSETS_DIR, NIGHT_FILE)

    # 抓取并下载两张图
    day_ok, day_artist = fetch_and_download(DAY_CATEGORY, day_path)
    night_ok, night_artist = fetch_and_download(NIGHT_CATEGORY, night_path)

    # 两张图都必须成功，否则保持昨日内容不变
    if not day_ok or not night_ok:
        print("[INFO] 图片未抓全，README 保持不变。")
        # 但如果有一张成功了，不影响另一张
        return 0

    # 以白天图的画师为准展示
    artist = day_artist or "未知画师"
    fortune = random.choice(FORTUNES)

    new_block = build_block(artist, fortune, today_str)

    # 读取 README，替换占位标记之间的内容
    try:
        with open(README_PATH, "r", encoding="utf-8") as f:
            readme = f.read()
    except FileNotFoundError:
        print(f"[ERROR] 找不到 {README_PATH}")
        return 1

    pattern = r"<!--ANIME-START-->.*?<!--ANIME-END-->"
    if not re.search(pattern, readme, flags=re.S):
        print("[ERROR] README 中未找到占位标记 <!--ANIME-START--> ... <!--ANIME-END-->")
        return 1

    new_readme = re.sub(pattern, new_block, readme, flags=re.S)
    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_readme)

    print(f"[OK] 已更新 README，画师：{artist}")
    print(f"     运势：{fortune[0]} - {fortune[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
