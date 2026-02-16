import type { OpenClawPluginApi } from "openclaw/plugin-sdk";
import { Type } from "@sinclair/typebox";
import { spawn } from "node:child_process";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const PLUGIN_DIR = dirname(fileURLToPath(import.meta.url));
const SCRIPTS_DIR = resolve(PLUGIN_DIR, "scripts");

/** Bridge plugin config keys to environment variables for Python scripts. */
function buildEnv(pluginConfig?: Record<string, unknown>): NodeJS.ProcessEnv {
  const env = { ...process.env };
  if (!pluginConfig) return env;
  if (pluginConfig.proxyBizId) env.PROXY_BIZ_ID = String(pluginConfig.proxyBizId);
  if (pluginConfig.proxyAuthKey)
    env.PROXY_AUTH_KEY = String(pluginConfig.proxyAuthKey);
  if (pluginConfig.proxyAuthPwd)
    env.PROXY_AUTH_PWD = String(pluginConfig.proxyAuthPwd);
  if (pluginConfig.proxyApiUrl)
    env.PROXY_API_URL = String(pluginConfig.proxyApiUrl);
  if (pluginConfig.cookieFilePath)
    env.SW_COOKIE_FILE = String(pluginConfig.cookieFilePath);
  return env;
}

/** Run a Python script and collect stdout/stderr. */
function runPython(
  script: string,
  args: string[],
  env: NodeJS.ProcessEnv,
): Promise<{ stdout: string; stderr: string; code: number }> {
  return new Promise((res) => {
    const child = spawn("python3", [resolve(SCRIPTS_DIR, script), ...args], {
      env,
      cwd: PLUGIN_DIR,
    });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (d: Buffer) => (stdout += d.toString()));
    child.stderr.on("data", (d: Buffer) => (stderr += d.toString()));
    child.on("close", (code: number | null) => res({ stdout, stderr, code: code ?? 1 }));
    child.on("error", (err: Error) => res({ stdout, stderr: err.message, code: 1 }));
  });
}

const similarwebPlugin = {
  id: "similarweb-analysis",
  name: "SimilarWeb Analysis",
  description:
    "Fetch website traffic data from SimilarWeb Pro via API proxy",
  version: "0.3.3",

  register(api: OpenClawPluginApi) {
    const env = buildEnv(api.pluginConfig as Record<string, unknown>);

    // --- Tool 1: similarweb_fetch ---
    api.registerTool({
      name: "similarweb_fetch",
      description:
        "Fetch SimilarWeb traffic data for a domain. Returns overview (visits, ranks, engagement, geography, traffic sources, social, keywords, referrals) as Markdown and CSV.",
      parameters: Type.Object({
        domain: Type.String({
          description: "Target domain, e.g. github.com",
        }),
        noProxy: Type.Optional(
          Type.Boolean({
            description:
              "Skip proxy and connect directly (risk of IP ban). Default false.",
          }),
        ),
      }),
      async execute(
        _toolCallId: string,
        params: { domain: string; noProxy?: boolean },
      ) {
        const args = [params.domain];
        if (params.noProxy) args.push("--no-proxy");

        const result = await runPython("sw_fetch.py", args, env);

        if (result.code !== 0) {
          const msg = (result.stderr || result.stdout).trim();
          return {
            content: [
              {
                type: "text" as const,
                text: `[ERROR] sw_fetch.py exited ${result.code}\n${msg}`,
              },
            ],
          };
        }
        return {
          content: [{ type: "text" as const, text: result.stdout.trim() }],
        };
      },
    });

    // --- Tool 2: similarweb_check_cookie ---
    api.registerTool({
      name: "similarweb_check_cookie",
      description:
        "Check whether the SimilarWeb cookie is still valid. Returns status and cookie age.",
      parameters: Type.Object({}),
      async execute() {
        const result = await runPython("sw_check_cookie.py", [], env);

        const ok = result.code === 0;
        const text = (result.stdout || result.stderr).trim();
        return {
          content: [
            {
              type: "text" as const,
              text: ok
                ? text
                : `[EXPIRED] Cookie 无效或已过期。请手动运行 sw_login.py 刷新。\n${text}`,
            },
          ],
        };
      },
    });

    api.logger.info(
      "SimilarWeb Analysis: registered similarweb_fetch, similarweb_check_cookie",
    );
  },
};

export default similarwebPlugin;
