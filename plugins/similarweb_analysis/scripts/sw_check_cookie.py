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
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "data")
COOKIE_FILE = os.path.join(DATA_DIR, "sw_cookies.txt")
LOG_FILE = os.path.join(DATA_DIR, "cookie_check_log.json")

# Allow importing from the same scripts directory
sys.path.insert(0, SCRIPT_DIR)
from similarweb_api import SimilarWebAPI


def load_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    return []


def save_log(log):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def check():
    now = datetime.now().isoformat()
    api = SimilarWebAPI(cookie_file=COOKIE_FILE)

    # 检查文件
    if not os.path.exists(COOKIE_FILE):
        print(f"[{now}] FAIL - cookie 文件不存在: {COOKIE_FILE}")
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
