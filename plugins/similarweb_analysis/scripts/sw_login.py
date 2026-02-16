"""
SimilarWeb Google 账号登录 + Cookie 提取
通过 dev-browser 打开 SimilarWeb，点击 Google Sign In，
自动填写 Google 邮箱/密码，处理可能的 SimilarWeb 设备验证码，
最终提取并保存 cookie。
"""

import subprocess
import json
import sys
import os
import time
import getpass

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
    """在 dev-browser 目录下运行 TypeScript 脚本（写入临时 .ts 文件以支持 top-level await）"""
    tmp_file = os.path.join(DEV_BROWSER_DIR, "_tmp_script.ts")
    try:
        with open(tmp_file, "w") as f:
            f.write(script)
        result = subprocess.run(
            ["npx", "tsx", tmp_file],
            cwd=DEV_BROWSER_DIR,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            print(f"[WARN] tsx stderr: {result.stderr[:300]}")
        return result.stdout.strip()
    finally:
        if os.path.exists(tmp_file):
            os.remove(tmp_file)


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


def navigate_to_login():
    """导航到 SimilarWeb，若需要登录则点击 Google Sign In"""
    script = '''
import { connect, waitForPageLoad } from "@/client.js";
const client = await connect();
const page = await client.page("sw_login", { viewport: { width: 1280, height: 900 } });
await page.goto("https://pro.similarweb.com/");
await waitForPageLoad(page);
await page.waitForTimeout(3000);

let url = page.url();
const title = await page.title();

// 判断是否已登录（在 pro.similarweb.com 且不在 login/verify 页面）
if (url.includes("pro.similarweb.com") && !url.includes("login") && !url.includes("verify") && !url.includes("secure.similarweb")) {
    await page.screenshot({ path: "tmp/login_state.png" });
    console.log(JSON.stringify({ state: "logged_in", url, title }));
    await client.disconnect();
    process.exit(0);
}

// 在登录页面，尝试点击 Google Sign In 按钮
const googleSelectors = [
    'button:has-text("Google")',
    'a:has-text("Google")',
    '[data-provider="google"]',
    'button:has-text("Sign in with Google")',
    'a:has-text("Sign in with Google")',
];

let clicked = false;
for (const sel of googleSelectors) {
    try {
        const btn = await page.$(sel);
        if (btn && await btn.isVisible()) {
            await btn.click();
            clicked = true;
            break;
        }
    } catch {}
}

if (clicked) {
    // 等待跳转到 Google 登录页面
    try {
        await page.waitForURL("**/accounts.google.com/**", { timeout: 15000 });
    } catch {
        // 可能已经跳转或页面变化
    }
    await page.waitForTimeout(2000);
}

url = page.url();
await page.screenshot({ path: "tmp/login_state.png" });

if (url.includes("accounts.google.com")) {
    console.log(JSON.stringify({ state: "google_login", url, title }));
} else if (url.includes("device-verification")) {
    console.log(JSON.stringify({ state: "verification", url, title }));
} else if (url.includes("login") || url.includes("secure.similarweb")) {
    console.log(JSON.stringify({ state: "login_page", url, title }));
} else {
    console.log(JSON.stringify({ state: "logged_in", url, title }));
}
await client.disconnect();
'''
    output = run_tsx(script, timeout=45)
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return {"state": "unknown", "url": "", "title": "", "raw": output}


def fill_google_credentials(email, password):
    """在 Google 登录页面填写邮箱和密码（两步式）"""
    # Step 1: 填写邮箱并点击 Next
    email_script = f'''
import {{ connect }} from "@/client.js";
const client = await connect();
const page = await client.page("sw_login");

// 填写邮箱
const emailInput = await page.$('input[type="email"]');
if (emailInput) {{
    await emailInput.fill("{email}");
    await page.waitForTimeout(500);

    // 点击 Next 按钮
    const nextBtn = await page.$('#identifierNext')
        || await page.$('button:has-text("Next")')
        || await page.$('button:has-text("下一步")');
    if (nextBtn) {{
        await nextBtn.click();
        await page.waitForTimeout(3000);
    }}
}}

const url = page.url();
await page.screenshot({{ path: "tmp/google_email.png" }});
console.log(JSON.stringify({{ step: "email_done", url }}));
await client.disconnect();
'''
    output = run_tsx(email_script, timeout=20)
    try:
        email_result = json.loads(output)
    except json.JSONDecodeError:
        email_result = {"step": "email_error", "raw": output}
    print(f"    邮箱填写结果: {email_result.get('step', 'unknown')}")

    # Step 2: 填写密码并点击 Next
    # 对密码中的特殊字符进行转义（反斜杠、反引号、美元符号、引号）
    escaped_password = password.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$").replace('"', '\\"')
    password_script = f'''
import {{ connect }} from "@/client.js";
const client = await connect();
const page = await client.page("sw_login");

// 等待密码输入框出现
try {{
    await page.waitForSelector('input[type="password"]', {{ timeout: 10000, state: "visible" }});
}} catch {{
    // 可能已经显示
}}

const pwInput = await page.$('input[type="password"]');
if (pwInput) {{
    await pwInput.fill("{escaped_password}");
    await page.waitForTimeout(500);

    // 点击 Next 按钮
    const nextBtn = await page.$('#passwordNext')
        || await page.$('button:has-text("Next")')
        || await page.$('button:has-text("下一步")');
    if (nextBtn) {{
        await nextBtn.click();
        // 等待较长时间，Google 登录后可能有多次跳转
        await page.waitForTimeout(8000);
    }}
}}

const url = page.url();
await page.screenshot({{ path: "tmp/google_password.png" }});
console.log(JSON.stringify({{ step: "password_done", url }}));
await client.disconnect();
'''
    output = run_tsx(password_script, timeout=30)
    try:
        pw_result = json.loads(output)
    except json.JSONDecodeError:
        pw_result = {"step": "password_error", "raw": output}
    print(f"    密码填写结果: {pw_result.get('step', 'unknown')}")
    return pw_result


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


def check_page_state():
    """检查当前页面 URL 状态"""
    script = '''
import { connect } from "@/client.js";
const client = await connect();
const page = await client.page("sw_login");
const url = page.url();
const title = await page.title();
await page.screenshot({ path: "tmp/current_state.png" });
console.log(JSON.stringify({ url, title }));
await client.disconnect();
'''
    output = run_tsx(script, timeout=15)
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return {"url": "", "title": "", "raw": output}


def login_flow():
    """完整登录流程（Google 账号登录）"""
    global DEV_BROWSER_DIR
    DEV_BROWSER_DIR = find_dev_browser_dir()
    if not DEV_BROWSER_DIR:
        print("[ERROR] 找不到 dev-browser 插件目录")
        sys.exit(1)
    print(f"[INFO] dev-browser 目录: {DEV_BROWSER_DIR}")

    # 确保 tmp 目录存在
    os.makedirs("tmp", exist_ok=True)

    # Step 1: 先检查现有 cookie 是否还有效
    if os.path.exists(COOKIE_FILE):
        print("\n[Step 1] 测试现有 cookie...")
        if verify_cookie():
            print("[OK] 现有 cookie 仍然有效，无需重新登录")
            return True
    print("[INFO] 需要重新登录")

    # Step 2: 启动浏览器
    print("\n[Step 2] 启动 dev-browser server...")
    ensure_server()

    # Step 3: 导航到 SimilarWeb 并检测状态
    print("\n[Step 3] 导航到 SimilarWeb...")
    state = navigate_to_login()
    print(f"    状态: {state.get('state', 'N/A')}")
    print(f"    URL: {state.get('url', 'N/A')}")

    page_state = state.get("state", "unknown")

    if page_state == "logged_in":
        print("\n[OK] 已经登录，跳到 cookie 提取")

    # Step 4: Google 登录
    elif page_state == "google_login":
        print("\n[Step 4] 已跳转到 Google 登录页面")
        email = input("    请输入 Google 邮箱: ").strip()
        if not email:
            print("[ERROR] 未输入邮箱")
            return False
        password = getpass.getpass("    请输入 Google 密码: ")
        if not password:
            print("[ERROR] 未输入密码")
            return False

        # Step 5: 自动填写 Google 邮箱和密码
        print("\n[Step 5] 填写 Google 登录信息...")
        result = fill_google_credentials(email, password)
        result_url = result.get("url", "")
        print(f"    登录后 URL: {result_url}")

        # Step 6: 检测 Google 登录后的状态
        print("\n[Step 6] 检测登录结果...")
        page_info = check_page_state()
        current_url = page_info.get("url", "")
        print(f"    当前 URL: {current_url}")

        # 如果还在 Google 页面，可能需要额外验证
        if "accounts.google.com" in current_url:
            print("[WARN] 仍在 Google 页面，可能需要额外验证（如两步验证）")
            print("    请在浏览器中完成 Google 验证后按回车继续...")
            input("    按回车继续...")
            page_info = check_page_state()
            current_url = page_info.get("url", "")
            print(f"    当前 URL: {current_url}")

        # Step 7: 检测是否出现 SimilarWeb 设备验证码页面
        if "device-verification" in current_url or "verify" in current_url:
            print("\n[Step 7] 检测到 SimilarWeb 设备验证页面")
            print("    请去 Gmail 查看 SimilarWeb 发送的 6 位验证码")
            code = input("    请输入 6 位验证码: ").strip()
            if not code:
                print("[ERROR] 未输入验证码")
                return False
            print(f"    填写验证码: {code}")
            verify_result = fill_verification_code(code)
            print(f"    验证后 URL: {verify_result.get('url', 'N/A')}")

    elif page_state == "verification":
        # 直接进入验证码页面（之前已有登录态但需要设备验证）
        print("\n[Step 7] 检测到 SimilarWeb 设备验证页面")
        print("    请去 Gmail 查看 SimilarWeb 发送的 6 位验证码")
        code = input("    请输入 6 位验证码: ").strip()
        if not code:
            print("[ERROR] 未输入验证码")
            return False
        print(f"    填写验证码: {code}")
        verify_result = fill_verification_code(code)
        print(f"    验证后 URL: {verify_result.get('url', 'N/A')}")

    elif page_state == "login_page":
        # Google 按钮没找到或点击失败，提示用户查看截图
        print("\n[WARN] 未能自动点击 Google 登录按钮")
        print("    请查看截图 tmp/login_state.png 了解页面状态")
        print("    请在浏览器中手动完成登录后按回车继续...")
        input("    按回车继续...")

    else:
        print(f"\n[WARN] 未知状态: {page_state}")
        print("    请查看截图 tmp/login_state.png 了解页面状态")
        print("    请在浏览器中手动完成登录后按回车继续...")
        input("    按回车继续...")

    # Step 8: 处理登录后弹窗
    print("\n[Step 8] 处理可能的弹窗...")
    handle_post_login_popups()

    # Step 9: 提取 cookie
    print("\n[Step 9] 提取 cookie...")
    cookie_info = extract_cookies()
    print(f"    Cookie 数量: {cookie_info.get('count', 'N/A')}")
    print(f"    Cookie 长度: {cookie_info.get('length', 'N/A')}")

    # Step 10: 验证
    print("\n[Step 10] 验证 cookie...")
    if verify_cookie():
        print(f"\n[SUCCESS] 登录成功，cookie 已保存到 {COOKIE_FILE}")
        return True
    else:
        print("\n[FAIL] 登录失败，请重试")
        return False


if __name__ == "__main__":
    login_flow()
