# SIH26104 — Wow Factor Features (Post-Core-Verification)

**Gate condition — do not start any of this until:**
1. Out-of-domain eval on `garystafford/deepfake-audio-detection` (ElevenLabs +
   5 other TTS platforms) is done and the EER is known
2. Tanvi's sliding-window inference is actually working end-to-end (not just
   planned)
3. Real latency numbers are measured (ms per inference call, actual score
   update cadence)

If any of these three are still open, work on them first. A polished demo
of an unverified core claim is worse than a plain demo of a verified one —
don't decorate before the foundation is checked.

---

## Priority 1 — Explainability overlay (build this first)

**What:** Show *why* the model flagged a segment as spoofed, not just the
score. AST is a transformer, so attention weights over spectrogram patches
are extractable — same conceptual pattern as Grad-CAM, applied to audio
instead of images.

**Why it scores well:** PS26104 explicitly frames this as a "risk-scoring
engine" — a bare number is table stakes. Showing the model's reasoning is
what separates "we called a HF model" from "we understand what's happening
inside it," which directly answers the Judges Check concern about
off-the-shelf models.

**Short implementation approach:**
1. During inference, extract attention weights from the AST model's final
   transformer layer (or an averaged/aggregated view across layers if
   single-layer attention is too noisy) for the current audio window
2. Map attention weights back to time/frequency regions of the input
   spectrogram — this gives you a 2D heatmap over the same window you just
   scored
3. Render this heatmap in the frontend alongside the live score — simplest
   version: a small spectrogram thumbnail with a color overlay, updated per
   window, next to the live graph (not a separate heavy visualization)
4. For the post-session summary, pick the 1-2 highest-scoring (most
   confidently spoofed) windows and show their heatmaps as "evidence"
   alongside the overall verdict

**Scope guard:** this is a visual overlay on an existing score, not a new
model or new training run. If attention-weight extraction proves fiddly
under time pressure, a simpler fallback exists (see below) — don't let this
become a multi-day rabbit hole.

**Fallback if attention extraction is too slow to get working:** show
spectral-difference regions instead — a simple signal-processing diff
between the input window's spectrogram and what a "typical genuine" energy
distribution looks like, highlighted the same way. Less rigorous, but still
visually communicates "the system is showing its work," and it's classical
DSP, not model-internals, so it's fast to build if needed.

---

## Priority 2 — Confidence banding / "uncertain" zone

**What:** Instead of a binary Bonafide/Spoof flag, introduce a third
state — "Uncertain, verify manually" — when the smoothed score falls in a
middle band (e.g. roughly 40-60% on a 0-100 spoof-probability scale; tune
the actual band once real score distributions are visible).

**Why it scores well:** Directly preempts a jury question you already
anticipated yourself — a system that only ever screams "SPOOF DETECTED" or
"SAFE" looks naive. A calibrated uncertain state signals the team
understands that real detection systems don't get to be 100% confident
every time, and it's a much stronger answer than an overconfident binary
system if a judge asks "what happens when the model isn't sure."

**Short implementation approach:**
1. No new model work — this is purely a thresholding/UI decision on scores
   you're already computing
2. Pick threshold bands once you have real score distributions from your
   eval runs (don't guess bands before you've seen real data)
3. Frontend: three visual states instead of two — e.g. green
   (bonafide-confident), amber (uncertain), red (spoof-confident) — on both
   the live graph and the post-session summary
4. In the post-session summary, explicitly report "X% of the session was in
   the uncertain band" as its own stat, not folded into the other two

**Scope guard:** this is genuinely a same-day task. Don't over-engineer the
banding logic (no need for a second model or dynamic per-session
thresholds) — static bands tuned once from real data are enough.

---

## Priority 3 (only if time remains) — Recency-weighted session scoring

**What:** Instead of a flat average of all window scores across a session,
weight recent windows more heavily. Rationale: a real attack pattern is an
impersonator joining a call mid-way after initial trust is established with
a genuine speaker — a flat average would dilute a late-session spoof signal
under a long genuine start.

**Why it scores well:** This is a defensible, explainable engineering
decision that shows domain thinking beyond "we averaged some numbers" — it
directly reflects a realistic fraud scenario, which ties into demo
narrative too (see Priority 4).

**Short implementation approach:**
1. Exponential moving average instead of flat mean for the post-session
   summary's overall verdict (recent windows contribute more)
2. Keep the raw distribution graph as-is (unweighted) so the visual history
   stays honest — only the single "overall verdict" number uses the
   weighted version
3. State the weighting explicitly in the summary UI or PPT — don't let it
   be an invisible design choice a judge has to reverse-engineer

**Scope guard:** this is a formula change, not new infrastructure. Cut this
first if time runs short — Priorities 1 and 2 matter more for jury impact.

---

## Priority 4 (narrative, not engineering — do this regardless of time)

**What:** Demo script uses a realistic fraud scenario (e.g. a fake "CFO"
call requesting an urgent wire transfer) instead of generic "here's a real
clip, here's a fake clip" framing.

**Why it scores well:** Same underlying technical demo, dramatically more
memorable. Zero extra engineering — this is a scripting/presentation
change only.

**Short implementation approach:** write the actual dialogue/scenario for
the pre-recorded demo clips ahead of time, so the audio content itself
tells the fraud story, not just the detection UI.

---

## Explicitly not doing (stays Future Scope slide only)

- Multilingual/multi-accent tuning beyond the base dataset
- Banking/telecom SDK or gRPC integration
- On-device NPU inference for native call-app integration (real product
  path, but blocked on platform-level call-audio access compliance —
  belongs on a "Future Scope" slide as one sentence, not a build target)
- Multi-class attack-type attribution (voice-changer vs. TTS vs. replay)