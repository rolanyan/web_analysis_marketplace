"""
Cookie 有效性检查
- 检查 cookie 文件是否存在
- 测试 API 调用是否正常
- 记录检查日志用于跟踪有效期
"""

import os
import json
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIE_FILE = os.environ.get("SW_COOKIE_FILE")
if not COOKIE_FILE:
    print("[ERROR] 环境变量 SW_COOKIE_FILE 未设置。请在 ~/.claude/.env 或 shell profile 中配置。")
    sys.exit(1)
LOG_FILE = os.path.join(os.path.dirname(COOKIE_FILE), "cookie_check_log.json")

# Allow importing from the same scripts directory
sys.path.insert(0, SCRIPT_DIR)
from similarweb_api import SimilarWebAPI


def load_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    return []


def save_log(log):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def check():
    now = datetime.now().isoformat()
    api = SimilarWebAPI(cookie_file=COOKIE_FILE)

    # 检查文件，不存在则创建空文件（含父目录）
    if not os.path.exists(COOKIE_FILE):
        os.makedirs(os.path.dirname(COOKIE_FILE), exist_ok=True)
        open(COOKIE_FILE, "w").close()
        print(f"[{now}] cookie 文件不存在，已创建: {COOKIE_FILE}")
        print("请运行 /sw_login 获取 cookie")
        return False

    mtime = os.path.getmtime(COOKIE_FILE)
    cookie_age_hours = (datetime.now().timestamp() - mtime) / 3600
    print(f"Cookie 文件年龄: {cookie_age_hours:.1f} 小时 ({cookie_age_hours/24:.1f} 天)")

    # 测试 identities API（轻量级）
    valid = api.is_cookie_valid()
    status = "OK" if valid else "EXPIRED"
    print(f"[{now}] {status}")

    # 测试一个数据 API
    data_ok = False
    if valid:
        try:
            result = api.get_total_visits("github.com")
            visits = result.get("Data", {}).get("github.com", {}).get("TotalVisits", 0)
            data_ok = visits > 0
            print(f"数据 API: {'OK' if data_ok else 'FAIL'} (TotalVisits={visits})")
        except Exception as e:
            print(f"数据 API: FAIL ({e})")

    # 记录日志
    log = load_log()
    log.append({
        "time": now,
        "cookie_age_hours": round(cookie_age_hours, 1),
        "identity_valid": valid,
        "data_api_ok": data_ok,
    })
    save_log(log)

    # 显示历史
    if len(log) > 1:
        print(f"\n历史记录 (共 {len(log)} 次):")
        for entry in log[-5:]:
            age = entry["cookie_age_hours"]
            s = "OK" if entry["identity_valid"] else "EXPIRED"
            print(f"  {entry['time']}  age={age:.1f}h  {s}")

    return valid


if __name__ == "__main__":
    ok = check()
    sys.exit(0 if ok else 1)
