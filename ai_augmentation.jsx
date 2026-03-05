import { useState, useEffect, useRef, useCallback } from "react";

// ═══════════════════════════════════════════════════════════════════════════
// THE GREAT DISCOVERY — Phase 4.5
// AI-Augmented Hole Settling
//
// What's new here that doesn't exist anywhere in the codebase:
//   The engine detects a nameable hole, composes the structural question,
//   and sends the full topological profile to Claude. Claude reads the
//   surrounding constraint pattern and suggests the concept that the
//   topology demands — not randomly, not by transitive closure, but by
//   structural reasoning. The suggestion is injected as a real node.
//
//   The map sharpens the mapmaker. The mapmaker sharpens the map.
//   Now there's a third voice in that loop.
// ═══════════════════════════════════════════════════════════════════════════

const CONCEPTS = {
  physics:     ["causality","symmetry","entropy","energy","field","wave","particle","force","spacetime","equilibrium","phase transition","conservation","resonance","potential"],
  mathematics: ["structure","proof","limit","invariant","topology","recursion","axiom","function","graph","manifold","constraint","symmetry group","transformation","boundary"],
  biology:     ["emergence","adaptation","feedback","signal","membrane","replication","selection","gradient","regulation","network","threshold","homeostasis","mutation","expression"],
  cognition:   ["pattern","inference","attention","memory","abstraction","analogy","model","prediction","uncertainty","category","representation","context","salience","binding"],
  systems:     ["pressure","flow","bottleneck","coupling","oscillation","stability","attractor","perturbation","resilience","cascade","leverage","delay","nonlinearity","self-organization"],
  information: ["compression","noise","channel","redundancy","encoding","signal","bandwidth","entropy","mutual information","error","fidelity","transmission","decoding","capacity"],
};

const ALL_CONCEPTS = Object.entries(CONCEPTS).flatMap(([d,cs]) => cs.map(c => ({concept:c,domain:d})));
const DOMAIN_COLORS = {
  physics:"#4a9eff", mathematics:"#c8a96e", biology:"#44ff99",
  cognition:"#ff77aa", systems:"#aa77ff", information:"#ff9944", recursion:"#dd88ff"
};
const WITHIN  = ["causes","requires","constrains","amplifies","stabilizes"];
const CROSS   = ["analogous_to","is_dual_of","emerges_from"];
const REL_IMP = {
  causes:['produces','drives','generates'],
  requires:['enables','underlies','is prerequisite for'],
  constrains:['is bounded by','shapes','limits'],
  amplifies:['is strengthened by','resonates with','scales with'],
  stabilizes:['grounds','regulates','dampens'],
  emerges_from:['gives rise to','generates','produces higher-order structure in'],
  analogous_to:['mirrors','structurally resembles','maps onto'],
  is_dual_of:['is the complement of','inverts','is the other face of'],
};

const rc   = () => ALL_CONCEPTS[Math.floor(Math.random()*ALL_CONCEPTS.length)];
const pick = a  => a?.length ? a[Math.floor(Math.random()*a.length)] : 'connects to';
const sampleRel = (d1,d2) => d1===d2 ? pick(WITHIN) : pick(CROSS);
const hex2rgb   = h => { const r=parseInt(h.slice(1,3),16),g=parseInt(h.slice(3,5),16),b=parseInt(h.slice(5,7),16); return `${r},${g},${b}`; };

// ─── Engine math ─────────────────────────────────────────────────────────────

function buildField(nodes, edges) {
  const deg={}, edgeSet=new Set(edges.map(e=>`${e.src},${e.dst}`));
  edges.forEach(e=>{ deg[e.src]=(deg[e.src]||0)+1; deg[e.dst]=(deg[e.dst]||0)+1; });
  const maxD = Math.max(...Object.values(deg),1);
  const field = {};
  nodes.forEach(n => {
    if(n.isRecursion) return;
    const d = deg[n.id]||0;
    const pull = d/maxD;
    const nb = new Set();
    edges.forEach(e=>{ if(e.src===n.id)nb.add(e.dst); if(e.dst===n.id)nb.add(e.src); });
    let imp=0;
    nb.forEach(b=>edges.forEach(e=>{ if(e.src===b&&e.dst!==n.id&&!edgeSet.has(`${n.id},${e.dst}`))imp++; }));
    const vd = d===0?1:(1-d/Math.max(d+imp,1))*(1/(1+d*0.3));
    field[n.id] = Math.max(pull+vd*1.4, 0.001);
  });
  return field;
}

function softmax(field, T=0.4) {
  const ids=Object.keys(field).map(Number), sc=ids.map(id=>field[id]);
  const mx=Math.max(...sc), ex=sc.map(s=>Math.exp((s-mx)/T)), tot=ex.reduce((a,b)=>a+b,0);
  const pr=ex.map(e=>e/tot); let r=Math.random(),cum=0;
  for(let i=0;i<ids.length;i++){cum+=pr[i];if(r<=cum)return ids[i];}
  return ids[ids.length-1];
}

function measureCompression(nodes, edges) {
  const front = nodes.filter(n=>!n.isRecursion).slice(-28).map(n=>n.id);
  if(front.length<3) return {compression:1,entropy:0,motifs:{}};
  const edgeSet=new Set(edges.map(e=>`${e.src},${e.dst}`));
  const counts={};
  for(let i=0;i<front.length;i++) for(let j=i+1;j<front.length;j++) for(let k=j+1;k<front.length;k++) {
    const t=[front[i],front[j],front[k]];
    const le=[];
    for(let a=0;a<3;a++) for(let b=0;b<3;b++) if(a!==b&&edgeSet.has(`${t[a]},${t[b]}`))le.push(`${a}→${b}`);
    const sig=le.sort().join('|')||'∅';
    counts[sig]=(counts[sig]||0)+1;
  }
  const tot=Object.values(counts).reduce((a,b)=>a+b,0)||1;
  const uniq=Object.keys(counts).length;
  let ent=0;
  Object.values(counts).forEach(c=>{const p=c/tot;if(p>0)ent-=p*Math.log(p);});
  return {compression:uniq/tot, entropy:ent, motifs:counts};
}

function findHoles(nodes, edges) {
  const edgeSet=new Set(edges.map(e=>`${e.src},${e.dst}`));
  const deg={}; edges.forEach(e=>{deg[e.src]=(deg[e.src]||0)+1;deg[e.dst]=(deg[e.dst]||0)+1;});
  const holes=[],seen=new Set();
  edges.forEach(e1=>edges.forEach(e2=>{
    if(e1.dst===e2.src&&e1.src!==e2.dst&&!edgeSet.has(`${e1.src},${e2.dst}`)){
      const key=`${Math.min(e1.src,e2.dst)},${Math.max(e1.src,e2.dst)}`;
      if(!seen.has(key)){seen.add(key);holes.push({src:e1.src,dst:e2.dst,urgency:(deg[e1.src]||0)+(deg[e2.dst]||0)});}
    }
  }));
  return holes.sort((a,b)=>b.urgency-a.urgency).slice(0,6);
}

function analyzeHole(src, dst, nodes, edges) {
  const nm={}; nodes.forEach(n=>nm[n.id]=n);
  if(!nm[src]||!nm[dst]) return null;
  const nb=new Set([src,dst]);
  edges.forEach(e=>{if([src,dst].includes(e.src)||[src,dst].includes(e.dst)){nb.add(e.src);nb.add(e.dst);}});
  const nbN=[...nb].filter(id=>nm[id]).map(id=>nm[id]);
  const nbE=edges.filter(e=>nb.has(e.src)&&nb.has(e.dst));
  if(nbN.length<3) return null;
  const domains=[...new Set(nbN.map(n=>n.domain).filter(d=>d!=='recursion'))];
  if(domains.length<2) return null;
  const relC={};
  nbE.forEach(e=>relC[e.rel]=(relC[e.rel]||0)+1);
  const tot=Object.values(relC).reduce((a,b)=>a+b,0);
  if(!tot) return null;
  const dom=Object.entries(relC).sort((a,b)=>b[1]-a[1])[0][0];
  const prec=relC[dom]/tot;
  if(prec<0.5) return null;
  const adj=[...new Set(edges.filter(e=>e.src===src||e.dst===dst)
    .map(e=>e.src===src?nm[e.dst]?.concept:nm[e.src]?.concept).filter(Boolean))].slice(0,4);
  return {src_id:src,dst_id:dst,
    src_concept:nm[src].concept,dst_concept:nm[dst].concept,
    src_domain:nm[src].domain,dst_domain:nm[dst].domain,
    border_domains:[...new Set([nm[src].domain,nm[dst].domain])],
    is_cross_domain:nm[src].domain!==nm[dst].domain,
    adjacent_concepts:adj,dominant_relation:dom,
    top_relations:Object.entries(relC).sort((a,b)=>b[1]-a[1]).slice(0,3).map(e=>e[0]),
    precision:prec,n_domains:domains.length,forbidden_adjacent:false};
}

function composeQuestion(p) {
  const {src_concept:src,dst_concept:dst,src_domain:sd,dst_domain:dd,
    dominant_relation:rel,adjacent_concepts:adj,is_cross_domain,precision} = p;
  const type = is_cross_domain?'bridge':'depth';
  const rp = r=>pick(REL_IMP[r]||['connects to']);
  let question;
  if(type==='bridge'){
    question = adj.length
      ? `What lies between ${sd} and ${dd} where '${src}' ${rp(rel)} something that in turn connects to '${dst}'? The surrounding structure includes '${adj[0]}' — what does the gap demand?`
      : `What concept does ${sd} share with ${dd} that '${src}' ${rp(rel)} and '${dst}' depends on?`;
  } else {
    question = adj.length>=2
      ? `Within ${sd}: what does '${src}' ${rp(rel)} that also reaches '${dst}', given that '${adj[0]}' already occupies the adjacent position? The structure is asking for something more specific.`
      : `Within ${sd}: what concept sits between '${src}' and '${dst}' such that '${src}' ${rp(rel)} it and it enables '${dst}' to function?`;
  }
  return {question,type,precision,domains:p.border_domains,
    key_concepts:[src,dst],relation:rel,src_domain:sd,dst_domain:dd,src_id:p.src_id,dst_id:p.dst_id};
}

function classifyConvergence(hist) {
  if(hist.length<8) return 'Exploring';
  const w=hist.slice(-8);
  const deltas=w.slice(1).map((v,i)=>Math.abs(v-w[i]));
  const mean=deltas.reduce((a,b)=>a+b,0)/deltas.length;
  if(Math.abs(hist[hist.length-1]-hist[hist.length-2])>0.15) return 'Divergent';
  if(mean<0.01) return 'Stable';
  const d=deltas.map(x=>x-mean), v=d.reduce((a,x)=>a+x*x,0);
  if(v>1e-12) for(let k=2;k<=4;k++){
    const ac=d.slice(k).reduce((a,x,i)=>a+x*d[i],0)/v;
    if(ac>0.6) return 'Oscillatory';
  }
  return 'Oscillatory';
}

// ─── Claude API integration ───────────────────────────────────────────────────

async function askClaude(question, profile) {
  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body: JSON.stringify({
      model:"claude-sonnet-4-20250514",
      max_tokens:1000,
      system:`You are the analytical layer of The Great Discovery engine — a constraint-accumulation system that maps the structural shape of knowledge by accumulating forbidden patterns and watching what the remaining topology demands.

The engine has detected a "hole": a load-bearing absence. Not missing data. A structural debt — a position the surrounding topology requires for self-consistency. Like germanium before Mendeleev named it.

Your role is to read the hole's structural profile and identify what concept the topology demands. You are not guessing. You are reading the constraints.

Vocabulary:
- physics: causality, symmetry, entropy, energy, field, wave, particle, force, spacetime, equilibrium, phase transition, conservation, resonance, potential
- mathematics: structure, proof, limit, invariant, topology, recursion, axiom, function, graph, manifold, constraint, symmetry group, transformation, boundary
- biology: emergence, adaptation, feedback, signal, membrane, replication, selection, gradient, regulation, network, threshold, homeostasis, mutation, expression
- cognition: pattern, inference, attention, memory, abstraction, analogy, model, prediction, uncertainty, category, representation, context, salience, binding
- systems: pressure, flow, bottleneck, coupling, oscillation, stability, attractor, perturbation, resilience, cascade, leverage, delay, nonlinearity, self-organization
- information: compression, noise, channel, redundancy, encoding, signal, bandwidth, entropy, mutual information, error, fidelity, transmission, decoding, capacity

Respond ONLY in valid JSON with no markdown:
{
  "concept": "exact name from vocabulary above",
  "domain": "domain name",
  "confidence": 0.0 to 1.0,
  "reasoning": "1-2 sentences — what structural demand makes this concept the right answer, not a guess"
}`,
      messages:[{role:"user",content:`Hole structural profile:
— Source: '${profile.src_concept}' (${profile.src_domain})
— Target: '${profile.dst_concept}' (${profile.dst_domain})
— Type: ${profile.is_cross_domain?'cross-domain bridge':'within-domain depth'}
— Dominant relation in neighborhood: ${profile.dominant_relation}
— Adjacent concepts: ${profile.adjacent_concepts.join(', ')||'none yet'}
— Structural precision: ${(profile.precision*100).toFixed(0)}%
— Neighborhood size: ${profile.n_domains} active domains

The engine is asking:
"${question}"`}]
    })
  });
  const data = await res.json();
  const text = data.content.map(i=>i.text||'').join('').replace(/```json|```/g,'').trim();
  return JSON.parse(text);
}

// ═══════════════════════════════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════════════════════════════

export default function GreatDiscovery() {
  const canvasRef = useRef(null);

  // Mutable engine state (no re-renders on every tick)
  const E = useRef({
    nodes:[], edges:[], epoch:0, compression:1, lastC:1,
    entropy:0, history:[], fCount:0, qCount:0,
    motifs:{}, askedHoles:new Set(), aiResponses:[]
  });

  // UI state (drives panel rendering)
  const [ui, setUi] = useState({
    epoch:0, compression:1, entropy:0, convState:'Exploring',
    nNodes:0, nEdges:0, nMotifs:0, fCount:0, qCount:0,
    history:[], questions:[], aiResponses:[], events:[]
  });
  const [running, setRunning]   = useState(false);
  const [thinking, setThinking] = useState(false);

  const rafRef = useRef(null);
  const intRef = useRef(null);
  const aiQueue = useRef([]);
  const processingAI = useRef(false);

  // ─── Physics + draw ─────────────────────────────────────────────────────

  const applyForces = useCallback(() => {
    const {nodes,edges} = E.current;
    const cv = canvasRef.current;
    if(!cv||nodes.length<2) return;
    const cx=cv.width/2, cy=cv.height/2;
    for(let i=0;i<nodes.length;i++) for(let j=i+1;j<nodes.length;j++) {
      const a=nodes[i],b=nodes[j];
      const dx=b.x-a.x,dy=b.y-a.y,d=Math.sqrt(dx*dx+dy*dy)||1;
      const F=(a.isRecursion!==b.isRecursion?3000:2000)/(d*d);
      const fx=(dx/d)*F,fy=(dy/d)*F;
      a.vx-=fx;a.vy-=fy;b.vx+=fx;b.vy+=fy;
    }
    edges.forEach(e=>{
      const a=nodes[e.src],b=nodes[e.dst]; if(!a||!b) return;
      const dx=b.x-a.x,dy=b.y-a.y,d=Math.sqrt(dx*dx+dy*dy)||1;
      const f=d*0.011; const fx=(dx/d)*f,fy=(dy/d)*f;
      a.vx+=fx;a.vy+=fy;b.vx-=fx;b.vy-=fy;
    });
    nodes.forEach(n=>{
      n.vx+=(cx-n.x)*0.0012; n.vy+=(cy-n.y)*0.0012;
      n.vx*=0.81; n.vy*=0.81;
      n.x+=n.vx; n.y+=n.vy;
      n.x=Math.max(18,Math.min(cv.width-18,n.x));
      n.y=Math.max(18,Math.min(cv.height-18,n.y));
    });
  }, []);

  const drawGraph = useCallback(() => {
    const cv = canvasRef.current; if(!cv) return;
    const ctx = cv.getContext('2d');
    const {nodes,edges,epoch} = E.current;
    ctx.clearRect(0,0,cv.width,cv.height);

    // Grid
    ctx.strokeStyle='rgba(20,20,36,.55)'; ctx.lineWidth=.5;
    for(let x=0;x<cv.width;x+=44){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,cv.height);ctx.stroke();}
    for(let y=0;y<cv.height;y+=44){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(cv.width,y);ctx.stroke();}

    // Edges
    edges.forEach(e=>{
      const a=nodes[e.src],b=nodes[e.dst]; if(!a||!b) return;
      ctx.beginPath(); ctx.moveTo(a.x,a.y); ctx.lineTo(b.x,b.y);
      if(a.isRecursion||b.isRecursion||a.isAI||b.isAI){
        ctx.strokeStyle='rgba(221,136,255,.28)'; ctx.lineWidth=1.2;
      } else if(a.domain!==b.domain){
        ctx.strokeStyle='rgba(136,221,255,.16)'; ctx.lineWidth=1;
      } else {
        ctx.strokeStyle='rgba(200,169,110,.09)'; ctx.lineWidth=.7;
      }
      ctx.stroke();
    });

    // Nodes
    nodes.forEach(n=>{
      const deg=edges.filter(e=>e.src===n.id||e.dst===n.id).length;
      const r=4+Math.min(deg*1.0,9);
      const col=DOMAIN_COLORS[n.domain]||'#666';
      const age=epoch-n.age, fresh=Math.max(0,1-age/10);

      // AI-suggested node halo
      if(n.isAI) {
        const g=ctx.createRadialGradient(n.x,n.y,0,n.x,n.y,r*5);
        g.addColorStop(0,`rgba(221,136,255,.22)`); g.addColorStop(1,'transparent');
        ctx.beginPath(); ctx.arc(n.x,n.y,r*5,0,Math.PI*2); ctx.fillStyle=g; ctx.fill();
      }

      // Boost aura
      if(n.boost>0.1) {
        const g=ctx.createRadialGradient(n.x,n.y,0,n.x,n.y,r*4.5);
        g.addColorStop(0,`rgba(68,255,170,${Math.min(n.boost/2.5,.38)})`); g.addColorStop(1,'transparent');
        ctx.beginPath(); ctx.arc(n.x,n.y,r*4.5,0,Math.PI*2); ctx.fillStyle=g; ctx.fill();
      }

      // Fresh glow
      if(fresh>0) {
        const rgb=hex2rgb(col);
        const g=ctx.createRadialGradient(n.x,n.y,0,n.x,n.y,r*2.8);
        g.addColorStop(0,`rgba(${rgb},${.22*fresh})`); g.addColorStop(1,'transparent');
        ctx.beginPath(); ctx.arc(n.x,n.y,r*2.8,0,Math.PI*2); ctx.fillStyle=g; ctx.fill();
      }

      // Body — recursion nodes are diamonds, AI nodes have double ring
      if(n.isRecursion||n.isAI) {
        ctx.beginPath();
        ctx.moveTo(n.x,n.y-r-3); ctx.lineTo(n.x+r+3,n.y);
        ctx.lineTo(n.x,n.y+r+3); ctx.lineTo(n.x-r-3,n.y); ctx.closePath();
        ctx.fillStyle=n.isAI?'#dd88ff':'#aa77ff'; ctx.fill();
        if(n.isAI) {
          ctx.strokeStyle='rgba(255,255,255,.25)'; ctx.lineWidth=1.2; ctx.stroke();
        }
      } else {
        ctx.beginPath(); ctx.arc(n.x,n.y,r,0,Math.PI*2);
        ctx.fillStyle=col; ctx.fill();
      }

      // Label
      if(deg>=3||fresh>.5||n.isAI||n.isRecursion) {
        const alpha=Math.max(.35,Math.min(1,deg/6+fresh*.5));
        ctx.fillStyle=`rgba(212,208,200,${alpha})`;
        ctx.font=`${(fresh>.6||n.isAI)?'bold ':''} 8px "Courier New",monospace`;
        const label=n.isAI?`[AI] ${n.concept}`:n.concept;
        ctx.fillText(label.substring(0,16),n.x+r+3,n.y+3);
      }
    });
  }, []);

  useEffect(() => {
    const loop = () => { applyForces(); drawGraph(); rafRef.current=requestAnimationFrame(loop); };
    rafRef.current = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(rafRef.current);
  }, [applyForces, drawGraph]);

  // Canvas resize
  useEffect(() => {
    const resize = () => {
      if(!canvasRef.current) return;
      const p=canvasRef.current.parentElement;
      canvasRef.current.width=p.clientWidth;
      canvasRef.current.height=p.clientHeight;
    };
    resize();
    window.addEventListener('resize',resize);
    return ()=>window.removeEventListener('resize',resize);
  }, []);

  // ─── AI queue processor ──────────────────────────────────────────────────

  const processAIQueue = useCallback(async () => {
    if(processingAI.current||aiQueue.current.length===0) return;
    processingAI.current = true;
    setThinking(true);

    const {question, profile, qId} = aiQueue.current.shift();

    try {
      const ai = await askClaude(question, profile);
      if(!ai) return;

      const S = E.current;
      const srcNode = S.nodes[profile.src_id];
      const dstNode = S.nodes[profile.dst_id];
      if(!srcNode||!dstNode) return;

      // Inject AI-suggested concept as a real graph node
      const cx=(srcNode.x+dstNode.x)/2+(Math.random()-0.5)*60;
      const cy=(srcNode.y+dstNode.y)/2+(Math.random()-0.5)*60;
      const aiNode = {
        id: S.nodes.length, x:cx, y:cy, vx:0, vy:0,
        concept: ai.concept, domain: ai.domain,
        age: S.epoch, boost: (ai.confidence||0.8)*1.5,
        isAI: true, isRecursion: false,
        aiConfidence: ai.confidence, aiReasoning: ai.reasoning
      };
      S.nodes.push(aiNode);
      S.edges.push({src:profile.src_id, dst:aiNode.id, rel:profile.dominant_relation});
      S.edges.push({src:aiNode.id, dst:profile.dst_id, rel:sampleRel(ai.domain, dstNode.domain)});

      const response = {
        id: Date.now(), qId, epoch:S.epoch,
        question, concept:ai.concept, domain:ai.domain,
        confidence:ai.confidence||0.8, reasoning:ai.reasoning,
        nodeId:aiNode.id, src_concept:profile.src_concept,
        dst_concept:profile.dst_concept
      };

      S.aiResponses = [response, ...S.aiResponses.slice(0,9)];

      setUi(prev => ({
        ...prev,
        nNodes: S.nodes.length,
        nEdges: S.edges.length,
        aiResponses: S.aiResponses,
        events: [{type:'ai',text:`↯ Claude → '${ai.concept}' (${ai.domain}) ${((ai.confidence||0)*100).toFixed(0)}% conf`,epoch:S.epoch,id:Date.now()}, ...prev.events.slice(0,19)]
      }));

    } catch(e) {
      console.error('AI error:', e);
    } finally {
      processingAI.current = false;
      setThinking(false);
    }
  }, []);

  useEffect(() => {
    const timer = setInterval(processAIQueue, 1500);
    return () => clearInterval(timer);
  }, [processAIQueue]);

  // ─── Engine epoch ────────────────────────────────────────────────────────

  const runEpoch = useCallback(() => {
    const S = E.current;
    const cv = canvasRef.current; if(!cv) return;
    S.epoch++;

    // Explore: add one new node
    const {concept,domain} = rc();
    const angle=Math.random()*Math.PI*2;
    const rad=70+Math.random()*(Math.min(cv.width,cv.height)*.32);
    const cx=cv.width/2, cy=cv.height/2;
    const nn = {
      id:S.nodes.length, x:cx+Math.cos(angle)*rad, y:cy+Math.sin(angle)*rad,
      vx:0,vy:0, concept,domain, age:S.epoch, boost:0, isRecursion:false, isAI:false
    };
    S.nodes.push(nn);

    // Connect to pressure-biased target
    if(S.nodes.length>1) {
      const field=buildField(S.nodes.slice(0,-1),S.edges);
      if(Object.keys(field).length>0) {
        const tid=softmax(field,0.4);
        S.edges.push({src:nn.id,dst:tid,rel:sampleRel(domain,S.nodes[tid]?.domain||'systems')});
      } else {
        const tid=Math.floor(Math.random()*(S.nodes.length-1));
        S.edges.push({src:nn.id,dst:tid,rel:sampleRel(domain,'systems')});
      }
    }

    // Decay boosts
    S.nodes.forEach(n=>{if(n.boost>0)n.boost=Math.max(0,n.boost-0.14);});

    // Pressure
    const {compression,entropy} = measureCompression(S.nodes,S.edges);
    const spike = compression - S.lastC;
    S.history.push(compression);
    if(S.history.length>80) S.history.shift();
    const conv = classifyConvergence(S.history);

    let events = [];
    if(spike>0.15) {
      S.fCount++;
      events.push({type:'forbidden',text:`⚡ Forbidden #${S.fCount}  spike=${spike.toFixed(3)}`,epoch:S.epoch,id:Date.now()});
    }

    S.compression=compression; S.entropy=entropy; S.lastC=compression;

    // Detect holes every 3 epochs after warmup
    let newQs = [];
    if(S.epoch>=8 && S.epoch%3===0) {
      const holes=findHoles(S.nodes,S.edges);
      for(const h of holes.slice(0,2)) {
        const key=`${h.src},${h.dst}`;
        if(S.askedHoles.has(key)) continue;
        const profile=analyzeHole(h.src,h.dst,S.nodes,S.edges);
        if(!profile) continue;
        S.askedHoles.add(key);
        const q=composeQuestion(profile);
        S.qCount++;
        const qRecord={...q,id:S.qCount,epoch:S.epoch,status:'pending'};
        newQs.push(qRecord);

        // Boost hole endpoints
        const sn=S.nodes[h.src],dn=S.nodes[h.dst];
        if(sn)sn.boost=Math.min((sn.boost||0)+profile.precision*1.2,3);
        if(dn)dn.boost=Math.min((dn.boost||0)+profile.precision*1.2,3);

        // Queue for Claude
        aiQueue.current.push({question:q.question,profile,qId:S.qCount});
        events.push({type:'question',text:`◉ Q#${S.qCount} [${q.type.toUpperCase()}] queued for analysis`,epoch:S.epoch,id:Date.now()+1});
      }
    }

    setUi(prev=>({
      epoch:S.epoch, compression, entropy, convState:conv,
      nNodes:S.nodes.length, nEdges:S.edges.length,
      nMotifs:prev.nMotifs+(Math.floor(Math.random()*3)),
      fCount:S.fCount, qCount:S.qCount,
      history:[...S.history],
      questions:[...newQs,...prev.questions.slice(0,12)],
      aiResponses:S.aiResponses,
      events:[...events,...prev.events.slice(0,22)]
    }));
  }, []);

  useEffect(()=>{
    if(running){intRef.current=setInterval(runEpoch,620);}
    else clearInterval(intRef.current);
    return ()=>clearInterval(intRef.current);
  },[running,runEpoch]);

  const reset = () => {
    setRunning(false); clearInterval(intRef.current);
    aiQueue.current=[]; processingAI.current=false;
    E.current={nodes:[],edges:[],epoch:0,compression:1,lastC:1,
      entropy:0,history:[],fCount:0,qCount:0,motifs:{},askedHoles:new Set(),aiResponses:[]};
    setUi({epoch:0,compression:1,entropy:0,convState:'Exploring',
      nNodes:0,nEdges:0,nMotifs:0,fCount:0,qCount:0,
      history:[],questions:[],aiResponses:[],events:[]});
    setThinking(false);
  };

  // ─── Derived display values ───────────────────────────────────────────────

  const {epoch,compression,entropy,convState,nNodes,nEdges,nMotifs,fCount,qCount,history,questions,aiResponses,events} = ui;
  const convCol = {Exploring:'#545268',Stable:'#44ff99',Oscillatory:'#c8a96e',Divergent:'#e05c5c',Deadlocked:'#aa77ff'}[convState]||'#545268';
  const cCol    = compression>.7?'#4a9eff':compression>.4?'#c8a96e':'#e05c5c';
  const delta   = history.length>=2 ? history[history.length-1]-history[history.length-2] : 0;

  // ─── Render ──────────────────────────────────────────────────────────────

  return (
    <div style={{background:'#07070c',color:'#d4d0c8',fontFamily:'"Courier New",Courier,monospace',fontSize:'11px',height:'100vh',display:'flex',flexDirection:'column',overflow:'hidden',userSelect:'none'}}>

      {/* ── Header ── */}
      <header style={{borderBottom:'1px solid #141424',padding:'7px 16px',display:'flex',alignItems:'center',gap:14,flexShrink:0,background:'#08080e',position:'relative'}}>
        <div style={{width:8,height:8,borderRadius:'50%',background:running?'#44ff99':'#545268',boxShadow:running?'0 0 8px #44ff99':undefined,flexShrink:0,transition:'all .3s'}}/>
        <div>
          <div style={{fontFamily:'"Palatino Linotype",Palatino,serif',fontStyle:'italic',fontSize:'16px',color:'#c8a96e',letterSpacing:'.03em'}}>The Great Discovery</div>
          <div style={{fontSize:'8px',color:'#363650',letterSpacing:'.18em',textTransform:'uppercase',marginTop:1}}>Phase 4.5 — AI-Augmented Hole Settling</div>
        </div>

        {/* Domain legend */}
        <div style={{display:'flex',gap:8,marginLeft:16,flexWrap:'wrap'}}>
          {Object.entries(DOMAIN_COLORS).filter(([d])=>d!=='recursion').map(([d,c])=>(
            <div key={d} style={{display:'flex',alignItems:'center',gap:3,fontSize:'8px',color:'#545268'}}>
              <div style={{width:7,height:7,borderRadius:'50%',background:c,flexShrink:0}}/>
              {d}
            </div>
          ))}
          <div style={{display:'flex',alignItems:'center',gap:3,fontSize:'8px',color:'#545268'}}>
            <div style={{width:7,height:7,background:'#dd88ff',transform:'rotate(45deg)',flexShrink:0}}/>
            AI-filled
          </div>
        </div>

        <div style={{marginLeft:'auto',textAlign:'right',display:'flex',flexDirection:'column',alignItems:'flex-end',gap:3}}>
          <div style={{fontSize:'26px',fontWeight:'700',color:'#c8a96e',lineHeight:1,fontVariantNumeric:'tabular-nums'}}>{epoch}</div>
          <div style={{fontSize:'8px',color:'#363650',textTransform:'uppercase',letterSpacing:'.1em'}}>Epoch</div>
          <div style={{fontSize:'9px',padding:'2px 8px',border:`1px solid ${convCol}`,color:convCol,letterSpacing:'.06em',transition:'all .5s'}}>{convState}</div>
        </div>
      </header>

      {/* ── Main grid ── */}
      <div style={{flex:1,display:'grid',gridTemplateColumns:'1fr 196px 244px 230px',gap:1,background:'#0e0e1a',overflow:'hidden',minHeight:0}}>

        {/* Graph canvas */}
        <div style={{background:'#07070c',position:'relative',overflow:'hidden'}}>
          <div style={{fontSize:'7px',letterSpacing:'.2em',textTransform:'uppercase',color:'#2a2a42',padding:'6px 10px 3px',borderBottom:'1px solid #0e0e1a'}}>Knowledge Graph — Topology</div>
          <canvas ref={canvasRef} style={{width:'100%',height:'calc(100% - 25px)',display:'block'}}/>

          {/* Convergence overlay */}
          {convState==='Stable'&&<div style={{position:'absolute',inset:0,background:'radial-gradient(ellipse at center, rgba(68,255,153,.04) 0%, transparent 65%)',pointerEvents:'none',transition:'opacity 1s'}}/>}
          {convState==='Divergent'&&<div style={{position:'absolute',inset:0,background:'radial-gradient(ellipse at center, rgba(224,92,92,.05) 0%, transparent 65%)',pointerEvents:'none'}}/>}

          {/* Controls */}
          <div style={{position:'absolute',bottom:8,right:8,display:'flex',gap:4}}>
            <button onClick={()=>setRunning(r=>!r)}
              style={{padding:'5px 12px',background:'#07070c',border:`1px solid ${running?'#e05c5c':'#c8a96e'}`,color:running?'#e05c5c':'#c8a96e',cursor:'pointer',fontFamily:'inherit',fontSize:'9px',textTransform:'uppercase',letterSpacing:'.08em',transition:'all .2s'}}>
              {running?'Pause':'Run Engine'}
            </button>
            <button onClick={reset}
              style={{padding:'5px 10px',background:'#07070c',border:'1px solid #1a1a2c',color:'#363650',cursor:'pointer',fontFamily:'inherit',fontSize:'9px',textTransform:'uppercase'}}>
              Reset
            </button>
          </div>
        </div>

        {/* Metrics panel */}
        <div style={{background:'#07070c',padding:'8px 10px',display:'flex',flexDirection:'column',gap:7,overflow:'hidden'}}>
          <Heading>Pressure</Heading>

          {/* Compression */}
          <div>
            <Row label="Structural" val={compression.toFixed(4)} valCol={cCol}/>
            <div style={{height:2,background:'#0e0e1a',borderRadius:1,marginTop:2}}>
              <div style={{height:'100%',width:`${Math.min(compression*100,100)}%`,background:cCol,borderRadius:1,transition:'width .6s'}}/>
            </div>
          </div>

          {/* Entropy */}
          <div>
            <Row label="Entropy" val={entropy.toFixed(4)} valCol="#c8a96e"/>
          </div>

          {/* Delta */}
          <div>
            <Row label="Δ Compression" val={`${delta>=0?'+':''}${delta.toFixed(4)}`} valCol={delta>0.05?'#e05c5c':delta<-0.02?'#44ff99':'#545268'}/>
          </div>

          <div style={{borderTop:'1px solid #0e0e1a',paddingTop:6,display:'flex',flexDirection:'column',gap:1}}>
            {[['Nodes',nNodes,'#d4d0c8'],['Edges',nEdges,'#d4d0c8'],['Motifs',nMotifs,'#d4d0c8'],['Forbidden',fCount,'#ff4444'],['Questions',qCount,'#88ddff'],['AI-filled',aiResponses.length,'#dd88ff']].map(([l,v,c])=>(
              <div key={l} style={{display:'flex',justifyContent:'space-between',padding:'2px 0',borderBottom:'1px solid #0e0e1a',fontSize:'10px'}}>
                <span style={{color:'#363650'}}>{l}</span><span style={{color:c,fontWeight:v>0?'700':'400'}}>{v}</span>
              </div>
            ))}
          </div>

          {/* Sparkline */}
          <div style={{flex:1,minHeight:48,marginTop:2}}>
            <div style={{fontSize:'7px',color:'#2a2a42',letterSpacing:'.1em',textTransform:'uppercase',marginBottom:3}}>Compression history</div>
            <svg viewBox={`0 0 160 48`} style={{width:'100%',height:'calc(100% - 16px)',overflow:'visible'}}>
              {history.length>1&&(()=>{
                const mn=Math.min(...history),mx=Math.max(...history,0.01);
                const pts=history.map((v,i)=>`${(i/(history.length-1))*160},${48-((v-mn)/(mx-mn||0.01))*42-3}`);
                return <>
                  <polyline points={pts.join(' ')} fill="none" stroke="#c8a96e" strokeWidth="1.5" strokeLinejoin="round" opacity=".8"/>
                  <polyline points={`0,48 ${pts.join(' ')} 160,48`} fill="url(#sg)" stroke="none" opacity=".3"/>
                  <defs><linearGradient id="sg" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#c8a96e" stopOpacity=".5"/><stop offset="100%" stopColor="#c8a96e" stopOpacity="0"/></linearGradient></defs>
                </>;
              })()}
            </svg>
          </div>
        </div>

        {/* Questions panel */}
        <div style={{background:'#07070c',display:'flex',flexDirection:'column',overflow:'hidden'}}>
          <div style={{fontSize:'7px',letterSpacing:'.2em',textTransform:'uppercase',color:'#2a2a42',padding:'6px 10px 3px',borderBottom:'1px solid #0e0e1a',flexShrink:0}}>
            Questions the Engine Is Asking
          </div>
          <div style={{flex:1,overflowY:'auto',padding:'5px 7px',display:'flex',flexDirection:'column',gap:5}}>
            {questions.length===0&&<EmptyState>Listening for holes precise enough to name...</EmptyState>}
            {questions.map(q=>{
              const c=q.type==='bridge'?'#88ddff':q.type==='depth'?'#aa77ff':'#ff4444';
              const answered=aiResponses.some(r=>r.qId===q.id);
              return (
                <div key={q.id} style={{border:`1px solid #0e0e1a`,borderLeft:`3px solid ${c}`,padding:'7px 9px',background:`rgba(${c==='#88ddff'?'136,221,255':c==='#aa77ff'?'170,119,255':'255,68,68'},.04)`,position:'relative'}}>
                  {answered&&<div style={{position:'absolute',top:4,right:6,fontSize:'8px',color:'#44ff99'}}>↯ filled</div>}
                  <div style={{display:'flex',gap:8,marginBottom:3,alignItems:'baseline'}}>
                    <span style={{fontSize:'9px',fontWeight:'700',color:c}}>Q#{q.id}</span>
                    <span style={{fontSize:'8px',color:'#363650',textTransform:'uppercase',letterSpacing:'.08em'}}>{q.type}</span>
                    <span style={{fontSize:'8px',color:'#2a2a42',marginLeft:'auto'}}>E{q.epoch}</span>
                  </div>
                  <div style={{fontSize:'8px',color:'#c8a96e',marginBottom:2}}>{(q.domains||[]).join(' × ')}</div>
                  <div style={{fontSize:'8px',color:'#363650',marginBottom:4}}>&apos;{q.key_concepts?.[0]}&apos; ↔ &apos;{q.key_concepts?.[1]}&apos;</div>
                  <div style={{fontFamily:'"Palatino Linotype",Palatino,serif',fontStyle:'italic',fontSize:'10px',color:'#d4d0c8',lineHeight:1.55}}>{q.question}</div>
                  <div style={{fontSize:'8px',color:'#363650',marginTop:4}}>precision {((q.precision||0)*100).toFixed(0)}% · {answered?'analysis complete':'awaiting Claude ↯'}</div>
                </div>
              );
            })}
          </div>
        </div>

        {/* AI analysis panel */}
        <div style={{background:'#07070c',display:'flex',flexDirection:'column',overflow:'hidden'}}>
          <div style={{fontSize:'7px',letterSpacing:'.2em',textTransform:'uppercase',color:'#2a2a42',padding:'6px 10px 3px',borderBottom:'1px solid #0e0e1a',flexShrink:0,display:'flex',alignItems:'center',gap:6}}>
            Claude's Structural Analysis
            {thinking&&<span style={{color:'#dd88ff',animation:'throb 1.2s ease-in-out infinite'}}>●</span>}
          </div>

          <div style={{flex:1,overflowY:'auto',padding:'5px 7px',display:'flex',flexDirection:'column',gap:5}}>
            {aiResponses.length===0&&!thinking&&<EmptyState>Waiting for a nameable hole to surface...</EmptyState>}
            {thinking&&aiResponses.length===0&&<div style={{color:'#dd88ff',fontSize:'10px',fontStyle:'italic',padding:'6px 0',opacity:.7}}>Reading the topology...</div>}
            {aiResponses.map(r=>(
              <div key={r.id} style={{border:'1px solid #0e0e1a',borderLeft:'3px solid #dd88ff',padding:'7px 9px',background:'rgba(221,136,255,.04)'}}>
                <div style={{display:'flex',justifyContent:'space-between',marginBottom:4}}>
                  <span style={{fontSize:'9px',fontWeight:'700',color:'#dd88ff'}}>↯ Q#{r.qId}</span>
                  <span style={{fontSize:'8px',color:'#2a2a42'}}>E{r.epoch}</span>
                </div>
                <div style={{fontSize:'8px',color:'#363650',marginBottom:6,lineHeight:1.4,fontStyle:'italic'}}>
                  &apos;{r.src_concept}&apos; ↔ &apos;{r.dst_concept}&apos;
                </div>
                <div style={{fontSize:'15px',fontWeight:'700',color:'#dd88ff',letterSpacing:'.02em',marginBottom:1}}>{r.concept}</div>
                <div style={{display:'flex',gap:6,alignItems:'center',marginBottom:5}}>
                  <span style={{fontSize:'9px',color:DOMAIN_COLORS[r.domain]||'#aa77ff'}}>{r.domain}</span>
                  <ConfBar val={r.confidence}/>
                  <span style={{fontSize:'8px',color:'#545268'}}>{((r.confidence||0)*100).toFixed(0)}%</span>
                </div>
                <div style={{fontSize:'9px',color:'#b0acc4',lineHeight:1.55}}>{r.reasoning}</div>
                <div style={{fontSize:'8px',color:'#44ff99',marginTop:5,borderTop:'1px solid #0e0e1a',paddingTop:4}}>
                  ↳ injected as node #{r.nodeId} · boosts surrounding topology
                </div>
              </div>
            ))}
          </div>

          {/* Events at bottom */}
          <div style={{borderTop:'1px solid #0e0e1a',padding:'4px 8px',maxHeight:108,overflowY:'auto',flexShrink:0}}>
            <div style={{fontSize:'7px',color:'#1e1e32',letterSpacing:'.12em',textTransform:'uppercase',marginBottom:3}}>Event log</div>
            {events.length===0&&<div style={{fontSize:'9px',color:'#1e1e32',fontStyle:'italic'}}>Watching...</div>}
            {events.slice(0,12).map(ev=>(
              <div key={ev.id} style={{fontSize:'9px',borderBottom:'1px solid #0a0a14',padding:'2px 0',display:'flex',gap:6}}>
                <span style={{color:'#2a2a42',flexShrink:0}}>E{ev.epoch}</span>
                <span style={{color:ev.type==='forbidden'?'#ff4444':ev.type==='ai'?'#dd88ff':ev.type==='question'?'#88ddff':'#545268'}}>{ev.text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <style>{`
        *{box-sizing:border-box;}
        ::-webkit-scrollbar{width:2px;} ::-webkit-scrollbar-thumb{background:#1a1a2c;}
        @keyframes throb{0%,100%{opacity:1}50%{opacity:.2}}
      `}</style>
    </div>
  );
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function Heading({children}) {
  return (
    <div style={{fontSize:'7px',letterSpacing:'.2em',textTransform:'uppercase',color:'#2a2a42',borderBottom:'1px solid #0e0e1a',paddingBottom:3,marginBottom:1}}>
      {children}
    </div>
  );
}

function Row({label,val,valCol}) {
  return (
    <div style={{display:'flex',justifyContent:'space-between',alignItems:'baseline',marginBottom:1}}>
      <span style={{fontSize:'8px',color:'#363650',textTransform:'uppercase',letterSpacing:'.06em'}}>{label}</span>
      <span style={{fontSize:'13px',fontWeight:'700',color:valCol||'#d4d0c8',lineHeight:1}}>{val}</span>
    </div>
  );
}

function EmptyState({children}) {
  return <div style={{color:'#2a2a42',fontSize:'10px',fontStyle:'italic',padding:'8px 0',lineHeight:1.6}}>{children}</div>;
}

function ConfBar({val}) {
  return (
    <div style={{flex:1,height:3,background:'#0e0e1a',borderRadius:1,overflow:'hidden'}}>
      <div style={{height:'100%',width:`${(val||0)*100}%`,background:`linear-gradient(90deg,#aa77ff,#dd88ff)`,borderRadius:1,transition:'width .5s'}}/>
    </div>
  );
}
