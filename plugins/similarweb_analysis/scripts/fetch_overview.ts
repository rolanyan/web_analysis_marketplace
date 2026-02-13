/**
 * 提取 SimilarWeb Pro 网站表现页面的原始文本。
 * 用法: npx tsx fetch_overview.ts <domain>
 * 输出: 页面 innerText 到 stdout
 *
 * 必须从 dev-browser skill 目录运行，以正确解析 @/client.js 导入。
 */

import { connect } from "@/client.js";
import { dismissDialog } from "./dismiss_dialog.js";

const domain = process.argv[2];
if (!domain) {
  console.error("Usage: npx tsx fetch_overview.ts <domain>");
  process.exit(1);
}

const overviewUrl = `https://pro.similarweb.com/#/digitalsuite/websiteanalysis/overview/website-performance/*/999/3m?webSource=Total&key=${domain}`;

async function main() {
  const client = await connect();
  try {
    const page = await client.page("similarweb");

    // 导航到网站表现页
    await page.goto(overviewUrl, { waitUntil: "domcontentloaded" });

    // 等待 SPA 渲染
    await page.waitForTimeout(8000);

    // 尝试关闭弹窗
    await dismissDialog(page);

    // 额外等待确保内容加载完成
    await page.waitForTimeout(2000);

    // 提取页面文本
    const text = await page.evaluate(() => document.body.innerText);

    // 输出到 stdout
    console.log(text);
  } finally {
    await client.disconnect();
  }
}

main().catch((err) => {
  console.error("Error:", err.message);
  process.exit(1);
});
