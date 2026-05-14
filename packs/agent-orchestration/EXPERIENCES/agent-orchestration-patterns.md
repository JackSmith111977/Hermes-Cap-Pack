---
type: best-practice
skill_ref: "agent orchestration patterns"
keywords: [agent-orchestration-patterns]
created: 2026-05-14
---

# Agent Orchestration Patterns

> 多 Agent 编排实战经验 — 从消息注入到多 Agent 协作的完整指南

## 1. Multi-Agent Pitfalls

### Pitfall 1: Serial Invocation
**Problem**: Waiting for Agent A to finish before starting Agent B creates coupled execution and convergence of thought.

**Solution**: Use parallel spawn (Party Mode). Fire all `delegate_task` calls in a single response so agents work simultaneously.

```python
# ❌ Bad: Serial
agent_a_result = delegate_task("Review architecture")
agent_b_result = delegate_task("Review tests")  # waits for A

# ✅ Good: Parallel
agent_a = delegate_task("Review architecture")
agent_b = delegate_task("Review tests")
# Both run concurrently
```

### Pitfall 2: Context Bloat
**Problem**: Feeding entire conversation history to new agents dilutes focus and wastes tokens.

**Solution**: Compress context to ≤400 words per subagent. Summarize before passing.

| Context | Max Size | Strategy |
|---------|----------|----------|
| Background | 400 words | Summarize key points only |
| Other agents | 200 words per agent | Extract positions, not verbatim |
| User intent | 100 words | Single sentence goal |

### Pitfall 3: Hook vs Injection Confusion
**Problem**: Gateway hooks (`agent:start`) are **async non-blocking** — they cannot modify messages.

**Solution**: Use `run_conversation()` prefix injection (built into Hermes v0.12.0+) for message modification. Use hooks only for side effects (logging, monitoring).

| Mechanism | Timing | Blocking? | Can modify message? |
|-----------|--------|-----------|---------------------|
| `agent:start` Hook | Before LLM | Async non-blocking | ❌ No |
| `run_conversation()` injection | Before message queued | Sync blocking | ✅ Yes |

---

## 2. Message Injection Setup

### Built-in SRA Injection (Hermes v0.12.0+)

The injection code is already in `run_agent.py` — no manual modification needed.

```python
# run_agent.py ~ line 891
# _query_sra_context() queries SRA_PROXY_URL (default: http://127.0.0.1:8536)
# Returns "[SRA] Skill Runtime Advisor 推荐:" prefix
# Injected before user_message at ~line 10802
```

**Key design decisions**:
- **Injection point**: `run_conversation()` before "Add user message"
- **Injection method**: Prefix to user_message (not system prompt) — preserves prompt caching
- **Cache**: Module-level dict with MD5 hash key — avoids duplicate HTTP calls
- **Timeout**: 2 seconds — fast fail, doesn't block messages
- **Degradation**: try/except full catch, returns empty string on failure

### SRA Daemon Management

```bash
# Systemd service (production)
systemctl --user enable srad.service
systemctl --user start srad.service

# Manual (dev)
~/projects/sra/venv/bin/sra attach   # foreground
~/projects/sra/venv/bin/sra start    # background

# Verify
curl -s --noproxy '*' http://127.0.0.1:8536/health
```

**Orphan dependency trap**: When removing SRA, clean up `~/.config/systemd/user/hermes-gateway.service.d/sra-dep.conf` to avoid dangling `Wants=` references.

---

## 3. OpenCode vs Claude Code Integration

### Capability Comparison

| Feature | Claude Code | OpenCode | Codex | Blackbox |
|---------|-------------|----------|-------|----------|
| Provider lock-in | Anthropic only | Provider-agnostic | OpenAI only | Multi-model |
| Skill system | `.claude/skills/` | `.opencode/skills/` + Claude compat | No native skills | No native skills |
| MCP support | Built-in | Built-in | Limited | Via config |
| Print/CI mode | ✅ `-p` flag | ✅ `run` subcommand | ✅ `exec` | ✅ `--prompt` |
| Interactive mode | ✅ tmux/PTY | ✅ PTY | ✅ PTY | ✅ PTY |
| Parallel spawn | ✅ via tmux worktrees | ✅ via background tasks | ✅ via background | ✅ via background |
| Checkpoints | ✅ Built-in | ⚠️ Limited | ❌ | ✅ Built-in |

### When to Use Which

| Scenario | Recommended Agent | Rationale |
|----------|-------------------|-----------|
| Deep code review | Claude Code | Strongest at architectural analysis |
| Multi-model voting | Blackbox | Chairman/judge workflow across models |
| Provider flexibility | OpenCode | Switch providers without config changes |
| Quick one-shot task | Codex | Fastest spin-up time |
| Memory/state heavy | Hermes + subagent delegation | Full toolset + Honcho memory |

### Integration Patterns

**Pattern 1: Hermes as orchestrator spawning coding agents**
```
Hermes → delegate_task → Claude Code (print mode) → return result
                       → OpenCode (background) → return result
                       → collect + synthesize
```

**Pattern 2: Gateway with context injection**
```
User Message → run_conversation() → _query_sra_context() → inject [SRA] prefix
                                  → LLM processes injected context → Response
```

**Pattern 3: Parallel worktrees**
```
git worktree add /tmp/fix-auth main
git worktree add /tmp/fix-db main
→ Spawn Claude Code in each worktree
→ Collect results, push, create PRs
→ git worktree remove each
```

---

## 4. Party Mode Orchestration Reference

### Roster Selection
| Task Type | Recommended Agents |
|-----------|-------------------|
| Architecture design | PM + Architect + Developer |
| Bug investigation | Security + Backend + QA |
| Code review | Claude Code (style) + Codex (logic) + Blackbox (multi-model) |
| Strategy | Product + Data + Design |

### Context Injection Template
```
Persona: You are {name}, {role}.
Context: {project background, ≤400 words}
Others' Opinions: {only if adversarial round}
Task: {specific question}
```

---

## 5. Red Flags Summary

- ❌ Serial agent calls → parallel spawn instead
- ❌ Full history dump → compress to ≤400 words
- ❌ Paraphrasing agent responses → present raw output
- ❌ Using hooks for message modification → use `run_conversation()` injection
- ❌ Missing SRA dependency cleanup → remove `sra-dep.conf` on uninstall
- ❌ Running Codex outside git repo → use `mktemp -d && git init`
- ❌ Running interactive CLI without `pty=true` → process hangs
- ❌ Ignoring workspace trust dialogs → handle "Yes" automatically
