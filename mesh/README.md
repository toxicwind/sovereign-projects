# Mesh — Sovereign MCP Federation Gateway

> **Nexus (mcpproxy-go fork). Federates 231+ tools across 18 MCP servers behind one HTTP endpoint.**

Mesh is the sovereign MCP tool federation gateway. Every agent runtime — Tau, QED, Yote, OpenFang, Grok — talks to Mesh over a single HTTP endpoint.

Mesh is **not** the stack control plane. That role belongs to `~/sovereign/`. Mesh is a service consumed by every other workspace in the [Sovereign Monorepo](/README.md).

## Where it fits
Mesh provides a unified MCP layer for all workspace tools. 

## Active Emergent Features
- **MCP Federation (231+ tools across 18 servers)**: Single point of federation for Tau, QED, Yote, and OpenFang.
- **Subagent Mesh Routing**: Coordinated tool routing and discovery per agent session.
- **High-Frequency Health Probes & Failfast**: Proactive health checking for upstreams with automatic failure short-circuiting.
- **Tool Quarantine Security**: Defense against malicious/poisoned tool schemas and prompt injection vectors.

- [Architecture & Runbooks](/mesh/gateway/docs/)
- [Admin UI](/http://127.0.0.1:25127/)
- [Monorepo Overview](/README.md)
