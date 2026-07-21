#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日自动更新脚本
- 从 nekos.best 抓取白天/夜晚两张图
- 随机抽取一条运势文案
- 写入 README.md 的占位标记之间
- API 失败则保持昨日内容不变
"""

import json
import re
import random
import datetime
import sys

import urllib.request
import urllib.error

API_BASE = "https://nekos.best/api/v2"
DAY_CATEGORY = "neko"        
NIGHT_CATEGORY = "kitsune"   
USER_AGENT = "github-profile-bot/1.0 (https://github.com/github-actions)"
TIMEOUT = 15
README_PATH = "README.md"


FORTUNES = [

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


    ("大吉 🌟", "适合出门走走，别光对着屏幕。"),
    ("中吉", "今天记得喝水，每小时一杯。"),
    ("中吉", "早睡早起，精神百倍。"),
    ("小吉", "给家人朋友打个电话吧。"),
    ("小吉", "整理一下桌面，心情也会变好。"),
    ("末吉", "今天少喝点咖啡。"),


    ("大吉 🌟", "今天的你，比昨天更 kawaii。"),
    ("中吉", "yyds，今天也是被纸片人治愈的一天。"),
    ("中吉", "追番进度 +1，人生进度 +0。"),
    ("小吉", "今天适合补完一部番。"),
    ("小吉", "别忘了你的老婆/老公还在等你看她/他。"),
    ("末吉", "今天不要立 flag。"),
]


def fetch_image(category):
    """从 nekos.best 抓取一张图，返回 (url, artist) 或 None"""
    url = f"{API_BASE}/{category}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        result = data["results"][0]
        img_url = result["url"]
        artist = result.get("artist_name") or "未知画师"
        return img_url, artist
    except (urllib.error.URLError, KeyError, IndexError, ValueError) as e:
        print(f"[WARN] 抓取 {category} 失败: {e}")
        return None


def build_block(day_img, day_artist, night_img, night_artist, fortune, today_str):
    luck, msg = fortune

    return f"""<!--ANIME-START-->
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="{night_img}">
  <source media="(prefers-color-scheme: light)" srcset="{day_img}">
  <img src="{day_img}" width="280" align="right" alt="今日看板娘"/>
</picture>

### 🌸 今日看板娘 · {today_str}

**今日运势：{luck}**
{msg}

画师：{day_artist}
*每天 0 点由 GitHub Actions 自动更新 | 切换深色模式看看？*
<!--ANIME-END-->"""


def main():
    today_str = datetime.date.today().strftime("%Y-%m-%d")


    day = fetch_image(DAY_CATEGORY)
    night = fetch_image(NIGHT_CATEGORY)


    if not day or not night:
        print("[INFO] 图片未抓全，README 保持不变。")
        return 0

    day_img, day_artist = day
    night_img, night_artist = night
    fortune = random.choice(FORTUNES)

    new_block = build_block(day_img, day_artist, night_img, night_artist, fortune, today_str)


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

    print(f"[OK] 已更新 README，今日看板娘：{day_img}")
    print(f"     夜晚版：{night_img}")
    print(f"     运势：{fortune[0]} - {fortune[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
