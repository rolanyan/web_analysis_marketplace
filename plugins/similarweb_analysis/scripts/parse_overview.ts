/**
 * 解析 SimilarWeb Pro 网站表现页的原始文本为 Markdown 格式。
 * 用法: npx tsx parse_overview.ts <domain> <raw_text_file> <output_dir>
 * 输出: 写入 {output_dir}/overview.md
 *
 * 必须从 dev-browser skill 目录运行。
 */

import * as fs from "fs";
import * as path from "path";

const domain = process.argv[2];
const rawTextFile = process.argv[3];
const outputDir = process.argv[4];

if (!domain || !rawTextFile || !outputDir) {
  console.error("Usage: npx tsx parse_overview.ts <domain> <raw_text_file> <output_dir>");
  process.exit(1);
}

const rawText = fs.readFileSync(rawTextFile, "utf-8");
const lines = rawText.split("\n").map((l) => l.trim()).filter((l) => l.length > 0);

// ========== 辅助函数 ==========

/** 在 lines 中查找包含 keyword 的行的索引 */
function findLine(keyword: string, startFrom = 0): number {
  for (let i = startFrom; i < lines.length; i++) {
    if (lines[i].includes(keyword)) return i;
  }
  return -1;
}

/** 在 lines 中查找精确匹配 keyword 的行的索引 */
function findExactLine(keyword: string, startFrom = 0): number {
  for (let i = startFrom; i < lines.length; i++) {
    if (lines[i] === keyword) return i;
  }
  return -1;
}

/** 在某行之后的 N 行内查找匹配正则的值 */
function findValueAfter(anchorIdx: number, pattern: RegExp, range = 5): string {
  if (anchorIdx < 0) return "-";
  for (let i = anchorIdx + 1; i < Math.min(anchorIdx + range + 1, lines.length); i++) {
    const m = lines[i].match(pattern);
    if (m) return m[0];
  }
  return "-";
}

/** 提取带数值后缀的数字（如 1.530B, 510.3M, 123.6K） */
const numPattern = /[\d,.]+[BMK]?/;

/** 提取百分比 */
const pctPattern = /[\d,.]+%/;

/** 提取排名 */
const rankPattern = /#[\d,]+/;

// ========== 提取数据 ==========

// --- 网站简介 ---
let siteDescription = "-";
const descIdx = findLine("Join ") !== -1 ? findLine("Join ") : findLine(domain);
if (descIdx >= 0) {
  // 找到较长的描述行
  for (let i = Math.max(0, descIdx - 2); i < Math.min(descIdx + 5, lines.length); i++) {
    if (lines[i].length > 50 && !lines[i].includes("SimilarWeb") && !lines[i].startsWith("#")) {
      siteDescription = lines[i];
      break;
    }
  }
}

// --- 总访问量 ---
const totalVisitsIdx = findExactLine("总访问量");
let totalVisits = "-";
let totalVisitsChange = "-";
let timeRange = "-";
if (totalVisitsIdx >= 0) {
  // 时间范围通常在总访问量之后
  for (let i = totalVisitsIdx + 1; i < totalVisitsIdx + 5 && i < lines.length; i++) {
    if (lines[i].match(/[A-Z][a-z]{2}\s+\d{4}\s*-\s*[A-Z][a-z]{2}\s+\d{4}/)) {
      timeRange = lines[i];
    }
    const numMatch = lines[i].match(/^([\d,.]+[BMK])$/);
    if (numMatch) totalVisits = numMatch[1];
    const changeMatch = lines[i].match(/([+-]?[\d,.]+%)\s*自上个月/);
    if (changeMatch) totalVisitsChange = changeMatch[1];
  }
}

// --- 设备分布 ---
let desktopPct = "-";
let mobilePct = "-";
const desktopIdx = findLine("Desktop");
if (desktopIdx >= 0) {
  const dm = lines[desktopIdx].match(/([\d.]+%)/);
  if (dm) desktopPct = dm[1];
}
const mobileIdx = findLine("Mobile Web");
if (mobileIdx >= 0) {
  const mm = lines[mobileIdx].match(/([\d.]+%)/);
  if (mm) mobilePct = mm[1];
}

// --- 排名 ---
let globalRank = "-";
let countryRank = "-";
let countryName = "-";
let industryRank = "-";
let industryName = "-";

const globalRankIdx = findLine("全球排名");
if (globalRankIdx >= 0) {
  const rm = lines[globalRankIdx].match(/#([\d,]+)/);
  if (rm) globalRank = `#${rm[1]}`;
}

const countryRankIdx = findLine("国家/地区排名");
if (countryRankIdx >= 0) {
  const line = lines[countryRankIdx];
  // 格式: "国家/地区排名 美国 #82" 或在后续行
  const cm = line.match(/国家\/地区排名\s+(.+?)\s+#([\d,]+)/);
  if (cm) {
    countryName = cm[1];
    countryRank = `#${cm[2]}`;
  } else {
    const rm = line.match(/#([\d,]+)/);
    if (rm) countryRank = `#${rm[1]}`;
    const nm = line.replace(/国家\/地区排名/, "").replace(/#[\d,]+/, "").trim();
    if (nm) countryName = nm;
  }
}

const industryRankIdx = findLine("行业排名");
if (industryRankIdx >= 0) {
  const line = lines[industryRankIdx];
  const im = line.match(/#([\d,]+)/);
  if (im) industryRank = `#${im[1]}`;
  // 提取行业名 — 在 / 之后的部分
  const indMatch = line.match(/\/\s*(.+?)\s+#/);
  if (indMatch) {
    industryName = indMatch[1];
  } else {
    const nameMatch = line.replace(/行业排名/, "").replace(/#[\d,]+/, "").replace(/.*\//, "").trim();
    if (nameMatch) industryName = nameMatch;
  }
}

// --- 参与度概览 ---
const engagementIdx = findExactLine("参与度概览");

let monthlyVisits = "-";
let uniqueVisitors = "-";
let dedupedAudience = "-";
let visitDuration = "-";
let pagesPerVisit = "-";
let bounceRate = "-";

if (engagementIdx >= 0) {
  const mvIdx = findLine("每月访问量", engagementIdx);
  if (mvIdx >= 0) monthlyVisits = findValueAfter(mvIdx, numPattern);

  const uvIdx = findLine("月独立访客数", engagementIdx);
  if (uvIdx >= 0) uniqueVisitors = findValueAfter(uvIdx, numPattern);

  const daIdx = findLine("已消除重叠的受众", engagementIdx);
  if (daIdx >= 0) dedupedAudience = findValueAfter(daIdx, numPattern);

  const durIdx = findLine("访问持续时间", engagementIdx);
  if (durIdx >= 0) visitDuration = findValueAfter(durIdx, /\d{2}:\d{2}:\d{2}/);

  const ppvIdx = findLine("页面数/访问", engagementIdx);
  if (ppvIdx >= 0) pagesPerVisit = findValueAfter(ppvIdx, /[\d.]+/);

  const brIdx = findLine("跳出率", engagementIdx);
  if (brIdx >= 0) bounceRate = findValueAfter(brIdx, pctPattern);
}

// --- 竞对对比 ---
interface CompetitorEntry {
  site: string;
  visits: string;
}
const competitors: CompetitorEntry[] = [];
const compIdx = findLine("随着时间的访问");
if (compIdx >= 0) {
  // 竞对数据通常在后续行，每个网站一行数值
  for (let i = compIdx + 1; i < Math.min(compIdx + 30, lines.length); i++) {
    if (lines[i].match(/^[\w.-]+\.\w{2,}$/)) {
      // 域名行
      const nextVal = findValueAfter(i, numPattern, 2);
      competitors.push({ site: lines[i], visits: nextVal });
    }
    // 停止条件
    if (lines[i] === "地理分布" || lines[i].includes("热门国家")) break;
  }
}

// --- 地理分布 ---
interface GeoEntry {
  country: string;
  share: string;
  change: string;
}
const geoData: GeoEntry[] = [];
const geoIdx = findLine("热门国家/地区");
if (geoIdx >= 0) {
  for (let i = geoIdx + 1; i < Math.min(geoIdx + 30, lines.length); i++) {
    // 查找包含百分比的行
    const shareMatch = lines[i].match(/([\d.]+%)/g);
    if (shareMatch && shareMatch.length >= 1) {
      // 国家名在前一行或同一行开头
      const countryLine = lines[i - 1] && !lines[i - 1].match(/[\d.]+%/) ? lines[i - 1] : "";
      if (countryLine && countryLine.length < 30) {
        geoData.push({
          country: countryLine,
          share: shareMatch[0],
          change: shareMatch.length > 1 ? `+${shareMatch[1]}` : "-",
        });
      }
    }
    if (geoData.length >= 5) break;
    if (lines[i] === "流量来源" || lines[i].includes("渠道概况")) break;
  }
}

// --- 流量来源渠道 ---
interface ChannelEntry {
  name: string;
  share: string;
}
const channels: ChannelEntry[] = [];
const channelNames = ["直接", "有机搜索", "付费搜索", "外链", "显示广告", "社交", "电子邮件"];
for (const ch of channelNames) {
  const chIdx = findLine(ch);
  if (chIdx >= 0) {
    const pm = lines[chIdx].match(/([\d.]+%)/);
    if (pm) {
      channels.push({ name: ch, share: pm[1] });
    } else {
      const nextPct = findValueAfter(chIdx, pctPattern, 2);
      channels.push({ name: ch, share: nextPct });
    }
  }
}

// --- 自然搜索 ---
let organicShare = "-";
let brandShare = "-";
let nonBrandShare = "-";
const organicIdx = findLine("自然搜索");
if (organicIdx >= 0) {
  for (let i = organicIdx; i < Math.min(organicIdx + 10, lines.length); i++) {
    if (lines[i].includes("品牌") && !lines[i].includes("非品牌")) {
      const pm = lines[i].match(/([\d.]+%)/);
      if (pm) brandShare = pm[1];
    }
    if (lines[i].includes("非品牌")) {
      const pm = lines[i].match(/([\d.]+%)/);
      if (pm) nonBrandShare = pm[1];
    }
  }
  // organic share from channels
  const orgCh = channels.find((c) => c.name === "有机搜索");
  if (orgCh) organicShare = orgCh.share;
}

// --- 热门搜索词 ---
interface SearchTerm {
  term: string;
  share: string;
  change: string;
}
const organicTerms: SearchTerm[] = [];
const organicTermIdx = findLine("热门自然非品牌搜索词");
if (organicTermIdx < 0) {
  // fallback: 查找 "热门有机关键词"
  const altIdx = findLine("热门有机关键词");
  if (altIdx >= 0) {
    // parse from altIdx
  }
}
if (organicTermIdx >= 0) {
  for (let i = organicTermIdx + 1; i < Math.min(organicTermIdx + 30, lines.length); i++) {
    // 搜索词通常是单独一行，后面跟着百分比
    if (lines[i].match(/^[\w\s/-]+$/) && lines[i].length < 50 && !lines[i].match(/^\d/) && !lines[i].includes("热门") && !lines[i].includes("付费")) {
      const term = lines[i];
      const nextShare = findValueAfter(i, pctPattern, 2);
      const nextChange = i + 2 < lines.length ? (lines[i + 2].match(/([+-]?[\d,.]+%)/) || ["-"])[0] : "-";
      if (nextShare !== "-") {
        organicTerms.push({ term, share: nextShare, change: nextChange });
      }
    }
    if (organicTerms.length >= 5) break;
    if (lines[i] === "付费搜索" || lines[i].includes("付费搜索")) break;
  }
}

// --- 外链 Top 5 ---
interface ReferralEntry {
  domain: string;
  share: string;
  change: string;
}
const topReferrals: ReferralEntry[] = [];
const refIdx = findLine("热门外链网站");
if (refIdx >= 0) {
  for (let i = refIdx + 1; i < Math.min(refIdx + 30, lines.length); i++) {
    if (lines[i].match(/^[\w.-]+\.\w{2,}$/)) {
      const d = lines[i];
      const share = findValueAfter(i, pctPattern, 2);
      const change = i + 2 < lines.length ? (lines[i + 2].match(/([+-]?[\d,.]+%)/) || ["-"])[0] : "-";
      topReferrals.push({ domain: d, share, change });
    }
    if (topReferrals.length >= 5) break;
    if (lines[i].includes("热门外链行业")) break;
  }
}

// --- 热门外链行业 ---
interface RefIndustryEntry {
  category: string;
  share: string;
}
const refIndustries: RefIndustryEntry[] = [];
const refIndIdx = findLine("热门外链行业");
if (refIndIdx >= 0) {
  for (let i = refIndIdx + 1; i < Math.min(refIndIdx + 30, lines.length); i++) {
    const pm = lines[i].match(/([\d.]+%)/);
    if (pm && lines[i - 1] && !lines[i - 1].match(/[\d.]+%/)) {
      refIndustries.push({ category: lines[i - 1], share: pm[1] });
    }
    if (refIndustries.length >= 5) break;
    if (lines[i] === "出站流量" || lines[i].includes("出站")) break;
  }
}

// --- 社交流量 ---
interface SocialEntry {
  platform: string;
  share: string;
}
const socialData: SocialEntry[] = [];
const socialIdx = findLine("社交流量");
if (socialIdx >= 0) {
  const socialNames = ["Youtube", "X (Twitter)", "Twitter", "Linkedin", "Reddit", "Facebook", "WhatsApp", "Instagram"];
  for (let i = socialIdx; i < Math.min(socialIdx + 20, lines.length); i++) {
    for (const sn of socialNames) {
      if (lines[i].includes(sn)) {
        const pm = lines[i].match(/([\d.]+%)/);
        if (pm) {
          socialData.push({ platform: sn, share: pm[1] });
        } else {
          const nextPct = findValueAfter(i, pctPattern, 2);
          if (nextPct !== "-") socialData.push({ platform: sn, share: nextPct });
        }
      }
    }
    if (lines[i] === "显示广告" || lines[i].includes("显示广告")) break;
  }
}

// --- 显示广告 ---
interface DisplayAdEntry {
  publisher: string;
  share: string;
  change: string;
}
const displayAds: DisplayAdEntry[] = [];
const displayIdx = findLine("热门媒体");
if (displayIdx >= 0) {
  for (let i = displayIdx + 1; i < Math.min(displayIdx + 30, lines.length); i++) {
    if (lines[i].match(/^[\w.-]+\.\w{2,}$/)) {
      const d = lines[i];
      const share = findValueAfter(i, pctPattern, 2);
      const change = i + 2 < lines.length ? (lines[i + 2].match(/([+-]?[\d,.]+%|>[\d,]+%|-)/) || ["-"])[0] : "-";
      displayAds.push({ publisher: d, share, change });
    }
    if (displayAds.length >= 5) break;
  }
}

// ========== 生成 Markdown ==========

let md = `# ${domain} 网站表现概览\n\n`;
md += `> 数据来源：SimilarWeb | 时间范围：${timeRange} (3个月) | 范围：全球\n\n`;

md += `## 网站简介\n\n**${domain}**\n\n`;
if (siteDescription !== "-") md += `${siteDescription}\n\n`;
md += `---\n\n`;

// 流量与互动
md += `## 流量与互动\n\n`;
md += `| 指标 | 数值 |\n|------|------|\n`;
md += `| 总访问量 | ${totalVisits} |\n`;
md += `| 环比变化 | ${totalVisitsChange} |\n`;
md += `| Desktop | ${desktopPct} |\n`;
md += `| Mobile Web | ${mobilePct} |\n\n`;

md += `### 排名\n\n`;
md += `| 排名类型 | 排名 |\n|----------|------|\n`;
md += `| 全球排名 | ${globalRank} |\n`;
md += `| 国家/地区排名（${countryName}） | ${countryRank} |\n`;
md += `| 行业排名（${industryName}） | ${industryRank} |\n\n`;
md += `---\n\n`;

// 参与度
md += `## 参与度概览\n\n`;
md += `> 时间范围：${timeRange} | 全球 | All Traffic\n\n`;
md += `| 指标 | 数值 |\n|------|------|\n`;
md += `| 每月访问量 | ${monthlyVisits} |\n`;
md += `| 月独立访客数 | ${uniqueVisitors} |\n`;
md += `| 已消除重叠的受众 | ${dedupedAudience} |\n`;
md += `| 访问持续时间 | ${visitDuration} |\n`;
md += `| 页面数/访问 | ${pagesPerVisit} |\n`;
md += `| 跳出率 | ${bounceRate} |\n\n`;
md += `---\n\n`;

// 竞对对比
if (competitors.length > 0) {
  md += `## 随着时间的访问（竞对对比）\n\n`;
  md += `| 网站 | 总访问量 |\n|------|----------|\n`;
  for (const c of competitors) {
    md += `| ${c.site} | ${c.visits} |\n`;
  }
  md += `\n---\n\n`;
}

// 地理分布
if (geoData.length > 0) {
  md += `## 地理分布 - 热门国家/地区\n\n`;
  md += `| 国家/地区 | 流量份额 | 变动 |\n|-----------|----------|------|\n`;
  for (const g of geoData) {
    md += `| ${g.country} | ${g.share} | ${g.change} |\n`;
  }
  md += `\n---\n\n`;
}

// 流量来源渠道
if (channels.length > 0) {
  md += `## 流量来源渠道概况\n\n`;
  md += `| 渠道 | 流量占比 |\n|------|----------|\n`;
  for (const ch of channels) {
    md += `| ${ch.name} | ${ch.share} |\n`;
  }
  md += `\n---\n\n`;
}

// 自然搜索
md += `## 自然搜索\n\n`;
md += `- 自然搜索构成网站流量的 **${organicShare}**\n`;
if (brandShare !== "-") md += `- 品牌搜索占比：**${brandShare}**\n`;
if (nonBrandShare !== "-") md += `- 非品牌搜索占比：**${nonBrandShare}**\n`;
md += `\n`;

if (organicTerms.length > 0) {
  md += `### 热门自然非品牌搜索词\n\n`;
  md += `| 搜索词 | 占比 | 变动 |\n|--------|------|------|\n`;
  for (const t of organicTerms) {
    md += `| ${t.term} | ${t.share} | ${t.change} |\n`;
  }
  md += `\n`;
}
md += `---\n\n`;

// 外链
if (topReferrals.length > 0) {
  md += `## 外链\n\n`;
  const refCh = channels.find((c) => c.name === "外链");
  if (refCh) md += `- 外链流量构成网站流量的 **${refCh.share}**\n\n`;
  md += `### 热门外链网站（桌面端）\n\n`;
  md += `| 域 | 共享 | 变动 |\n|----|------|------|\n`;
  for (const r of topReferrals) {
    md += `| ${r.domain} | ${r.share} | ${r.change} |\n`;
  }
  md += `\n`;
}

if (refIndustries.length > 0) {
  md += `### 热门外链行业（桌面端）\n\n`;
  md += `| 网站类别 | 流量份额 |\n|----------|----------|\n`;
  for (const ri of refIndustries) {
    md += `| ${ri.category} | ${ri.share} |\n`;
  }
  md += `\n---\n\n`;
}

// 社交流量
if (socialData.length > 0) {
  md += `## 社交流量\n\n`;
  const socialCh = channels.find((c) => c.name === "社交");
  if (socialCh) md += `- 社交流量构成网站流量的 **${socialCh.share}**\n\n`;
  md += `| 社交平台 | 占比 |\n|----------|------|\n`;
  for (const s of socialData) {
    md += `| ${s.platform} | ${s.share} |\n`;
  }
  md += `\n---\n\n`;
}

// 显示广告
if (displayAds.length > 0) {
  md += `## 显示广告\n\n`;
  const displayCh = channels.find((c) => c.name === "显示广告");
  if (displayCh) md += `- 展示型广告构成网站流量的 **${displayCh.share}**\n\n`;
  md += `### 热门媒体（发布商）\n\n`;
  md += `| 发布商 | 共享 | 变动 |\n|--------|------|------|\n`;
  for (const d of displayAds) {
    md += `| ${d.publisher} | ${d.share} | ${d.change} |\n`;
  }
  md += `\n`;
}

// 写入文件
const outputPath = path.join(outputDir, "overview.md");
fs.writeFileSync(outputPath, md, "utf-8");
console.log(`overview.md written to ${outputPath}`);
console.log(`Total visits: ${totalVisits}, Global rank: ${globalRank}`);
