# The Great Discovery — AI Bridge v1.0

## What This Is

A constitutional relay between the Great Discovery JSX engine
and any AI provider. The JSX never calls Anthropic directly.
It emits a structural event. This bridge handles the rest.

```
JSX Engine
   ↓
POST → n8n webhook (/structural-hole)
   ↓
Provider Router (Anthropic active | OpenAI stub | LM Studio stub)
   ↓
Normalizer Gate (validates structural contract — rejects non-conforming)
   ↓
Git Commit (structural_log.jsonl)
   ↓
Response → JSX (concept injected into graph)
```

## Files

```
config.js                          ← EDIT THIS for deployment
jsx-patch/
  ai_augmentation.jsx              ← Drop-in replacement (bridge wired in)
  bridge.js                        ← Bridge functions (reference / reuse)
n8n/
  structural_bridge_flow.json      ← Import into n8n
docs/
  n8n_setup.md                     ← Setup guide (Ubuntu + Termux)
```

## Quick Start

1. Edit `config.js` — set `WEBHOOK_URL` to your n8n instance
2. Import `n8n/structural_bridge_flow.json` into n8n
3. Add Anthropic API key in n8n Credentials
4. Activate the flow
5. Replace your `ai_augmentation.jsx` with `jsx-patch/ai_augmentation.jsx`

Full instructions: `docs/n8n_setup.md`

## Structural Contract

Every AI response must conform to:

```json
{
  "concept": "string (from allowed vocabulary)",
  "domain": "physics|mathematics|biology|cognition|systems|information",
  "confidence": 0.0,
  "reasoning": "string"
}
```

Anything else is rejected by the Normalizer Gate before touching the graph.

## What Changed vs Original JSX

| Before | After |
|--------|-------|
| `askClaude()` calls Anthropic directly | `askStructuralBridge()` calls n8n |
| API key exposed in frontend | Key lives in n8n credentials only |
| No deduplication | `conceptAlreadyExists()` check before injection |
| No validation | `validateBridgeResponse()` hard gate |
| No error surfacing in UI | Bridge errors show in event log |
| Provider locked to Anthropic | Switch node — any provider |
| No audit trail | Git commit per injection |

## Provider Abstraction

Change provider by editing the `Set — Route Metadata` node in n8n.
Set `provider` to: `anthropic`, `openai`, or `lmstudio`.

Or pass it in the request payload from JSX. Your call.
