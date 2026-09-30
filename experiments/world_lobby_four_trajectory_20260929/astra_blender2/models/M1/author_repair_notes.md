# M1 repaired candidate v2 — author handoff

Status: ready for independent review. Quality: **LIMITED**. This is an author repair report, not independent approval or freeze.

Rebuilt `scene.blend` and `scene.glb` from empty Blender using `build_scene.py` and `layout.json`. Current scene has85 semantic objects and582 mesh components, with complete unique component_names mapping in both exports. Cameras are byte-identical to v1; all180 retain valid=false/unvalidated status and public intrinsics. No input mask was changed.

## Repairs and verification

- M1-I01: retained inherited v1 records and added the current author access/iteration history; unknown earlier history remains explicitly inherited. Manifest is ready_for_independent_review.
- M1-I02: corrected chair cap winding and removed the collapsing bevel. Evaluated scene has0 inconsistent-winding meshes and0 degenerate-face meshes. All8 current curved backs pass GLB watertightness, winding and positive volume.
- M1-I03: retained3 visually observed side seats, repositioned them and separated all13 seat bodies. Minimum radial body clearance is0.051413m. Exact placements remain inferred from incompatible multi-view camera estimates.
- M1-I04: split partition collision into component boxes. Original reviewer probe and full prism x=[6.2,7.85],y=[3.55,4.30],z=[.02,2.55] are clear of enabled proxies. North door is closed. South recess ends at an inferred back wall; no onward route is claimed.
- M1-I07: added inferred side-seat legs and reception plinth, with support relations and semantic names.
- M1-I06/I08: consolidated4 dividers into2, moved north seating and side seats, added the observed side table, reduced the floor motif and adjusted inferred materials/light levels. Every parameter and actual object-bound delta is recorded in the linked JSON files.

## Actual evidence and limitations

Read all6 contact sheets covering180 input frames; viewed original RGB61/74/82/108/129/155 and all10 actual v1 comparisons before repair. Ran and visualized **all10 exact paired checks for v2**:33,61,74,82,91,100,108,118,129,155. All10 v2 comparison images and saved depth arrays were inspected; see `analysis/paired_visual_inspection_v2.json`. Rendering used CPU2threads,12samples,640x480; no supplemental or unlogged render.

M1 has no DA3/input depth. Signed input-depth residuals are null/N/A. Recorded ray-plane distances depend on assumed camera/height; recorded signed v2-minus-v1 optical-Z changes are model self-comparisons, never reference errors. Three full180 BVH passes apply only to M2–M4: M1 count remains0.

M1-I05 remains severe: sample108 median opticalZ is0.791m and91.43% of pixels are below1m; its preserved estimated camera lies behind the modeled partition.61/74/82 constrain that shared partition, so it was not moved/hidden to clear one incompatible camera. Furniture remains too dense in61/74 and shifted right in129. Planter consolidation improves foreground obstruction in33/91/100/155; no claim of globally accurate reconstruction. All180 poses and2.6±.35m door scale remain unvalidated. Weave, vegetation, materials, lighting, thickness and physics are inferred.

## Review artifacts

- `author_repair_notes.json`: issue-by-issue disposition, parameters, frame/pixel evidence and hashes.
- `analysis/author_repair/parameter_changes_v2.json`: before/after values and measurement rationale.
- `analysis/author_repair/object_parameter_deltas_v1_v2.json`: every changed logical object's bounds, dimensions and components, including incidental seeded plant detail.
- `analysis/author_repair/rgb_ray_plane_measurements.json`: conditional measurements, signed pixel residuals and retained disagreements.
- `checks/author/technical_verification.json`: topology/export, seat clearance, portal, camera/identity and budget assertions.
- `checks/glb_load.json` and `checks/artifact_inspection.json`: provided generic validators both PASS.

Two full versions and20 actual paired views total; snapshots and all prior checks retained. No geometry change after v2 checks. Separate final independent review remains required.

SHA256 scene.blend: `747b24362a5c0a2d71d24499a0e82cdc8a1f4595fc9e724a7da5c0d192708f63`

SHA256 scene.glb: `d9add3bc69f3a87dd980e6252d8aac8cd5426665511b00bfe4fd1a06c3e22b50`
