"""
SimilarWeb 数据获取 CLI
使用方法:
  python3 sw_fetch.py github.com
  python3 sw_fetch.py github.com --no-proxy
输出:
  web_data/{domain}/raw_api_data.json  — 11 个 API 的原始 JSON
  web_data/{domain}/overview.md        — 格式化的网站概览
  web_data/{domain}/referrals_incoming.csv — 外链数据 CSV
"""

import sys
import json
import os
import csv
import io

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from similarweb_api import SimilarWebAPI
from proxy_pool import ProxyPool


def format_number(n):
    """格式化数字: 1234567 -> 1.23M, 1234567890 -> 1.23B"""
    if n is None or n == 0:
        return "0"
    abs_n = abs(n)
    if abs_n >= 1e9:
        return f"{n/1e9:.2f}B"
    elif abs_n >= 1e6:
        return f"{n/1e6:.2f}M"
    elif abs_n >= 1e3:
        return f"{n/1e3:.1f}K"
    return str(int(n))


def format_duration(seconds):
    """格式化时长: 125.3 -> 2m 5s"""
    if not seconds:
        return "0s"
    m = int(seconds) // 60
    s = int(seconds) % 60
    if m > 0:
        return f"{m}m {s}s"
    return f"{s}s"


def format_percent(v, multiply=True):
    """格式化百分比"""
    if v is None:
        return "N/A"
    if multiply:
        return f"{v * 100:.1f}%"
    return f"{v:.1f}%"


def generate_overview_md(domain, data):
    """从 API JSON 数据生成 overview.md"""
    lines = []
    lines.append(f"# {domain} — SimilarWeb 网站概览")
    lines.append("")
    lines.append(f"*数据来源: SimilarWeb Pro API*")
    lines.append("")

    # === 总访问量 ===
    tv = data.get("total_visits", {})
    if "Data" in tv:
        d = tv["Data"].get(domain, {})
        visits = d.get("TotalVisits", 0)
        change = d.get("Change", 0)
        lines.append("## 总访问量")
        lines.append("")
        lines.append(f"- **总访问量**: {format_number(visits)}")
        lines.append(f"- **环比变化**: {change * 100:+.1f}%")
        lines.append("")

    # === 排名 ===
    ranks = data.get("ranks", {})
    if "Data" in ranks:
        r = ranks["Data"].get(domain, {})
        lines.append("## 排名")
        lines.append("")
        gr = r.get("GlobalRank", {})
        cr = r.get("CountryRank", {})
        cat = r.get("CategoryRank", {})
        category = r.get("Category", "")
        country_code = r.get("Country", "")
        lines.append(f"| 排名类型 | 排名 |")
        lines.append(f"|---------|------|")
        lines.append(f"| 全球排名 | #{gr.get('Value', 'N/A')} |")
        if cr.get("Value"):
            lines.append(f"| 国家排名 (Country {country_code}) | #{cr.get('Value', 'N/A')} |")
        if cat.get("Value"):
            cat_short = category.split("/")[-1].replace("_", " ") if category else ""
            lines.append(f"| 行业排名 ({cat_short}) | #{cat.get('Value', 'N/A')} |")
        lines.append("")

    # === 设备分布 ===
    ds = data.get("device_split", {})
    if "Data" in ds:
        d = ds["Data"].get(domain, {})
        desktop = d.get("Desktop", 0)
        mobile = d.get("Mobile Web", 0)
        total = desktop + mobile
        if total > 0:
            lines.append("## 设备分布")
            lines.append("")
            lines.append(f"| 设备 | 访问量 | 占比 |")
            lines.append(f"|------|--------|------|")
            lines.append(f"| Desktop | {format_number(desktop)} | {format_percent(desktop / total)} |")
            lines.append(f"| Mobile | {format_number(mobile)} | {format_percent(mobile / total)} |")
            lines.append("")

    # === 参与度 ===
    eng = data.get("engagement", {})
    if "Data" in eng and eng["Data"]:
        e = eng["Data"][0]
        lines.append("## 参与度指标")
        lines.append("")
        lines.append(f"| 指标 | 数值 |")
        lines.append(f"|------|------|")
        lines.append(f"| 跳出率 | {format_percent(e.get('BounceRate', 0))} |")
        lines.append(f"| 平均停留时间 | {format_duration(e.get('AvgVisitDuration', 0))} |")
        lines.append(f"| 平均页面数 | {e.get('PagesPerVisit', 0):.1f} |")
        lines.append(f"| 月均访问量 | {format_number(e.get('AvgMonthVisits', 0))} |")
        lines.append(f"| 独立访客 | {format_number(e.get('UniqueUsers', 0))} |")
        lines.append("")

    # === 地理分布 ===
    geo = data.get("geography", {})
    if "Data" in geo:
        geo_data = geo["Data"]
        if isinstance(geo_data, dict) and domain in geo_data:
            countries = geo_data[domain]
        elif isinstance(geo_data, list):
            countries = geo_data
        else:
            countries = []
        # Build country name lookup from Filters if available
        country_names = {}
        for f in geo.get("Filters", {}).get("country", []):
            country_names[int(f["id"])] = f["text"]
        if countries:
            lines.append("## 地理分布 (Top 5)")
            lines.append("")
            lines.append(f"| 国家 | 流量占比 | 变化 |")
            lines.append(f"|------|---------|------|")
            items = countries if isinstance(countries, list) else []
            for c in items[:5]:
                country_code = c.get("Country", "N/A")
                name = country_names.get(country_code, c.get("CountryName", str(country_code)))
                share = c.get("Share", c.get("TotalShare", 0))
                change = c.get("Change", 0)
                lines.append(f"| {name} | {format_percent(share)} | {change * 100:+.1f}% |")
            lines.append("")

    # === 流量来源 ===
    ts = data.get("traffic_sources", {})
    if "Data" in ts and "Total" in ts["Data"]:
        sources = ts["Data"]["Total"].get(domain, {})
        total = sum(sources.values())
        if total > 0:
            lines.append("## 流量来源渠道")
            lines.append("")
            lines.append(f"| 渠道 | 占比 |")
            lines.append(f"|------|------|")
            for name, val in sorted(sources.items(), key=lambda x: -x[1]):
                lines.append(f"| {name} | {format_percent(val / total)} |")
            lines.append("")

    # === 社交流量 ===
    social = data.get("social_traffic", {})
    if "Data" in social:
        sdata = social["Data"]
        if isinstance(sdata, dict) and domain in sdata:
            platforms = sdata[domain]
        elif isinstance(sdata, dict) and "Total" in sdata:
            platforms = sdata["Total"].get(domain, {})
        else:
            platforms = {}
        if platforms and isinstance(platforms, dict):
            # Values may be dicts with "Share" key or plain numbers
            shares = {}
            for name, val in platforms.items():
                if isinstance(val, dict):
                    shares[name] = val.get("Share", 0)
                else:
                    shares[name] = val
            total = sum(shares.values())
            if total > 0:
                lines.append("## 社交流量分布")
                lines.append("")
                lines.append(f"| 平台 | 占比 |")
                lines.append(f"|------|------|")
                for name, val in sorted(shares.items(), key=lambda x: -x[1]):
                    lines.append(f"| {name} | {format_percent(val / total)} |")
                lines.append("")

    # === 搜索关键词 ===
    kw = data.get("search_keywords", {})
    if "Data" in kw and kw["Data"]:
        kw_data = kw["Data"]
        lines.append("## 搜索关键词 (Top 5)")
        lines.append("")
        lines.append(f"| 关键词 | 流量占比 | 变化 |")
        lines.append(f"|--------|---------|------|")
        for item in kw_data[:5]:
            term = item.get("SearchTerm", "N/A")
            share = item.get("TotalShare", 0)
            change = item.get("Change", 0)
            lines.append(f"| {term} | {format_percent(share)} | {change * 100:+.1f}% |")
        lines.append("")

    # === 品牌 vs 非品牌 ===
    bk = data.get("branded_keywords", {})
    if "Data" in bk:
        bdata = bk["Data"]
        if isinstance(bdata, dict) and domain in bdata:
            binfo = bdata[domain]
            branded = binfo.get("Branded", 0)
            non_branded = binfo.get("NoneBranded", binfo.get("Non Branded", 0))
            total = branded + non_branded
            if total > 0:
                lines.append("## 品牌 vs 非品牌搜索")
                lines.append("")
                lines.append(f"- **品牌搜索**: {format_percent(branded / total)}")
                lines.append(f"- **非品牌搜索**: {format_percent(non_branded / total)}")
                lines.append("")

    # === 外链 Top 10 ===
    refs = data.get("top_referrals", {})
    if "Data" in refs and refs["Data"]:
        total_count = refs.get("TotalCount", len(refs["Data"]))
        lines.append(f"## 外链来源 Top 10 (共 {total_count} 条)")
        lines.append("")
        lines.append(f"| # | 域名 | 行业 | 流量占比 | 变化 |")
        lines.append(f"|---|------|------|---------|------|")
        for i, r in enumerate(refs["Data"][:10], 1):
            domain_name = r.get("Domain", "N/A")
            category = r.get("Category", "N/A")
            share = r.get("Share", 0)
            change = r.get("Change", 0)
            lines.append(f"| {i} | {domain_name} | {category} | {format_percent(share)} | {change * 100:+.1f}% |")
        lines.append("")

    # === 相似网站 ===
    similar = data.get("similar_sites", {})
    if isinstance(similar, list) and similar:
        lines.append("## 相似网站")
        lines.append("")
        for s in similar[:10]:
            if isinstance(s, dict):
                domain_name = s.get("Domain", s.get("Url", "N/A"))
                rank = s.get("Rank", "")
                rank_str = f" (#{rank})" if rank else ""
                lines.append(f"- {domain_name}{rank_str}")
            elif isinstance(s, str):
                lines.append(f"- {s}")
        lines.append("")

    return "\n".join(lines)


def generate_referrals_csv(data):
    """从 API JSON 数据生成 referrals_incoming.csv"""
    refs = data.get("top_referrals", {})
    if "Data" not in refs or not refs["Data"]:
        return ""

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["序号", "域名", "行业", "全球排名", "流量份额(%)", "变动(%)"])

    for i, r in enumerate(refs["Data"], 1):
        writer.writerow([
            i,
            r.get("Domain", ""),
            r.get("Category", ""),
            r.get("Rank", ""),
            f"{r.get('Share', 0) * 100:.4f}",
            f"{r.get('Change', 0) * 100:.2f}",
        ])

    return output.getvalue()


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("Usage: python3 sw_fetch.py <domain> [--no-proxy]")
        print("  domain     目标域名，如 github.com")
        print("  --no-proxy 不使用代理，直连请求（注意封 IP 风险）")
        sys.exit(0)

    domain = sys.argv[1]
    use_proxy = "--no-proxy" not in sys.argv

    print("=" * 60)
    print(f"SimilarWeb 数据获取 — {domain}")
    print(f"代理模式: {'开启' if use_proxy else '关闭（直连）'}")
    print("=" * 60)

    # 初始化代理
    proxy = None
    if use_proxy:
        print("\n[1/4] 提取代理 IP...")
        proxy = ProxyPool()
        proxy.extract(keep_alive=3)
        print(f"  IP: {proxy.current_ip}  地区: {proxy.current_area}  过期: {proxy.deadline}")

    # 初始化 API
    api = SimilarWebAPI(proxy_pool=proxy)

    # 验证 cookie
    step = 2 if use_proxy else 1
    total = 4 if use_proxy else 3
    print(f"\n[{step}/{total}] 验证 cookie...")
    if not api.is_cookie_valid():
        print("  [ERROR] Cookie 无效或已过期，请运行: /sw_login")
        sys.exit(1)
    print("  [OK] Cookie 有效")

    # 获取数据
    step += 1
    print(f"\n[{step}/{total}] 获取 {domain} 完整数据 (11 个 API)...")
    data = api.get_full_overview(domain)

    # 统计成功/失败
    ok_count = sum(1 for v in data.values() if "error" not in v)
    fail_count = sum(1 for v in data.values() if "error" in v)
    print(f"\n  结果: {ok_count} 成功, {fail_count} 失败")

    # 保存文件
    step += 1
    print(f"\n[{step}/{total}] 保存数据文件...")

    output_dir = f"web_data/{domain}"
    os.makedirs(output_dir, exist_ok=True)

    # 1. 原始 JSON
    raw_file = f"{output_dir}/raw_api_data.json"
    with open(raw_file, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  [OK] {raw_file}")

    # 2. overview.md
    overview_md = generate_overview_md(domain, data)
    overview_file = f"{output_dir}/overview.md"
    with open(overview_file, "w") as f:
        f.write(overview_md)
    print(f"  [OK] {overview_file}")

    # 3. referrals CSV
    referrals_csv = generate_referrals_csv(data)
    if referrals_csv:
        csv_file = f"{output_dir}/referrals_incoming.csv"
        with open(csv_file, "w") as f:
            f.write(referrals_csv)
        refs_count = data.get("top_referrals", {}).get("TotalCount", 0)
        print(f"  [OK] {csv_file} ({refs_count} 条记录)")

    # 汇报
    print(f"\n{'=' * 60}")
    print(f"完成！数据已保存到 {output_dir}/")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
