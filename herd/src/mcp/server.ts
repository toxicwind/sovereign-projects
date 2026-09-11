/**
 * herd-schema-mcp — Herd Schema API MCP Server
 *
 * Provides:
 * - Model discovery (25100 completions API)
 * - Completions with streaming
 * - Herd status and routing
 * - Local-first repo scanning
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { existsSync, readdirSync } from "node:fs";
import { join } from "node:path";

const COMPLETIONS_URL = process.env.COMPLETIONS_URL || "http://127.0.0.1:25100/v1/chat/completions";
const HERD_DIR = process.env.HERD_DIR || "/home/toxic/projects/sovereign-projects/herd";
const PROJECTS_DIR = process.env.PROJECTS_DIR || "/home/toxic/projects";
const SOVEREIGN_DIR = process.env.SOVEREIGN_DIR || "/home/toxic/sovereign";

const server = new Server({ name: "herd-schema-mcp", version: "1.0.0" }, { capabilities: { tools: {} } });

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    { name: "list_models", description: "List models on herd completions API (port 25100)", inputSchema: { type: "object", properties: {} } },
    { name: "completions", description: "Send prompt to herd completions API", inputSchema: { type: "object", properties: { model: { type: "string" }, prompt: { type: "string" }, max_tokens: { type: "number" }, stream: { type: "boolean" } }, required: ["prompt"] } },
    { name: "herd_status", description: "Get herd status: services, models, port 25100 health", inputSchema: { type: "object", properties: {} } },
    { name: "scan_repos", description: "Scan local git repos for audit", inputSchema: { type: "object", properties: { paths: { type: "array", items: { type: "string" } }, auto_fix: { type: "boolean" }, pre_check: { type: "boolean" }, completions: { type: "boolean" } } } },
    { name: "repo_tree", description: "Get hierarchical tree of local git repos grouped by area", inputSchema: { type: "object", properties: { area: { type: "string" }, recent_days: { type: "number" } } } },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (req) => {
  const { name, arguments: args } = req.params;
  switch (name) {
    case "list_models": {
      try {
        const resp = await fetch(COMPLETIONS_URL.replace("/chat/completions", "/models"), { signal: AbortSignal.timeout(5000) });
        const data = await resp.json();
        return { content: [{ type: "text", text: JSON.stringify({ count: data.data?.length || 0, models: data.data?.map((m: any) => m.id) || [] }, null, 2) }] };
      } catch (e) { return { content: [{ type: "text", text: `Error: ${e}` }] }; }
    }
    case "completions": {
      const prompt = args?.prompt as string;
      const model = (args?.model as string) || "beellama/qwen-flash-64k";
      const maxTokens = (args?.max_tokens as number) || 500;
      try {
        const resp = await fetch(COMPLETIONS_URL, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ model, messages: [{ role: "user", content: prompt }], max_tokens: maxTokens, stream: args?.stream || false }), signal: AbortSignal.timeout(30000) });
        const data = await resp.json();
        return { content: [{ type: "text", text: data.choices?.[0]?.message?.content || "" }] };
      } catch (e) { return { content: [{ type: "text", text: `Completions error: ${e}` }] }; }
    }
    case "herd_status": {
      const status: Record<string, any> = {};
      try { const resp = await fetch(COMPLETIONS_URL.replace("/chat/completions", "/models"), { signal: AbortSignal.timeout(3000) }); const d = await resp.json(); status.models = d.data?.length || 0; } catch { status.models = "unreachable"; }
      status.port25100 = status.models !== "unreachable" ? "healthy" : "down";
      status.herd_exists = existsSync(HERD_DIR);
      status.projects_exists = existsSync(PROJECTS_DIR);
      status.sovereign_exists = existsSync(SOVEREIGN_DIR);
      return { content: [{ type: "text", text: JSON.stringify(status, null, 2) }] };
    }
    case "scan_repos": {
      const paths = (args?.paths as string[]) || [PROJECTS_DIR, SOVEREIGN_DIR];
      const results: any[] = [];
      for (const p of paths) { if (!existsSync(p)) { results.push({ path: p, error: "NOT_FOUND" }); continue; } const repos = scanGitRepos(p); results.push({ path: p, count: repos.length, repos: repos.slice(0, 5) }); }
      return { content: [{ type: "text", text: JSON.stringify({ total: results.reduce((a, r) => a + r.count, 0), results }, null, 2) }] };
    }
    case "repo_tree": {
      const area = args?.area as string | undefined;
      const recentDays = (args?.recent_days as number) || 7;
      return { content: [{ type: "text", text: JSON.stringify(buildRepoTree(area, recentDays), null, 2) }] };
    }
    default: throw new Error(`Unknown tool: ${name}`);
  }
});

function scanGitRepos(dir: string): any[] {
  const repos: any[] = [];
  try { const entries = readdirSync(dir, { withFileTypes: true }); for (const e of entries) { if (!e.isDirectory() || !existsSync(join(dir, e.name, ".git"))) continue; repos.push({ name: e.name, path: join(dir, e.name) }); } } catch {}
  return repos;
}

function buildRepoTree(area?: string, recentDays = 7): any {
  const paths = area === "projects" ? [PROJECTS_DIR] : area === "sovereign" ? [SOVEREIGN_DIR] : [PROJECTS_DIR, SOVEREIGN_DIR];
  const tree: Record<string, any[]> = {};
  for (const p of paths) { tree[p === PROJECTS_DIR ? "projects" : "sovereign"] = scanGitRepos(p).slice(0, 50); }
  return tree;
}

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("herd-schema-mcp running on stdio");
}

main().catch(console.error);
