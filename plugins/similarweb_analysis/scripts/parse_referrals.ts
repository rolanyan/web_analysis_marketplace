/**
 * 解析 SimilarWeb Pro 外链页面的原始文本为 CSV 格式。
 * 用法: npx tsx parse_referrals.ts <domain> <raw_text_file> <output_dir>
 * 输出: 写入 {output_dir}/referrals_incoming.csv
 *
 * 必须从 dev-browser skill 目录运行。
 *
 * 外链页面的 innerText 表格数据以分离列块呈现：
 * - 先是序号行（"1 2 3 ... 100"）
 * - 然后是域名列（每行一个域名，可能带 (N) 后缀）
 * - 行业列
 * - 排名列（#数字 或 -）
 * - 流量份额列（绝对值行 + 百分比行 交替）
 * - 变动列（百分比）
 */

import * as fs from "fs";
import * as path from "path";

const domain = process.argv[2];
const rawTextFile = process.argv[3];
const outputDir = process.argv[4];

if (!domain || !rawTextFile || !outputDir) {
  console.error("Usage: npx tsx parse_referrals.ts <domain> <raw_text_file> <output_dir>");
  process.exit(1);
}

const rawText = fs.readFileSync(rawTextFile, "utf-8");
const lines = rawText.split("\n").map((l) => l.trim()).filter((l) => l.length > 0);

// ========== 定位表格区域 ==========

// 查找表头 "域" 行（标记表格开始）
let tableStartIdx = -1;
for (let i = 0; i < lines.length; i++) {
  // "域 (N,NNN)" 或 "域"
  if (lines[i].match(/^域\s*(\([\d,]+\))?$/)) {
    tableStartIdx = i;
    break;
  }
}

if (tableStartIdx < 0) {
  console.error("ERROR: Could not find table header '域' in raw text.");
  process.exit(1);
}

// 查找序号行（"1 2 3 ... 100" 或包含连续数字）
let seqIdx = -1;
for (let i = tableStartIdx; i < Math.min(tableStartIdx + 20, lines.length); i++) {
  if (lines[i].match(/^1\s+2\s+3/)) {
    seqIdx = i;
    break;
  }
}

// 域名列开始位置
const domainStartIdx = seqIdx >= 0 ? seqIdx + 1 : tableStartIdx + 7; // fallback

// ========== 提取域名列表 ==========

const domainPattern = /^[\w][\w.-]*\.\w{2,}(\(\d+\))?$/;
const domains: string[] = [];
let domainEndIdx = domainStartIdx;

for (let i = domainStartIdx; i < lines.length; i++) {
  // 清理域名后缀 (如 "nexusmods.com(2)" → "nexusmods.com")
  const cleaned = lines[i].replace(/\(\d+\)$/, "");
  if (cleaned.match(domainPattern)) {
    domains.push(cleaned);
    domainEndIdx = i + 1;
  } else if (domains.length > 0) {
    // 碰到非域名行，检查是否还有更多域名（可能有空行等）
    // 如果连续 3 行非域名，停止
    let nonDomainCount = 0;
    for (let j = i; j < Math.min(i + 3, lines.length); j++) {
      if (!lines[j].replace(/\(\d+\)$/, "").match(domainPattern)) nonDomainCount++;
    }
    if (nonDomainCount >= 3) {
      domainEndIdx = i;
      break;
    }
  }
}

if (domains.length === 0) {
  console.error("ERROR: No domains found in the table.");
  process.exit(1);
}

const count = domains.length;

// ========== 提取行业列表 ==========

// 行业紧跟在域名列表之后，是非域名、非排名的文本
const industries: string[] = [];
let industryStartIdx = domainEndIdx;

// 跳过可能的空行或序号
for (let i = industryStartIdx; i < lines.length; i++) {
  const line = lines[i];
  // 行业名不是域名、不是排名(#xxx)、不是纯数字、不是百分比
  if (
    !line.match(domainPattern) &&
    !line.match(/^#[\d,]+$/) &&
    !line.match(/^-$/) &&
    !line.match(/^[\d,.]+[BMK]?$/) &&
    !line.match(/^[\d,.]+%$/) &&
    !line.match(/^[+-]?\s*[\d,.]+%$/) &&
    line.length > 1 &&
    line.length < 100
  ) {
    industries.push(line);
    if (industries.length >= count) break;
  } else if (industries.length > 0 && (line.match(/^#[\d,]+$/) || line.match(/^-$/))) {
    // 碰到排名数据，行业列结束
    break;
  }
}

// ========== 提取排名列表 ==========

const ranks: string[] = [];
// 从行业列结束后开始
let rankStartIdx = industryStartIdx + industries.length;

// 向后搜索排名区域
for (let i = rankStartIdx; i < lines.length; i++) {
  if (lines[i].match(/^#[\d,]+$/) || lines[i] === "-") {
    ranks.push(lines[i]);
    if (ranks.length >= count) break;
  } else if (ranks.length > 0 && lines[i].match(/^[\d,.]+[BMK]/)) {
    // 碰到流量数据，排名列结束
    break;
  }
}

// ========== 提取流量份额列表 ==========

// 流量份额为两行一组：绝对值行 + 百分比行
const trafficAbsolute: string[] = [];
const trafficPercent: string[] = [];
let trafficStartIdx = rankStartIdx + ranks.length;

// 向后搜索流量区域
for (let i = trafficStartIdx; i < lines.length; i++) {
  // 绝对值行: "9M", "3.3M", "892.4K" 等
  const absMatch = lines[i].match(/^([\d,.]+[BMK])$/);
  if (absMatch) {
    trafficAbsolute.push(absMatch[1]);
    // 下一行应该是百分比
    if (i + 1 < lines.length) {
      const pctMatch = lines[i + 1].match(/^([\d,.]+%)$/);
      if (pctMatch) {
        trafficPercent.push(pctMatch[1]);
        i++; // 跳过百分比行
      } else {
        trafficPercent.push("-");
      }
    }
    if (trafficAbsolute.length >= count) break;
  } else if (trafficAbsolute.length > 0 && lines[i].match(/^[+-]?\s*[\d,.]+%$/)) {
    // 碰到变动数据，流量列结束
    break;
  }
}

// ========== 提取变动列表 ==========

const changes: string[] = [];
let changeStartIdx = trafficStartIdx + trafficAbsolute.length * 2;

for (let i = changeStartIdx; i < lines.length; i++) {
  const changeMatch = lines[i].match(/^([+-]?\s*[\d,.]+%|-)$/);
  if (changeMatch) {
    let val = changeMatch[1].replace(/\s+/g, "");
    // 确保正值有 + 前缀
    if (val.match(/^\d/) && val !== "-") val = `+${val}`;
    changes.push(val);
    if (changes.length >= count) break;
  }
}

// ========== 组装 CSV ==========

let csv = "序号,域,行业,全球排名,流量份额(访问量),流量份额(%),变动\n";

for (let i = 0; i < count; i++) {
  const seq = i + 1;
  const d = domains[i] || "-";
  const ind = industries[i] || "-";
  const rank = ranks[i] || "-";
  const absTraffic = trafficAbsolute[i] || "-";
  const pctTraffic = trafficPercent[i] || "-";
  const change = changes[i] || "-";

  csv += `${seq},${d},${ind},${rank},${absTraffic},${pctTraffic},${change}\n`;
}

// 写入文件
const outputPath = path.join(outputDir, "referrals_incoming.csv");
fs.writeFileSync(outputPath, csv, "utf-8");
console.log(`referrals_incoming.csv written to ${outputPath}`);
console.log(`Total rows: ${count}`);
