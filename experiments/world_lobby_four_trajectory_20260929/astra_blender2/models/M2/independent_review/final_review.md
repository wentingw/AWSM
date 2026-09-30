# M2 independent final review

**Status: LIMITED. Technical/protocol blockers: none found. Review complete.**

Reviewer: `gpt-6-astra`; independent fresh context; final candidate v3. The four initial geometry blockers are repaired. Visual fidelity and native input consistency remain limited.

- Blender SHA256: `8f80d6299b98743be2151788827528ed8c4fa714ca8490f9797b52cc2c24177a`
- GLB SHA256: `79c7ed61d8a7eee347b462e094fcccf324c824e1774d4f9bb3c9448612921a6f`

The reviewer inspected all six contact sheets covering180 samples, original RGB74/108/129, and every final paired comparison at33/61/74/82/91/100/108/118/129/155. Current Blender and GLB geometry was independently loaded and audited. No new render, BVH input pass, model edit, subagent, GT access or evaluation feedback was used.

## Explicit revisit of initial issues

| Initial issue | Final disposition and independent evidence |
|---|---|
| I01 — records/budgets | Resolved. Three versions, each exactly the fixed ten views:30/50 paired views,3/5 versions. Exactly three180-frame passes. All report and snapshot hashes agree; v3/input_final match the current model. Required records retained. |
| I02 — discarded rod orientation | Resolved. All975 requested world endpoints checked; maximum error1.50µm. Vertical rib spikes are gone in actual comparisons. |
| I03 — inward meshes/degeneracy | Resolved in both artifacts. All1,577 closed components have positive signed volume; no triangle below1e-12m². Normals are finite; open foliage/bowls excluded from closed-volume claims. |
| I04 — shell leaks/blocked passage | Resolved technically. Wall seams have backing. Sample74 missing pixels:2,325→0;61:4,508→3. Nominal1.05×2.24m service aperture is statically clear, including collision proxies. The1.5m hidden vestibule is inferred and bounded. Exterior glazing is explicitly closed and nontraversable. |
| I05 — overlapping seat bases | Resolved. Actual convex base footprints have at least6mm separation; collider polygons match. Shared boundaries are inferred. Seat appearance remains limited. |
| I06 — pendant placements | Still HIGH/LIMITED. Foreground pendant13 in129 improves from+3.382m to−0.074m median signed residual, but82/108 still have missing/misordered lamp silhouettes. Prioritize those correspondences and retain uncertainty for ambiguous lamps. |
| I07 — reception/end wall | Still HIGH/LIMITED. Frame100 desk-intrusion region improves−2.129→+0.231m. Desk regions33/129 remain−1.483/+1.814m; end wall33/129 remains−2.624/+0.927m. Keep conflicting signs and jointly constrain RGB silhouettes; do not rescale or move cameras. |
| I08 — appearance/silhouettes | Still MEDIUM/LIMITED. Mirrors and cap shading improve, but seats61/129/155 remain tall/boxy with wrong back contours/yaws; door frames108 remain visually thin; floor pattern/reflections91/100/108 are subdued; plants and reception trees are inaccurate. Refine those specific contours before fine material detail. |
| I09 — full-input outliers | Uncertainty documented and independently confirmed. DA3 median jumps8.095→19.627m at20→21 and7.942→18.748m at166→167 despite4.14/8.32mm pose steps. Frame175 predicts0.372m median. Contact sheets show similar RGB. Preserve these conflicts; no pose/depth/mask correction is justified by this review. |

A minor additional contact finding, **F10**, remains: four rounded vessels penetrate the floor by3cm, two tree urns by2cm, and some feet/base contacts penetrate the floor inset by1.75cm. Flatten/lift bottoms and use the local finish height in any later physics-ready cleanup. No major unsupported furniture was found in the inspected support bounds.

## Verified evidence and limits

All65 semantic IDs map exactly once to1,602 Blender/GLB components (164,946 triangles). Artifact bounds agree within4.93e-7m; no missing Blender image dependency or external GLB resource was found. All180 cameras equal the unchanged rigid transform times packet poses. Native unit scale is1; Blender units are meters. Saved-camera projection error is0.00010px. All30 saved paired grids, NPZ-intrinsic depth resampling, validity masks, signed/absolute/relative errors and edge arrays were checked.

Existing full-pass references were independently resampled from all180 allowed NPZ inputs, with maximum float-storage difference1.91e-6m. Reference values and domains are identical across the three passes. Final input-consistency MAE is0.6491m over the ten paired views and1.4262m over the full input pass. These summarize consistency with predicted DA3, **not ground-truth accuracy**.

The review checked static topology, rod directions, seat-base separation, support bounds and aperture proxies. It does not certify arbitrary all-pairs intersections, dynamic physics, hidden connectivity, native pose truth, or material appearance in an unrendered GLB viewer. Declared author accesses are in scope; their historical completeness cannot be proved from self-reported logs.

Detailed findings, object/frame references and exact paths read: [final_review.json](final_review.json). Reviewer access/command record: [final_input_access_log.json](final_input_access_log.json). Independent checks: [Blender](final_blender_audit.json), [GLB](final_glb_audit.json), [records/depth](final_records_audit.json), [priority residual regions](final_priority_regions.json). Initial review files were preserved.
