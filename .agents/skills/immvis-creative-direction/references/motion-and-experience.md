# Choreography & interaction

Design a sequence of experience beats: initial frame, reveal, exploration, explanation, decision, action. Specify what the visitor perceives, does, learns and can skip at each beat.

For each moving element specify: trigger, purpose, duration/rhythm, camera behavior, user control, interruption, reduced-motion substitute and mobile fallback.

Prefer compositional transitions (shared object, spatial continuity, visual cause/effect) rather than generic fade-up-on-scroll. Do not hijack scroll without strong rationale and a recoverable navigation model. Any custom pointer must preserve pointer feedback, keyboard alternatives and touch usability.

UX constraints: visible path to primary conversion; content remains readable with JS/WebGL disabled where practical; focus states; text contrast; semantic landmarks; WCAG-conscious navigation; motion can be reduced; loading feedback and graceful asset fallbacks.

Engineering checks: avoid huge synchronous JS bundles; lazy-load heavyweight scenes; validate actual frame pacing on target hardware; adaptive DPR/LOD; respect bandwidth and battery; monitor page shift and interaction lag. Do not invent measured FPS or Lighthouse scores.
