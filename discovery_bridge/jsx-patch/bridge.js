/**
 * bridge.js
 * The Great Discovery — Structural AI Bridge
 *
 * DROP-IN REPLACEMENT for the direct Anthropic fetch in ai_augmentation.jsx
 *
 * HOW TO APPLY:
 *   1. In ai_augmentation.jsx, DELETE the entire askClaude() function
 *   2. DELETE the import of fetch (it's native, stays)
 *   3. PASTE this file's contents in its place (or import it)
 *   4. The call site `await askClaude(question, profile)` becomes
 *      `await askStructuralBridge(question, profile)` — one rename
 *
 * WHAT CHANGED:
 *   Before: JSX → api.anthropic.com (direct, key exposed, provider locked)
 *   After:  JSX → n8n webhook → provider → normalizer → back to JSX
 *
 * The JSX now only:
 *   - Emits a structural event payload
 *   - Validates the response shape
 *   - Injects if valid, rejects if not
 *   It does NOT know or care which AI answered.
 */

// ── Structural contract ───────────────────────────────────────────────────────
// Every response from the bridge MUST match this shape.
// Anything else is rejected before touching the graph.

const ALLOWED_RELATION_TYPES = ["supports", "contradicts", "extends", "bridges"];
const MIN_CONFIDENCE = 0.4;
const WEBHOOK_URL = (typeof window !== "undefined" && window.BRIDGE_CONFIG)
  ? window.BRIDGE_CONFIG.WEBHOOK_URL
  : "http://localhost:5678/webhook/structural-hole";
const TIMEOUT_MS = (typeof window !== "undefined" && window.BRIDGE_CONFIG)
  ? window.BRIDGE_CONFIG.TIMEOUT_MS
  : 30000;


// ── Payload builder ───────────────────────────────────────────────────────────
// Constructs the canonical structural event emitted to n8n.
// n8n does not receive raw JSX state — it receives a structured query.

function buildStructuralPayload(question, profile) {
  return {
    event: "STRUCTURAL_HOLE_DETECTED",
    schema_version: "1.0",
    timestamp: new Date().toISOString(),
    hole: {
      src_concept:       profile.src_concept,
      dst_concept:       profile.dst_concept,
      src_domain:        profile.src_domain,
      dst_domain:        profile.dst_domain,
      is_cross_domain:   profile.is_cross_domain,
      dominant_relation: profile.dominant_relation,
      adjacent_concepts: profile.adjacent_concepts || [],
      precision:         profile.precision,
      n_domains:         profile.n_domains,
      src_id:            profile.src_id,
      dst_id:            profile.dst_id,
    },
    question: question,
    // Vocabulary constraint — tells the provider what concepts are valid
    allowed_domains: [
      "physics", "mathematics", "biology",
      "cognition", "systems", "information"
    ],
    allowed_concepts: {
      physics:     ["causality","symmetry","entropy","energy","field","wave","particle","force","spacetime","equilibrium","phase transition","conservation","resonance","potential"],
      mathematics: ["structure","proof","limit","invariant","topology","recursion","axiom","function","graph","manifold","constraint","symmetry group","transformation","boundary"],
      biology:     ["emergence","adaptation","feedback","signal","membrane","replication","selection","gradient","regulation","network","threshold","homeostasis","mutation","expression"],
      cognition:   ["pattern","inference","attention","memory","abstraction","analogy","model","prediction","uncertainty","category","representation","context","salience","binding"],
      systems:     ["pressure","flow","bottleneck","coupling","oscillation","stability","attractor","perturbation","resilience","cascade","leverage","delay","nonlinearity","self-organization"],
      information: ["compression","noise","channel","redundancy","encoding","signal","bandwidth","entropy","mutual information","error","fidelity","transmission","decoding","capacity"],
    },
  };
}


// ── Response validator ────────────────────────────────────────────────────────
// Hard gate. Nothing enters the graph that doesn't pass this.

function validateBridgeResponse(data) {
  if (!data || typeof data !== "object") {
    throw new Error("Bridge returned non-object response");
  }

  if (typeof data.concept !== "string" || data.concept.trim() === "") {
    throw new Error("Bridge response missing valid concept string");
  }

  if (typeof data.domain !== "string" || data.domain.trim() === "") {
    throw new Error("Bridge response missing valid domain string");
  }

  if (typeof data.confidence !== "number") {
    throw new Error("Bridge response missing confidence number");
  }

  if (data.confidence < MIN_CONFIDENCE) {
    throw new Error(`Bridge response confidence ${data.confidence} below threshold ${MIN_CONFIDENCE}`);
  }

  if (typeof data.reasoning !== "string") {
    data.reasoning = "No reasoning provided.";
  }

  // Validate relations if present (optional field)
  if (data.relations !== undefined) {
    if (!Array.isArray(data.relations)) {
      throw new Error("Bridge response relations field must be an array");
    }
    data.relations = data.relations.filter(r =>
      r && typeof r.to !== "undefined" &&
      ALLOWED_RELATION_TYPES.includes(r.type)
    );
  } else {
    data.relations = [];
  }

  return data;
}


// ── Main bridge function ──────────────────────────────────────────────────────
// Replaces askClaude(question, profile) — same signature, same return shape.
// Returns: { concept, domain, confidence, reasoning } or throws.

async function askStructuralBridge(question, profile) {
  const payload = buildStructuralPayload(question, profile);

  // Timeout wrapper — don't hang the engine if bridge is unreachable
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

  let response;
  try {
    response = await fetch(WEBHOOK_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
  } catch (err) {
    clearTimeout(timer);
    if (err.name === "AbortError") {
      throw new Error(`Structural bridge timed out after ${TIMEOUT_MS}ms`);
    }
    throw new Error(`Structural bridge unreachable: ${err.message}`);
  } finally {
    clearTimeout(timer);
  }

  if (!response.ok) {
    throw new Error(`Structural bridge HTTP ${response.status}: ${response.statusText}`);
  }

  let data;
  try {
    data = await response.json();
  } catch (err) {
    throw new Error("Structural bridge returned non-JSON response");
  }

  // Validate and return — throws if invalid, so caller's try/catch handles it
  return validateBridgeResponse(data);
}


// ── Deduplication check (call before injection) ───────────────────────────────
// Pass your current nodes array and the returned concept.
// Returns true if the concept already exists in the graph.

function conceptAlreadyExists(nodes, concept, domain) {
  return nodes.some(
    n => n.concept === concept && n.domain === domain && !n.isRecursion
  );
}


// Export for use in JSX (or Node if testing)
if (typeof module !== "undefined") {
  module.exports = { askStructuralBridge, buildStructuralPayload, validateBridgeResponse, conceptAlreadyExists };
}
