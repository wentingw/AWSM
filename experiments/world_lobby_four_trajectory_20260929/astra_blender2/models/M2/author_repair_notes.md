# M2 author repair notes — final candidate v3

Status: ready for independent review. Visual quality **LIMITED**. This is an author report, not independent certification or freeze.

- Blender SHA256: `8f80d6299b98743be2151788827528ed8c4fa714ca8490f9797b52cc2c24177a`
- GLB SHA256: `79c7ed61d8a7eee347b462e094fcccf324c824e1774d4f9bb3c9448612921a6f`
- Budget used: 3 versions, 30 exact paired views, 0 supplemental views, exactly 3 full 180-frame BVH passes.
- Full passes: `checks/input_v1`, `checks/input_v2`, `checks/input_final`. The latter two check v2 and v3 respectively; no geometry changes follow the final pass.
- All 180 camera records and rigid scale1 transform preserved. Camera file bytes equal v1; public projection validated by paired tool; original domains identical across versions.

## Review responses

**M2-I01 — records_complete**. Initial evidence retained; two new versions and exactly two additional full180 passes; budgets verified. Final author records and snapshots retained.

**M2-I02 — repaired_author_validated**. All975 requested rod endpoints checked; maximum error1.49519328e-06m. Mode assignment fixed before quaternion.

**M2-I03 — repaired_author_validated**. All1577 closed Blender and GLB components have positive volume, no near-zero triangles. Chair bevel removed; desk counter bevel newly caught in v2 removed in v3. Open bowls and foliage are intentionally excluded from closed-volume claims.

**M2-I04 — repaired_author_validated**. Continuous structural backings split at precise apertures; open service vestibule and split collision proxies. Static tested crossing box clear; closed facade state explicitly blocks exterior entrances.

**M2-I05 — repaired_author_validated**. Seat center/radius/yaw preserved; explicit Voronoi shared boundaries clipped with6mm pairwise gap. Convex footprint intersection test is zero for all seat pairs; colliders use matching footprint prisms.

**M2-I06 — LIMITED_after_measured_repair**. M2-I06 LIMITED: pendant13 foreground correction is supported in33/129 and reduces129 lamp residual from+3.382m to-0.074m. Other distant33/129 correspondences are tentative;82/108 silhouette ordering and missing/overlapping lamps remain visibly wrong. No claim of complete lamp recovery.

**M2-I07 — LIMITED_after_measured_repair**. M2-I07 LIMITED: desk RGB silhouette fit uses33/108/118/129 (<3px front-corner errors), while own DA3 desk signs conflict.129 residual worsens to about+1.81m as33 improves to about-1.48m. End-wall y15.15m retained;33 roughly-2.62m versus129 positive residual; native scale/cameras unchanged.

**M2-I08 — LIMITED_after_appearance_repair**. M2-I08 LIMITED: upholstery shapes/yaws, plant morphology, bowl weave, floor dash pattern, mirror reflections, wall grain and lighting remain approximations. Packed floor texture is visibly too subdued; GLB procedural bump materials may simplify.

**M2-I09 — uncertainty_documented**. The selected DA3 window changes produce discontinuous predicted depth (median8.09 to19.67m at20->21,7.94 to18.74m at166->167) despite sub-centimeter translation and <0.07deg rotation steps and similar source RGB.175 has implausibly short0.37m median. This supports prediction-window inconsistency as a major contributor, not proof that all native poses/geometry are correct. No depth rescale, pose edit or mask trim.

## Concrete measured changes

Reception center: [0.6, 13.45, 0.38] → [0.23424434654125262, 14.358316954150656, 0.27519214296343053]; dimensions [3.1, 1.05, 1.12] → [2.61821583808892, 1.05, 0.9103842859268612]. Measured front corners in RGB33/108/118/129 agree within3px. This improves100 intrusion but worsens129 DA3 agreement; signs are retained below.

Recess start y:8.0 → 7.221245m from RGB61/74/82 ray-plane constraints; values7.070/7.221/7.297m disagree, median used. Window/side/end planes, floor, global transform and scale unchanged.

All fifteen pendant centers and diameters, ten mirror discs, exact before/after layout values and each changed logical-object dimension/bound are recorded in `analysis/revision_measurements.json`, `analysis/revision_evidence.json` and `analysis/object_adjustment_ledger.json`. Shared-seat cuts, backing dimensions, inferred portal returns, frame thicknesses, foliage counts, cap shading and lighting/material changes are explicitly listed. V3 changes are in `analysis/v3_changes.json`. No unmeasured hidden dimension is presented as certain.

## Spatial residual evidence

Signed residual means model optical Z minus own predicted DA3, never ground truth. The original input domain is preserved. These boxes are diagnostics, not new validity masks.

| Region / frame / original RGB box | v1 signed median m | v3 signed median m |
|---|---:|---:|
| reception_33 / 33 / [575, 443, 678, 465] | -2.384 | -1.483 |
| reception_129 / 129 / [919, 568, 1014, 594] | 0.943 | 1.814 |
| wall_end_129 / 129 / [816, 366, 1239, 427] | 0.927 | 0.927 |
| light_d_129 / 129 / [597, 83, 724, 120] | 3.382 | -0.074 |
| wall_end_33 / 33 / [450, 250, 900, 340] | -2.627 | -2.624 |
| wall_end_129 / 129 / [1040, 370, 1240, 470] | 0.759 | 0.764 |
| desk_intrusion / 100 / [920, 580, 1080, 780] | -2.129 | 0.231 |
| open_passage / 74 / [1160, 315, 1280, 540] | -0.911 | -0.869 |
| open_passage / 82 / [918, 458, 985, 565] | -0.532 | -0.320 |
| mirror_cluster / 61 / [568, 270, 1120, 560] | 0.029 | 0.021 |
| mirror_cluster / 74 / [703, 253, 1120, 515] | -0.310 | -0.321 |

All62 regional records and before/after context for every changed object are available in the JSON evidence. Technical normals/endpoint changes are construction corrections, not depth-score optimization.

## Checks and limits

- v1: all ten required comparisons produced and inspected; own-input MAE 0.746716m, valid coverage 99.644909%.
- v2: all ten required comparisons produced and inspected; own-input MAE 0.651883m, valid coverage 99.999082%.
- v3: all ten required comparisons produced and inspected; own-input MAE 0.649109m, valid coverage 99.998918%.
- checks/input_v1:180frames, own-input MAE 1.501260m; same reference arrays/domain as the other passes.
- checks/input_v2:180frames, own-input MAE 1.427656m; same reference arrays/domain as the other passes.
- checks/input_final:180frames, own-input MAE 1.426198m; same reference arrays/domain as the other passes.

Aggregate values are descriptive only. Spatial conflicts and RGB failures remain, especially far pendant correspondences in82/108, seat silhouette/yaw, sparse procedural plant form, end-wall input disagreement and floor/wall appearance. The input outlier investigation reads existing native packet poses, DA3 arrays and saved v1 model arrays; discontinuities align with DA3 selected-window changes, not large pose jumps. No camera correction, depth rescale or mask trimming was performed.

Validation: 65semantic IDs own1602meshes in both artifacts.1577 closed components have outward positive volume; no near-zero triangles. Rod endpoints agree within1.50micrometres. Shared-seat solid footprint intersections are zero. The1.05×2.24m service aperture is statically clear into the bounded1.5m inferred vestibule. Exterior door pairs remain explicitly closed with blocking facade proxies. No claim of a full navigation/physics simulation.

Rebuild with `build_scene.py` (factory startup, threads2) using the retained `layout.json` and `cameras.json`; the script never reads a saved blend. The generated floor texture is packed and embedded in GLB. See `revision_access_log.json` and appended `input_access_log.json` for scoped author access records. Existing independent review files were only read, never rewritten.
