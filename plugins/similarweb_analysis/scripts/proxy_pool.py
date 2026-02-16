"""
青云短效代理 IP 池管理
- 提取代理 IP
- 构造代理 URL
- 自动重试和通道管理

需要设置环境变量:
  PROXY_API_URL  — 代理 API 地址（默认 https://overseas.proxy.qg.net/get）
  PROXY_KEY      — 代理产品 key
  PROXY_AUTH_KEY — 代理认证 AuthKey
  PROXY_AUTH_PWD — 代理认证 AuthPwd
"""

import requests
import time
import os

PROXY_API = os.environ.get("PROXY_API_URL", "https://overseas.proxy.qg.net/get")


def _require_env(name):
    val = os.environ.get(name)
    if not val:
        raise RuntimeError(
            f"环境变量 {name} 未设置。请在 ~/.claude/.env 或 shell profile 中配置。\n"
            f"详见插件 README.md 的「环境变量配置」章节。"
        )
    return val


class ProxyPool:
    def __init__(self, key=None, auth_key=None, auth_pwd=None):
        self.key = key or _require_env("PROXY_KEY")
        self.auth_key = auth_key or _require_env("PROXY_AUTH_KEY")
        self.auth_pwd = auth_pwd or _require_env("PROXY_AUTH_PWD")
        self._current = None  # {"server": ..., "proxy_ip": ..., "deadline": ...}

    def extract(self, num=1, keep_alive=3, max_retries=3, retry_interval=30):
        """提取代理 IP，自动重试通道占用"""
        params = {
            "key": self.key,
            "num": num,
            "format": "json",
            "distinct": "false",
            "keep_alive": keep_alive,
            "isp": 0,
        }
        for attempt in range(max_retries):
            try:
                resp = requests.get(PROXY_API, params=params, timeout=10)
                data = resp.json()
                if data.get("code") == "SUCCESS":
                    self._current = data["data"][0]
                    return self._current
                elif data.get("code") in ("NO_AVAILABLE_CHANNEL", "FAILED_OPERATION"):
                    if attempt < max_retries - 1:
                        print(f"[proxy] {data.get('code')}，{retry_interval}s 后重试 ({attempt+1}/{max_retries})")
                        time.sleep(retry_interval)
                    else:
                        raise RuntimeError(f"代理不可用，已重试 {max_retries} 次: {data.get('code')}")
                else:
                    raise RuntimeError(f"代理提取失败: {data.get('code')} - {data.get('message', '')}")
            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(5)
                else:
                    raise RuntimeError(f"代理 API 请求异常: {e}")
        return None

    def get_proxy_url(self):
        """获取当前代理的 URL（带认证），如果没有则自动提取"""
        if not self._current:
            self.extract()
        if not self._current:
            raise RuntimeError("无法获取代理 IP")
        return f"http://{self.auth_key}:{self.auth_pwd}@{self._current['server']}"

    def get_proxies_dict(self):
        """获取 requests 库需要的 proxies 字典"""
        url = self.get_proxy_url()
        return {"http": url, "https": url}

    @property
    def current_ip(self):
        return self._current["proxy_ip"] if self._current else None

    @property
    def current_area(self):
        return self._current.get("area", "N/A") if self._current else None

    @property
    def deadline(self):
        return self._current.get("deadline", "N/A") if self._current else None
