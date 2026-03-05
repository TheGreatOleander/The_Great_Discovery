# The Great Discovery — n8n Setup Guide

## What n8n Does Here

n8n is the relay between your JSX engine and any AI provider.
The JSX never calls Anthropic directly. It fires a structural event.
n8n receives it, routes it to the right provider, validates the response,
commits it to git, and returns the result.

One flow. Replaceable providers. Full audit trail.

---

## Option A — Ubuntu / Linux (if you get a laptop)

### Install

```bash
npm install -g n8n
```

### Run (foreground, for testing)

```bash
n8n start
```

### Run (background, persistent)

```bash
# Using screen
screen -S n8n
n8n start
# Ctrl+A then D to detach

# Or using pm2
npm install -g pm2
pm2 start n8n -- start
pm2 save
pm2 startup
```

n8n opens at: `http://localhost:5678`

---

## Option B — Termux on Android

### Prerequisites

```bash
pkg update && pkg upgrade
pkg install nodejs
```

### Install n8n

```bash
npm install -g n8n
```

> This takes a while on Android. Let it finish.

### Run

```bash
n8n start
```

n8n opens at: `http://127.0.0.1:5678`

### Run in background (Termux)

```bash
# Install tmux
pkg install tmux

# Start session
tmux new-session -s n8n

# Run n8n
n8n start

# Detach: Ctrl+B then D
# Reattach later: tmux attach -t n8n
```

---

## Import the Flow

1. Open n8n in browser: `http://localhost:5678`
2. Create an account (local only, no signup needed)
3. Click the menu (top left) → **Import from File**
4. Select: `n8n/structural_bridge_flow.json`
5. The flow loads with all nodes pre-wired

---

## Add Your Anthropic API Key

1. In n8n, go to **Settings → Credentials**
2. Click **New Credential**
3. Select **HTTP Header Auth**
4. Name: `Anthropic API Key`
5. Header Name: `x-api-key`
6. Header Value: your Anthropic API key
7. Save

Then in the flow:
- Click the **HTTP — Anthropic** node
- Under Authentication, select the credential you just created

---

## Update the Git Commit Path

In the flow, click **Execute — Git Commit** node.
Change the `cd ~/great-discovery` path to wherever your repo lives.

```bash
# Example for Termux
cd /data/data/com.termux/files/home/great-discovery

# Example for Ubuntu
cd /home/yourname/great-discovery
```

---

## Activate the Flow

1. Click **Activate** toggle (top right of flow editor)
2. The webhook is now live at: `http://localhost:5678/webhook/structural-hole`

---

## Connect the JSX

Edit `config.js`:

```javascript
// Local Ubuntu
WEBHOOK_URL: "http://localhost:5678/webhook/structural-hole",

// Termux (same device as browser)
WEBHOOK_URL: "http://127.0.0.1:5678/webhook/structural-hole",

// Termux (accessing from another device on same WiFi)
// Find your phone's local IP: ifconfig | grep inet
WEBHOOK_URL: "http://192.168.1.XXX:5678/webhook/structural-hole",
```

---

## Test It Without the JSX

```bash
curl -X POST http://localhost:5678/webhook/structural-hole \
  -H "Content-Type: application/json" \
  -d '{
    "event": "STRUCTURAL_HOLE_DETECTED",
    "schema_version": "1.0",
    "timestamp": "2026-01-01T00:00:00Z",
    "hole": {
      "src_concept": "entropy",
      "dst_concept": "attractor",
      "src_domain": "physics",
      "dst_domain": "systems",
      "is_cross_domain": true,
      "dominant_relation": "causes",
      "adjacent_concepts": ["symmetry", "stability"],
      "precision": 0.72,
      "n_domains": 2,
      "src_id": 5,
      "dst_id": 12
    },
    "question": "What lies between physics and systems where entropy causes something that in turn connects to attractor?",
    "allowed_domains": ["physics", "mathematics", "biology", "cognition", "systems", "information"]
  }'
```

Expected response shape:
```json
{
  "concept": "cascade",
  "domain": "systems",
  "confidence": 0.82,
  "reasoning": "...",
  "relations": []
}
```

---

## Switching Providers

To use OpenAI or LM Studio instead of Anthropic:

1. In the **Set — Route Metadata** node
2. Change `provider` value from `"anthropic"` to `"openai"` or `"lmstudio"`
3. Wire up credentials for that branch
4. The normalizer handles all three the same way

To make it configurable from the JSX payload, you can also pass
`"provider": "openai"` in the request body and the Switch node will route it.

---

## Structural Log

Every successful injection is appended to `structural_log.jsonl` in your repo
and committed with a message like:

```
structural injection: cascade (systems) conf=0.82
```

This gives you a full history of every concept the AI has ever injected
into your topology. Replayable. Diffable. Auditable.

---

## Troubleshooting

**Bridge unreachable error in JSX**
→ Check n8n is running: `curl http://localhost:5678/healthz`

**401 from Anthropic**
→ API key not set in credentials, or wrong header name (must be `x-api-key`)

**Normalizer rejection**
→ Provider returned malformed JSON. Check n8n execution log for raw response.

**Git commit failing silently**
→ The `|| true` prevents flow failure. Check the repo path is correct.
→ Make sure git is initialized: `git init && git add . && git commit -m "init"`
