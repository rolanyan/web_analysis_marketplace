"""
SimilarWeb API 封装
- 加载 cookie
- 调用各类数据 API
- 支持可选代理
- 自动重试 SSL 错误
"""

import requests
import os
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

SW_BASE = "https://pro.similarweb.com"

SW_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/143.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json; charset=utf-8",
    "Referer": "https://pro.similarweb.com/",
    "x-requested-with": "XMLHttpRequest",
    "sec-ch-ua": '"Chromium";v="143", "Not A(Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
}


class SimilarWebAPI:
    def __init__(self, cookie_file=None, proxy_pool=None):
        if not cookie_file:
            cookie_file = os.environ.get("SW_COOKIE_FILE")
            if not cookie_file:
                raise RuntimeError(
                    "环境变量 SW_COOKIE_FILE 未设置。请在 ~/.claude/.env 或 shell profile 中配置。\n"
                    "详见插件 README.md 的「环境变量配置」章节。"
                )
        self.cookie_file = cookie_file
        self.proxy_pool = proxy_pool
        self._cookie_str = None

    def _load_cookie(self):
        if self._cookie_str:
            return self._cookie_str
        if not os.path.exists(self.cookie_file):
            raise FileNotFoundError(f"Cookie 文件不存在: {self.cookie_file}，请先运行 /sw_login")
        with open(self.cookie_file, "r") as f:
            self._cookie_str = f.read().strip()
        return self._cookie_str

    def _build_headers(self, domain="example.com"):
        cookie = self._load_cookie()
        return {
            **SW_HEADERS,
            "Cookie": cookie,
            "x-sw-page": f"https://pro.similarweb.com/#/digitalsuite/websiteanalysis/"
                         f"overview/website-performance/*/999/3m?webSource=Total&key={domain}",
        }

    def _request(self, path, params, domain="example.com", max_retries=3):
        """发起 API 请求，自动重试 SSL 错误和代理 403"""
        url = f"{SW_BASE}{path}"
        headers = self._build_headers(domain)
        proxies = self.proxy_pool.get_proxies_dict() if self.proxy_pool else None

        for attempt in range(max_retries):
            try:
                resp = requests.get(
                    url, params=params, headers=headers,
                    proxies=proxies, timeout=30,
                )
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 403:
                    if self.proxy_pool and attempt < max_retries - 1:
                        area = self.proxy_pool.current_area
                        print(f"    [403] 代理 IP 被拦截 (地区: {area})，换 IP 重试...")
                        self.proxy_pool.extract(keep_alive=3)
                        proxies = self.proxy_pool.get_proxies_dict()
                        print(f"    [换 IP] {self.proxy_pool.current_ip} ({self.proxy_pool.current_area})")
                        continue
                    raise PermissionError("403 Forbidden — cookie 可能已过期或代理 IP 不可用")
                else:
                    raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:200]}")
            except (requests.exceptions.SSLError, requests.exceptions.ConnectionError) as e:
                if self.proxy_pool and attempt < max_retries - 1:
                    print(f"    [连接错误] {e.__class__.__name__}，换 IP 重试...")
                    try:
                        self.proxy_pool.extract(keep_alive=3)
                        proxies = self.proxy_pool.get_proxies_dict()
                        print(f"    [换 IP] {self.proxy_pool.current_ip} ({self.proxy_pool.current_area})")
                    except RuntimeError:
                        time.sleep(2)
                    continue
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    raise RuntimeError(f"连接失败（已重试 {max_retries} 次）: {e}")

    def _default_params(self, domain, from_date="2025|11|01", to_date="2026|01|31"):
        return {
            "country": "999",
            "from": from_date,
            "to": to_date,
            "includeSubDomains": "true",
            "isWindow": "false",
            "keys": domain,
            "timeGranularity": "Monthly",
            "webSource": "Total",
        }

    # ======== 数据 API ========

    def get_total_visits(self, domain, **kwargs):
        """总访问量、变化趋势"""
        params = {**self._default_params(domain, **kwargs), "ShouldGetVerifiedData": "false"}
        return self._request(
            "/widgetApi/WebsiteOverview/EngagementVisits/SingleMetric",
            params, domain,
        )

    def get_ranks(self, domain, **kwargs):
        """全球排名、国家排名、行业排名"""
        params = self._default_params(domain, **kwargs)
        return self._request(
            "/widgetApi/WebsiteOverview/WebRanks/SingleMetric",
            params, domain,
        )

    def get_device_split(self, domain, **kwargs):
        """设备分布（Desktop vs Mobile）"""
        params = {**self._default_params(domain, **kwargs), "ShouldGetVerifiedData": "false"}
        return self._request(
            "/widgetApi/WebsiteOverview/EngagementDesktopVsMobileVisits/PieChart",
            params, domain,
        )

    def get_engagement(self, domain, **kwargs):
        """参与度（跳出率、停留时间、页面数等）"""
        params = {
            **self._default_params(domain, **kwargs),
            "ShouldGetVerifiedData": "false",
            "ignoreFilterConsistency": "false",
            "iso": "[object Object]",
        }
        return self._request(
            "/widgetApi/WebsiteOverview/EngagementOverview/Table",
            params, domain,
        )

    def get_geography(self, domain, page_size=5, **kwargs):
        """地理分布"""
        params = {
            **self._default_params(domain, **kwargs),
            "orderBy": "TotalShare desc",
            "pageSize": str(page_size),
        }
        return self._request(
            "/widgetApi/WebsiteGeography/Geography/Table",
            params, domain,
        )

    def get_traffic_sources(self, domain, **kwargs):
        """流量来源渠道占比"""
        params = self._default_params(domain, **kwargs)
        return self._request(
            "/widgetApi/MarketingMixTotal/TrafficSourcesOverview/PieChart",
            params, domain,
        )

    def get_top_referrals(self, domain, page_size=100, **kwargs):
        """外链来源"""
        params = {
            **self._default_params(domain, **kwargs),
            "pageSize": str(page_size),
            "webSource": "Desktop",
            "orderBy": "TotalShare desc",
        }
        return self._request(
            "/widgetApi/WebsiteOverviewDesktop/TopReferrals/Table",
            params, domain,
        )

    def get_social_traffic(self, domain, **kwargs):
        """社交流量分布"""
        params = {
            **self._default_params(domain, **kwargs),
            "webSource": "Desktop",
        }
        return self._request(
            "/widgetApi/WebsiteOverviewDesktop/TrafficSourcesSocial/PieChart",
            params, domain,
        )

    def get_search_keywords(self, domain, source_type="Organic", page_size=5, **kwargs):
        """搜索关键词"""
        params = {
            **self._default_params(domain, **kwargs),
            "SourceType": source_type,
            "pageSize": str(page_size),
            "duration": "1m",
        }
        return self._request(
            "/widgetApi/SearchKeywordsV2/WebsitePerformance/Table",
            params, domain,
        )

    def get_branded_keywords(self, domain, **kwargs):
        """品牌 vs 非品牌搜索"""
        params = {**self._default_params(domain, **kwargs), "duration": "1m"}
        return self._request(
            "/widgetApi/TrafficSourcesSearchV2/BrandedKeywords/WebsitePerformance/PieChart",
            params, domain,
        )

    def get_similar_sites(self, domain, limit=20):
        """相似网站"""
        params = {"key": domain, "limit": str(limit), "country": "999", "webSource": "Total"}
        return self._request(
            "/api/WebsiteOverview/getsimilarsites",
            params, domain,
        )

    # ======== 便捷方法 ========

    def get_full_overview(self, domain, **kwargs):
        """获取完整概览数据（一次性调用所有 API）"""
        results = {}
        apis = [
            ("total_visits", self.get_total_visits),
            ("ranks", self.get_ranks),
            ("device_split", self.get_device_split),
            ("engagement", self.get_engagement),
            ("geography", self.get_geography),
            ("traffic_sources", self.get_traffic_sources),
            ("top_referrals", self.get_top_referrals),
            ("social_traffic", self.get_social_traffic),
            ("search_keywords", self.get_search_keywords),
            ("branded_keywords", self.get_branded_keywords),
            ("similar_sites", self.get_similar_sites),
        ]
        for name, func in apis:
            try:
                results[name] = func(domain, **kwargs) if name != "similar_sites" else func(domain)
                print(f"  [OK] {name}")
            except Exception as e:
                results[name] = {"error": str(e)}
                print(f"  [FAIL] {name}: {e}")
        return results

    def is_cookie_valid(self):
        """检查 cookie 是否有效"""
        try:
            headers = self._build_headers()
            resp = requests.get(
                f"{SW_BASE}/api/identities",
                headers=headers, timeout=15,
            )
            return resp.status_code == 200 and resp.json()
        except Exception:
            return False
