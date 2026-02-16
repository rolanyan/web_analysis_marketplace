"""
SimilarWeb 半自动登录 + Cookie 提取
通过 dev-browser 打开 SimilarWeb，检测是否需要验证码，提示用户输入后自动填写。
最终提取并保存 cookie。
"""

import subprocess
import json
import sys
import os
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "data")
COOKIE_FILE = os.path.join(DATA_DIR, "sw_cookies.txt")

DEV_BROWSER_DIR = None


def find_dev_browser_dir():
    """查找 dev-browser 插件目录"""
    import glob
    pattern = os.path.expanduser(
        "~/.claude/plugins/cache/dev-browser-marketplace/dev-browser/*/skills/dev-browser"
    )
    dirs = glob.glob(pattern)
    if dirs:
        return dirs[0]
    return None


def run_tsx(script, timeout=30):
    """在 dev-browser 目录下运行 TypeScript 脚本"""
    result = subprocess.run(
        ["npx", "tsx", "-e", script],
        cwd=DEV_BROWSER_DIR,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        print(f"[WARN] tsx stderr: {result.stderr[:300]}")
    return result.stdout.strip()


def ensure_server():
    """确保 dev-browser server 在运行"""
    import urllib.request
    try:
        urllib.request.urlopen("http://localhost:9222/", timeout=3)
        print("[OK] dev-browser server 已在运行")
        return True
    except Exception:
        print("[INFO] 正在启动 dev-browser server...")
        subprocess.Popen(
            ["bash", "server.sh"],
            cwd=DEV_BROWSER_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(10)
        return True


def navigate_and_detect():
    """导航到 SimilarWeb 并检测页面状态"""
    script = '''
import { connect, waitForPageLoad } from "@/client.js";
const client = await connect();
const page = await client.page("sw_login", { viewport: { width: 1280, height: 900 } });
await page.goto("https://pro.similarweb.com/");
await waitForPageLoad(page);
await page.waitForTimeout(3000);
const url = page.url();
const title = await page.title();
await page.screenshot({ path: "tmp/login_state.png" });
console.log(JSON.stringify({ url, title }));
await client.disconnect();
'''
    output = run_tsx(script, timeout=30)
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return {"url": "", "title": "", "raw": output}


def fill_verification_code(code):
    """填写验证码并提交"""
    script = f'''
import {{ connect }} from "@/client.js";
const client = await connect();
const page = await client.page("sw_login");

// 填写验证码
const input = await page.$('input[type="text"]') || await page.$('input[type="number"]') || await page.$('input');
if (input) {{
    await input.fill("{code}");
    await page.waitForTimeout(500);

    // 点击提交按钮
    const btn = await page.$('button[type="submit"]')
        || await page.$('button:has-text("继续")')
        || await page.$('button:has-text("Continue")')
        || await page.$('button:has-text("Verify")')
        || await page.$('button:has-text("验证")');
    if (btn) {{
        await btn.click();
        await page.waitForTimeout(5000);
    }}
}}

const url = page.url();
const title = await page.title();
await page.screenshot({{ path: "tmp/after_verify.png" }});
console.log(JSON.stringify({{ url, title }}));
await client.disconnect();
'''
    output = run_tsx(script, timeout=20)
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return {"url": "", "title": "", "raw": output}


def handle_post_login_popups():
    """处理登录后可能出现的弹窗"""
    script = '''
import { connect } from "@/client.js";
const client = await connect();
const page = await client.page("sw_login");

// 检测并关闭常见弹窗
const closeSelectors = [
    'button:has-text("关闭")',
    'button:has-text("Close")',
    'button:has-text("Got it")',
    'button:has-text("Skip")',
    'button:has-text("跳过")',
    'button[aria-label="Close"]',
    'button[aria-label="close"]',
    '.modal-close',
];

for (const sel of closeSelectors) {
    try {
        const btn = await page.$(sel);
        if (btn && await btn.isVisible()) {
            await btn.click();
            await page.waitForTimeout(1000);
            console.log("closed: " + sel);
        }
    } catch {}
}

await page.screenshot({ path: "tmp/after_popup.png" });
const url = page.url();
console.log(JSON.stringify({ url }));
await client.disconnect();
'''
    return run_tsx(script, timeout=15)


def extract_cookies():
    """从浏览器提取 SimilarWeb cookie 并保存"""
    os.makedirs(DATA_DIR, exist_ok=True)
    cookie_path = os.path.abspath(COOKIE_FILE)
    script = '''
import { connect } from "@/client.js";
import * as fs from "fs";
const client = await connect();
const page = await client.page("sw_login");
const cookies = await page.context().cookies(["https://pro.similarweb.com"]);
const cookieStr = cookies.map(c => `${c.name}=${c.value}`).join("; ");
fs.writeFileSync("COOKIE_OUTPUT_PATH", cookieStr);
const result = { count: cookies.length, length: cookieStr.length };
console.log(JSON.stringify(result));
await client.disconnect();
'''.replace("COOKIE_OUTPUT_PATH", cookie_path)
    output = run_tsx(script, timeout=15)
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return {"raw": output}


def verify_cookie():
    """用一个简单的 API 调用验证 cookie 是否有效"""
    import requests
    try:
        with open(COOKIE_FILE, "r") as f:
            cookie_str = f.read().strip()
    except FileNotFoundError:
        return False

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/143.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://pro.similarweb.com/",
        "x-requested-with": "XMLHttpRequest",
        "x-sw-page": "https://pro.similarweb.com/#/digitalsuite/websiteanalysis/overview/website-performance/*/999/3m?webSource=Total&key=github.com",
        "Cookie": cookie_str,
    }
    resp = requests.get(
        "https://pro.similarweb.com/api/identities",
        headers=headers,
        timeout=15,
    )
    if resp.status_code == 200:
        data = resp.json()
        if data and isinstance(data, list) and data[0].get("UserName"):
            print(f"[OK] Cookie 有效，用户: {data[0]['UserName']}")
            return True
    print(f"[FAIL] Cookie 无效，状态码: {resp.status_code}")
    return False


def login_flow():
    """完整登录流程"""
    global DEV_BROWSER_DIR
    DEV_BROWSER_DIR = find_dev_browser_dir()
    if not DEV_BROWSER_DIR:
        print("[ERROR] 找不到 dev-browser 插件目录")
        sys.exit(1)
    print(f"[INFO] dev-browser 目录: {DEV_BROWSER_DIR}")

    # Step 1: 先检查现有 cookie 是否还有效
    if os.path.exists(COOKIE_FILE):
        print("\n[检查] 测试现有 cookie...")
        if verify_cookie():
            print("[OK] 现有 cookie 仍然有效，无需重新登录")
            return True

    # Step 2: 启动浏览器
    print("\n[Step 1] 启动 dev-browser server...")
    ensure_server()

    # Step 3: 导航并检测状态
    print("\n[Step 2] 导航到 SimilarWeb...")
    state = navigate_and_detect()
    print(f"    URL: {state.get('url', 'N/A')}")
    print(f"    Title: {state.get('title', 'N/A')}")

    url = state.get("url", "")

    # Step 4: 根据页面状态决定下一步
    if "device-verification" in url:
        print("\n[Step 3] 检测到设备验证页面，需要输入验证码")
        print("    验证码已发送到注册邮箱，请查收")
        code = input("    请输入验证码: ").strip()
        if not code:
            print("[ERROR] 未输入验证码")
            return False

        print(f"\n[Step 4] 填写验证码: {code}")
        result = fill_verification_code(code)
        print(f"    验证后 URL: {result.get('url', 'N/A')}")
        print(f"    验证后 Title: {result.get('title', 'N/A')}")

    elif "login" in url or "secure.similarweb" in url:
        print("\n[INFO] 需要完整登录，请在浏览器中手动登录后按回车")
        input("    手动登录完成后按回车继续...")

    elif "pro.similarweb.com" in url:
        print("\n[OK] 已经登录")

    # Step 5: 处理弹窗
    print("\n[Step 5] 处理可能的弹窗...")
    handle_post_login_popups()

    # Step 6: 提取 cookie
    print("\n[Step 6] 提取 cookie...")
    cookie_info = extract_cookies()
    print(f"    Cookie 数量: {cookie_info.get('count', 'N/A')}")
    print(f"    Cookie 长度: {cookie_info.get('length', 'N/A')}")

    # Step 7: 验证
    print("\n[Step 7] 验证 cookie...")
    if verify_cookie():
        print(f"\n[SUCCESS] 登录成功，cookie 已保存到 {COOKIE_FILE}")
        return True
    else:
        print("\n[FAIL] 登录失败，请重试")
        return False


if __name__ == "__main__":
    login_flow()
