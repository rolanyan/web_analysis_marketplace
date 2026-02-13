import type { Page } from "playwright";

/**
 * 检测并关闭 SimilarWeb Pro 页面上的弹窗。
 * 尝试查找 "关闭"、"Close"、"×" 等按钮并点击。
 */
export async function dismissDialog(page: Page): Promise<boolean> {
  try {
    // 常见的关闭按钮选择器
    const selectors = [
      'button:has-text("关闭")',
      'button:has-text("Close")',
      'button:has-text("Got it")',
      'button:has-text("Dismiss")',
      'button[aria-label="Close"]',
      'button[aria-label="close"]',
      '.modal-close',
      '.dialog-close',
      '[data-automation="close-button"]',
      '.notification-bar-close',
    ];

    for (const selector of selectors) {
      const btn = await page.$(selector);
      if (btn) {
        await btn.click();
        await page.waitForTimeout(500);
        return true;
      }
    }

    // 尝试通过 XPath 查找包含 "关闭" 文本的可点击元素
    const closeBtn = await page.$('xpath=//button[contains(text(), "关闭")] | //a[contains(text(), "关闭")] | //span[contains(text(), "关闭")]/ancestor::button');
    if (closeBtn) {
      await closeBtn.click();
      await page.waitForTimeout(500);
      return true;
    }

    return false;
  } catch {
    // 弹窗可能已消失或选择器失效
    return false;
  }
}
