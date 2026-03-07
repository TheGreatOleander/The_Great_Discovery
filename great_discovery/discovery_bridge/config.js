/**
 * config.js
 * The Great Discovery — AI Bridge Configuration
 *
 * This is the ONLY file you need to edit when changing deployment.
 * All other files import from here.
 */

const BRIDGE_CONFIG = {

  // ── Webhook endpoint ────────────────────────────────────────────────────────
  // Default: n8n running locally on standard port
  // Change this to wherever your n8n instance is running:
  //   Local Ubuntu:  "http://localhost:5678/webhook/structural-hole"
  //   Termux/Android:"http://127.0.0.1:5678/webhook/structural-hole"
  //   Remote server: "https://your-domain.com/webhook/structural-hole"
  //   ngrok tunnel:  "https://abc123.ngrok.io/webhook/structural-hole"
  WEBHOOK_URL: "http://localhost:5678/webhook/structural-hole",

  // ── Request timeout (ms) ────────────────────────────────────────────────────
  TIMEOUT_MS: 30000,

  // ── Allowed structural relation types ──────────────────────────────────────
  // These are the only relation types the bridge will accept from the AI.
  // Anything else is rejected before injection into the graph.
  ALLOWED_RELATION_TYPES: ["supports", "contradicts", "extends", "bridges"],

  // ── Minimum confidence threshold ───────────────────────────────────────────
  // Responses below this confidence are logged but not injected.
  MIN_CONFIDENCE: 0.4,

  // ── Git logging ─────────────────────────────────────────────────────────────
  // Controlled in n8n flow. This flag is here for documentation only.
  GIT_LOGGING_ENABLED: true,

};

// For use in browser (JSX) context
if (typeof window !== "undefined") {
  window.BRIDGE_CONFIG = BRIDGE_CONFIG;
}

// For use in Node/n8n context
if (typeof module !== "undefined") {
  module.exports = BRIDGE_CONFIG;
}
