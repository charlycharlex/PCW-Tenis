# 3D production gate: high-craft assets for immersive web

## Asset definition
Record intended physical scale, silhouette, use case, camera distances, interaction range, visual reference, surface finish, and fidelity target (hero close-up / midground / prop). For real products, preserve dimensions and recognizable physical details.

## Required pipeline
1. **Reference & study:** multi-view photos/scan/CAD when possible; form language, proportions, key micro-details and surface behavior. Do not hallucinate exact geometry when brand fidelity matters.
2. **Blockout:** validate silhouette from front/side/three-quarter at scene distance. No detailed texturing until proportions pass.
3. **Geometry:** use topology suited to deformations or static assets; bevels that catch realistic highlights; correct normals/smoothing; non-destructive modifiers when feasible; UV and logical naming; no accidental self-intersections or floating elements.
4. **Materials:** use physically coherent PBR values and believable roughness variation. Avoid generic chrome, noisily procedural scratches, arbitrary glowing edges and every-surface perfect smoothness. Treat microdetail as motivated by real construction.
5. **Lighting:** create lighting designed for shape readability and story. Test silhouettes, highlights, contact shadows and tonal separation; do not hide modeling errors with bloom, overexposure or fog.
6. **Animation/interaction:** deliberate pivot placement, eased and controlled motion, limits that respect the object, camera composition at hero and close-up distances.
7. **Optimization:** correct scale; consolidate where appropriate; texture compression; mesh LOD, instancing and baked details selectively; appropriate export (e.g. glTF/GLB); preserve key highlights and detail in browser renderer.
8. **Verification:** 360-degree turntable, 3 hero-frame close-ups, wireframe/topology inspection, normal checks, desktop and mobile render comparisons if tooling is available. Record limitations.

## Reject the asset if
- Its silhouette is generic or wrong for the reference.
- Details, connectors, seams or material boundaries make no physical sense.
- Topology artifacts, faceting, UV seams or bad shading appear at intended camera distance.
- Its materials rely mainly on metallic=1, neon emission, bloom or procedural noise to appear sophisticated.
- It looks convincing only from one camera angle despite a 360-degree interaction requirement.
- Performance requires disabling essential quality or breaking interaction on target devices.

## Honest fidelity labels
- **Proxy:** silhouette/blockout for interaction.
- **Lookdev:** mostly complete modeling and preliminary materials.
- **Review-ready:** passes documented art/technical checks; awaiting human approval.
- **Approved/final:** human-approved and tested in intended experience.
Never call a procedural primitive 'production-ready hero asset' without evidence.
