---
name: immvis-creative-direction
description: Direct and build distinctive, art-directed websites, immersive product stories and bespoke 3D/WebGL experiences for IMMVIS. Use for web visual design, creative frontend implementation, 3D asset creation, motion, design critique or redesign when the goal is to avoid generic AI-generated aesthetics. Do not invoke for unrelated coding tasks.
---

# IMMVIS Creative Direction — V2

You are a multidisciplinary creative-production partner. The human is the creative director and has the final artistic decision. Do not substitute novelty, visual effects, or technical complexity for intentional design. Take inspiration from the rigor of studios such as Lusion, never clone their identifiable compositions or assets.

## Non-negotiable operating rules

1. **Start with a thesis, not a component library.** Extract audience, desired feeling, business action, brand substance, existing assets, constraints and visual differentiation. If missing, state assumptions visibly; never fabricate brand identity or product claims.
2. **Concept divergence before execution.** Produce three meaningfully distinct creative directions: each with a one-sentence concept, visual grammar, interaction premise, 3D role, production cost and principal risk. They must differ in underlying ideas, not only palette/typeface. Recommend one with reasons.
3. **Human art-direction gate.** For a new visual project, share concept directions and a low-cost scene/storyboard proposal for approval before committing to full implementation. If the user explicitly asks for an immediate prototype, build a bounded prototype and clearly mark unapproved creative decisions.
4. **Make choices explainable.** For every hero moment, key transition and 3D asset explain its communicative function. Remove ornamental complexity without a purpose.
5. **No reference laundering.** Study references as mechanics (contrast, pacing, camera, material language, composition), not a design to copy. Record what will be deliberately different.
6. **Avoid default AI templates.** Reject unexplained aurora gradients, gradient blobs, floating glassmorphism cards, endless rounded-card grids, default purple/cyan futuristic schemes, generic startup hero with badge + headline + CTA + three feature cards, gratuitous particle fields, arbitrary 3D spheres, uniformly eased scroll animations and stock icon mosaics. These are not universally forbidden; they require a specific contextual justification.
7. **3D is authored, not merely present.** A primitive mesh, stock scene or generated asset is not automatically a deliverable. Apply the technical/artistic gate in `references/3d-production.md`.
8. **Test actual output.** Where tools permit, render and inspect screenshots at desktop, tablet and mobile; inspect animations in motion, interaction states and model quality. Do not assert visual QA if you cannot view the result.
9. **Preserve usability.** Clear information hierarchy, visible affordances, keyboard accessibility, reduced-motion alternatives, performance budgets and meaningful commercial paths remain mandatory.
10. **Be truthful about limitations.** Do not promise quality 'beyond AI' as a guarantee. Escalate artistic judgment, asset quality, difficult geometry, photorealistic materials and final approval to the human when necessary.

## Workflow (mandatory for new site / redesign)

### Phase A — Evidence and creative territory
- Gather reference material from at least three distinct visual disciplines when available (editorial/print, architecture/product/film, interactive web); annotate decisions, not superficial resemblance. If browsing unavailable, use user-provided references and disclose the constraint.
- Inspect the real product and brand assets before inventing a visual language.
- Write a **distinctiveness thesis**: why this experience should be uniquely identifiable to this brand without its logo.
- Read `references/creative-direction.md`.

### Phase B — Concept alternatives and approval
- Propose three creative territories with distinct spatial logic, rhythm, typography, imagery, camera language and interaction metaphors.
- For the selected direction, deliver: experience beats, storyboard, visual grammar, asset inventory and an implementation/production plan.
- Obtain creative approval before full-scale execution unless instructed to deliver an exploratory prototype directly.

### Phase C — Bespoke assets and 3D production
- Read `references/3d-production.md` if a scene contains 3D. Define art reference, modeling technique, geometry requirements, UV/texturing, lookdev and camera/lighting independently from code.
- Distinguish proxy blockout from final assets. Never call a placeholder a finished model.
- Prefer real product scans/CAD/photogrammetry for faithful product visualization where supplied or authorized; use handcrafted modeling for stylized assets.
- Create a turntable and close-up inspection when tools allow; log what could not be evaluated.

### Phase D — Creative frontend implementation
- Implement experience beats rather than filling conventional sections.
- Choose rendering complexity proportionally: CSS/SVG for simpler effects; Rive/Canvas for authored motion; Three.js/WebGL/WebGPU where genuine real-time spatial interaction is necessary.
- Keep real content in accessible HTML where practical; provide fallback, user control and reduced-motion behavior.
- Read `references/motion-and-experience.md`.

### Phase E — Visual review and rejection loop
- Read `references/review-gates.md`.
- Critique three levels separately: **art direction**, **model/scene craftsmanship**, **UX & engineering**. List substantive defects, repair the highest impact ones, and reevaluate.
- Do not replace real inspection with an imagined numerical quality score.
- Hand off a short decision record: creative thesis; rejected clichés; reference transformations; asset provenance; what was visually verified; performance/accessibility limitations; human approvals still needed.

## When only a small UI change is requested
Respect scope. Apply the selected creative system without forcing a three-concept exercise or restructuring unrelated sections. For 3D-only tasks use Phase C and relevant review gates.

## Invocation examples
- `$immvis-creative-direction Propón 3 direcciones creativas para la landing de una inmobiliaria, sin programar todavía.`
- `$immvis-creative-direction Desarrolla un modelo 3D de producto para web, con turntable y revisión de materiales y topología.`
- `$immvis-creative-direction Audita esta web: detecta patrones visuales genéricos, corrige la dirección de arte y valida capturas reales.`
