# M1 independent initial review — BLOCKED

Reviewer: `gpt-6-astra`; fresh independent context; review complete. Candidate: v1.

Model SHA256: `1ff3643fb89f6c209f14b14152a54598b8ecfe862296c77f8d6a074a960973fb`

The model loads and its semantic mapping, numerical projection, and saved check linkage pass. Four technical/protocol blockers remain. Visual quality is **LIMITED**.

## Required repairs

1. **M1-I01 — Missing required records.** `input_access_log.json` and `iteration_log.json` are absent; the manifest still says `building_initial_candidate`. Supply honest M1 author access/command and iteration records, including the failed build/retry and coordinator-run checks. Document unavailable history as unknown. Set the required ready status after completion.
2. **M1-I02 — Corrupt chair-back winding.** The `curved_back` components of north/south seats 2, 3 and 5 each have four inconsistent manifold edges. GLB independently confirms all six; south seat 2 also contains a degenerate evaluated polygon. Correct cap order/normals and verify the exported meshes.
3. **M1-I03 — Major seat penetration.** `south_seat_5` and `south_side_seat_0` have centers only **0.128 m** apart, versus combined radii **0.920 m**. Their bodies overlap by about **0.792 m** radially; further overlaps affect side seat 1. Reconcile physical count and placement using samples **61/74/82/91**.
4. **M1-I04 — Open doorway blocked by proxy.** `mirror_partition` uses one enabled AABB that fills `south_opening`. At **[6.85, 3.925, 1.0] m**, the front geometry is open but the proxy is solid. Split the proxy around the opening. The approximately 1.01 m deep modeled recess does not establish an onward route.

## Visual and support limitations

- **M1-I05 — Sample 108 occlusion.** Source shows the facade/open lobby; the render is mostly nearby partition/door. **91.43%** of saved model-depth pixels are below 1 m, median **0.791 m**. Camera **[7.7, 10.2482, 2.5474] m** is behind the partition, not inside a component. Reassess the joint camera/layout assumption against samples **100/108/118**, using visibility as well as reprojection. Projection math itself passes.
- **M1-I06 — Divider/seating placement.** Samples **33/155** have large model planters across the foreground where source shows open floor/seating edges; **91** has the same conflict from the opposite direction. **118** puts lounge furniture across source open floor. Measure silhouettes and architectural landmarks across these views before changing group centers or inferred poses. See pixel regions in JSON.
- **M1-I07 — Unsupported objects.** `south_side_seat_0..2` start about **8.2 cm** above the insert with no legs. `reception_desk` starts **8.2–10 cm** above its underlying floor without a support component/relation. Repair support as an explicit inference.
- **M1-I08 — Appearance/uncertainty.** Pale walls/fixtures and weak slat/weave contrast differ markedly; the floor grid is too prominent. All 180 cameras remain unvalidated and scale is assumed from a **2.6±0.35 m** door. Keep these limitations explicit.

## Evidence and passing checks

Inspected all six source contact sheets (180 thumbnails), full-resolution source RGB **33/74/108**, all ten actual paired sheets **33/61/74/82/91/100/108/118/129/155**, all ten saved model-depth arrays, and actual blend/GLB geometry. No new visual render or input BVH pass was run.

- **88 semantic IDs / 575 mesh components / 106,322 evaluated triangles.** Complete, unique semantic ownership; matching GLB names/extras and component bounds; no missing image dependency.
- **One observed full version / ten paired views**, within 5/50 budget. Current blend, GLB, build script, layout, objects and cameras match v1 snapshots. All check/model/RGB/depth hashes match. Complete historical budget certification awaits M1-I01.
- Public K and all input frame identities are preserved. All 180 estimated transforms are finite rigid matrices; independent Blender projection error is at most **0.000402 px**. Units are metric with scale length 1, explicitly assumed scale. Estimated cameras match the v1 snapshot.
- **Input depth residuals and three full180 input passes: N/A for M1.** Its packet contains RGB and public intrinsics, no input poses/depth. Positive model optical Z and 99.927–100% finite coverage only establish internal self-occlusion evidence.
- No outside-method/GT/evaluation/provenance-log access occurred during this review. Missing author access records prevent historical compliance certification; no actual leak is alleged.

This is the **initial review**, not a final-candidate approval. A future final review must read author repairs and explicitly revisit **M1-I01–M1-I08**, with current hashes, all fixed checks and budget reverified. Three full input passes remain inapplicable to M1.

Detailed evidence: [initial_review.json](initial_review.json), [record_audit.json](record_audit.json), [geometry_audit.json](geometry_audit.json), [focused_geometry_checks.json](focused_geometry_checks.json), [artifact_inspection.json](artifact_inspection.json). Task-data paths and command records: [input_access_log.json](input_access_log.json).
