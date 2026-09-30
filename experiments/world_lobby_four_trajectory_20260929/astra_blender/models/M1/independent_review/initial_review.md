# M1 independent initial review

**Status: REQUIRES_FIXES**  
Reviewer: `gpt-6-astra`  
Inspected artifact: `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M1/scene.blend`  
SHA256: `345efa3345d57d3ba7563f1d1ee711fa7fbeecc5dfe9073f9b946ee40393d59d`

The saved Blender scene loads and its semantic records are internally consistent. The five fixed comparisons nevertheless show substantial layout and appearance errors. Measured doorway intersections and wall colliders that span doorways require repair. This is an initial review, not freeze approval.

## Technical and protocol status

No technical corruption, missing model artifact, or unauthorized-input evidence prevented completion. Blender inspection passed with **1,081 meshes and 243,083 triangles**, finite coordinates and no missing image dependencies. All meshes map exactly once to **82 semantic objects**, and their recorded bounds agree with the evaluated artifact. The observed passage and collider defects in M1-I03/I04 violate the modelling contract. No GT feedback was used.

## Frame-specific comparison evidence

| Frame | Findings in actual source/model comparisons |
|---|---|
| 0 | Foreground south table/seating disappear; window-side plant is displaced/small; fixtures become smooth bowls; detailed floor reflections are lost. |
| 45 | Source right-hand mirror group and foreground furniture are mostly outside the rendered view; window-side bowl is misplaced; silver doors are reduced to narrow strips. |
| 90 | Mirror group is too small/distant; window column is too dominant; source dark open passage is not retained; planter silhouettes and floor reflections differ. |
| 135 | Mirror discs and bottom-edge south furniture disappear; north bowl landmark misses by196.24 original-image pixels; foliage rises too high; seating proportions differ. |
| 179 | Mirror group and foreground table/chairs disappear; north bowl landmark misses by105.05 pixels; tall sparse planter foliage and smooth ceiling bowls differ from RGB. |

Pixel residuals above are independently recomputed from author-picked points, not new independent pixel picks. The original images are1280×960. Supplementary originals62 and80 establish the visible passage beside the mirror wall.

## Actionable findings

### M1-I01 — HIGH

**Objects:** cameras / mirror_0..9 / seat_S1..5 / table_south  
**Evidence frames:** 0, 45, 90, 135, 179  
**Evidence type:** observed visual defect and measured projection

The fixed-view scene composition does not reproduce the supplied RGB. Foreground south seating/table visible at the bottom of RGB 0,45,135,179 are absent from the corresponding model views. The mirror cluster visible on the right in RGB 45,135,179 is almost entirely or entirely outside the model frame. In the actual geometry projection, mirror_0 has minimum x=1431 at frame45 and x=1726 at frame179 in a 1280-pixel-wide image; table_south has minimum positive-depth projected y=1696 and 2569 respectively versus image height960. In frame90 the mirror group appears much smaller and farther away than in RGB. Saved camera calibration and OpenCV-to-Blender conversion are correct, so this is a coupled inferred layout/pose defect, not evidence of an axis conversion failure.

**Repair:** Jointly refit the longitudinal positions of the south furniture and mirror group, room proportions, and five illustrative camera poses using RGB landmarks across near, middle and far depths. Add foreground table/chair silhouettes, mirror centers, columns, floor boundaries and wall corners to the fit; do not optimize only reception points. Preserve the common supplied intrinsics and explicit invalid-for-metric-evaluation camera flags. Recheck all five fixed views after repair.

### M1-I02 — HIGH

**Objects:** plant_glass_north / column_1  
**Evidence frames:** 0, 45, 90, 135, 179  
**Evidence type:** observed visual defect and recomputed author landmarks

The north window-side bowl plant and column grouping is displaced and the plant appears too small in the forward model views. At frame135, the source bowl/foliage sits well left of the model position. Independently recomputing the author's grass_N projection gives observed(176,550) versus projected(369.06,514.81), a196.24-pixel residual in original RGB coordinates. Corresponding residuals are111.11 at frame0,100.99 at45 and105.05 at179. These are author-picked landmarks independently reprojected, not new independent pixel measurements. The actual projected plant bounds at135 are x283..443, y452..554, consistent with the observed render displacement. Frame90 also shows an oversized/too-close column relative to nearby features.

**Repair:** Re-estimate the bowl/column positions and plant silhouette jointly with the architectural camera fit. Use the clearly visible bowl edge and column base in several source frames, including135 and90. Increase/refine foliage volume only after its screen position and pot scale agree; retain RGB-only scale uncertainty.

### M1-I03 — HIGH

**Objects:** wall_east_main / wall_east_recess / elevator_wall_east_main_0 / elevator_wall_east_main_1 / elevator_wall_east_recess_0  
**Evidence frames:** 45, 62, 80, 90, 135, 179  
**Evidence type:** observed visual defect and measured geometry

Door topology and placement need repair. RGB62,80,90 show a dark open passage beside the southern end of the mirror group, but the model substitutes a closed metal door near y2.0 and does not retain that opening. Separately, three model door leaves intersect wall panels: main_0 leaf overlaps panel_1_0 by0.187 in y; main_1 leaf overlaps panel_13_0 by0.1495; recess_0 leaf overlaps panel_1_0 by0.422. All overlaps span about2.03 in z and the full0.045 leaf thickness in inferred model units. Targeted Blender rays at z1 hit wall panels rather than door leaves at(y1.6),(y11.3),(y15.0). Existing renders show narrow metal strips where RGB shows broad door surfaces.

**Repair:** Represent the observed dark passage as an opening, with any unseen depth explicitly assumed. Split wall panels at exact door/passage jamb coordinates rather than skipping entire panels based on their centers. Keep closed silver doors only where observed; separate passage and elevator semantics. Verify each jamb/leaf for intersection and compare door widths against RGB62/80 and fixed views45/90.

### M1-I04 — HIGH

**Objects:** colliders:wall_east_main / colliders:wall_east_recess  
**Evidence frames:** 62, 80, 90  
**Evidence type:** measured record defect and contract noncompliance

colliders.json assigns each east wall a single solid bounding box over its full height and length. Independent point-in-box checks show the wall boxes cover all four nominal doorway centers at z1. They also cannot preserve the open passage required by RGB. This contradicts the contract requirement that simplified colliders reflect visible geometry and retain open doorways; an 'approximate' label does not resolve it.

**Repair:** Export compound wall colliders for the actual solid wall segments and lintels, leaving the observed passage empty. Keep closed door-leaf colliders separate from wall colliders so opening states can be represented. After geometry repair, test a small set of pedestrian-height rays/points through openings against both meshes and collider records, and document the intended door states.

### M1-I05 — MEDIUM

**Objects:** seat_N3 / seat_N4 / seat_N5 / seat_N6 / table_north / table_south  
**Evidence frames:** 0, 45, 90, 135, 179  
**Evidence type:** observed visual defect and targeted geometry measurement

The north lounge reads as overlapping circular stools rather than the closely fitted modular arrangement in RGB. Actual circular cushion extents overlap horizontally by0.169 for N3/N4,0.0846 for N4/N5 and0.0985 for N5/N6 in inferred units. These are shared-height circular cushion intersections, not merely foliage or unrelated bounding-box overlaps. Smaller south cushion overlaps are also recorded in structural_audit.json. Both table meshes have lowest z0.030 versus inset top z0.012, leaving a0.018 unsupported gap; this is a measured support defect, although it is subtle in the images.

**Repair:** Match the north seating silhouette and relative cushion sizes from RGB0/45/135/179. Adjust center spacing or model fitted noncircular modular boundaries instead of intersecting complete cylinders; preserve deliberate contacts without interpenetration. Extend/lower table supports to contact the floor. Use localized checks rather than claiming exhaustive collision clearance.

### M1-I06 — MEDIUM

**Objects:** pendant_0..19 / ceiling_slats_glass / ceiling_slats_wall  
**Evidence frames:** 0, 45, 90, 135, 179  
**Evidence type:** observed visual defect

The source ceiling has shallow, intricately textured luminous dishes with prominent patterned undersides and irregular spacing. All five model comparisons instead show smooth opaque cream bowls; their distribution and foreground sizes also differ. In45 and179 several model fixtures crowd the top edge while the source's identifiable suspended dishes occupy different positions. The code/scene contain concentric weave rings, but that construction does not produce the visible source underside in the existing renders.

**Repair:** First fit the identifiable fixture centers, projected diameters, heights and ceiling-band boundaries across the fixed views. Then make the underside's relief/ribbing visible at640x480 with restrained geometric or procedural detail and appropriate material contrast. Record unresolved fixture count or correspondence uncertainty rather than treating the generic repeated arrangement as verified.

### M1-I07 — MEDIUM

**Objects:** floor_black_inset / floor_stone / wall_north / wall_east_main / lighting  
**Evidence frames:** 0, 45, 90, 135, 179  
**Evidence type:** observed visual defect with uncertain appearance cause

The source black inset has strong fine patterned reflections/highlights and recognizable warm fixture reflections, while the model inset is a largely smooth blurred dark surface in all five comparisons. The light stone and oak walls are also much flatter/brighter and lose the source grain and tonal variation. These are observed appearance differences; RGB alone does not establish how much of the floor pattern is surface texture versus reflected ceiling detail or lighting.

**Repair:** After repairing ceiling geometry, tune floor roughness/normal detail, fixture emission, window lighting and wall grain against the supplied RGB. Preserve physically plausible reflections and avoid baking source-view imagery into the floor. Judge broad tones and reflection sharpness in the existing five-view comparison format, not only a single view.

### M1-I08 — MEDIUM

**Objects:** planter_north_left / planter_north_right  
**Evidence frames:** 0, 45, 90, 135, 179  
**Evidence type:** observed visual defect

The rendered planter vegetation forms tall sparse sprays with exposed straight stems and detached yellow clusters, whereas the source has denser, finer, lower branching masses. The mismatch is particularly clear in135 and179, where model foliage rises into the reception/tree region and obscures the scene differently. In90 the model planter bodies and spacing also differ from the source front silhouettes. The actual objects extend to approximately z1.96 in inferred units; that height is not a measured physical truth.

**Repair:** Fit the planter body silhouette and the foliage envelope separately in forward and reverse views. Reduce or redistribute tall sprigs, add finer branching and denser small leaves where visible, and preserve the central gap. Treat unseen branch topology as an assumption.

## Checks and budget

- Read the two generic contracts, M1 packet metadata, author scene/layout/semantic/collider/camera records, build and camera scripts, manifest, iteration/access logs and existing GLB-load record.
- Visually inspected all six source contact sheets (samples0..179), original RGB0,45,62,80,90,135,179, and all five actual author comparison images for fixed samples0,45,90,135,179.
- Ran generic inspect_scene.py through Blender5.2 with --factory-startup and --disable-autoexec on the actual scene.blend: PASS,1081 evaluated mesh objects,243083 triangles, finite coordinates and no missing image dependencies.
- Ran the saved read-only review_audit.py without rendering. All1081 meshes map exactly once to82 semantic records; semantic custom properties match; recorded object bounds agree within1e-4; no ordering-sensitive exact world-mesh duplicates detected.
- Verified all180 camera records against packet sample/source/timestamp/intrinsics metadata, orthonormal rotations (maximum error8.88e-16), determinants approximately1, and the saved sample179 camera's OpenCV-to-Blender conversion (maximum error7.86e-8). Blender focal calibration reconstructs fx approximately762.8000 at1280 pixels.
- Confirmed all180 camera valid flags are false and only0,45,90,135,179 are check-render-usable; inferred scale/camera uncertainty is explicitly declared. No supplied depth or pose exists in M1, so no model-versus-depth comparison is applicable.
- Recomputed author-picked RGB landmark projections from camera matrices and projected selected actual object vertices. RMS landmark residuals are39.84,39.08,10.51,63.97,38.11 pixels for0,45,90,135,179 respectively; these are conditional input agreement, not independent calibration accuracy.
- Inspected mirror geometry/materials: ten named reflective discs with metallic1 and roughness approximately0.008, mounted on the wall; no duplicated reflected room found in the inspected scene inventory/code.
- Measured targeted door-leaf/wall box intersections and12 actual Blender doorway rays, wall collider occupancy, circular seat overlaps and furniture support bounds. This was not an exhaustive collision or topology audit.
- Checked author logs: one complete scene version and five completed CPU Cycles renders,12 samples,640x480,4 threads; consistent with manifest counts and build-log saved paths. Reviewer added zero render attempts/views.
- Recomputed scene.blend SHA256 when finalizing the initial report; it matches the hash from the actual Blender audit.

The author has used **1/5 scene versions and5/60 checking renders**. Reviewer render attempts and added views: **0**. Supporting measurements are in [structural_audit.json](structural_audit.json); the generic artifact result is in [artifact_inspection.json](artifact_inspection.json).

## Scope and limitations

No parent experiment, GT geometry/depth/metrics, held-out frames, publication pages, execution plan, other method or historical model was read. No agents were spawned. Model geometry and author build script were not modified; all reviewer writes are confined to models/M1/independent_review.

- M1 is RGB-only: absolute scale, metric camera accuracy and unobserved geometry cannot be validated from this packet.
- Only seven original RGB images were inspected individually; all180 samples were surveyed through the six source contact sheets.
- Landmark residuals use the author's picked pixels and assumed geometry. Visual findings and recomputation do not turn them into independent physical measurements.
- Projection bounds ignore occlusion. Duplicate detection is ordering-sensitive and rounded to1e-6; collision/support checks were targeted, not exhaustive. No manifoldness or complete navigation claim is made.
- Existing author comparison images were inspected; no independent re-render was added. Render-to-candidate continuity relies on the inspected build script/logs and artifact audit rather than a fresh render.
- GLB parsing was reviewed through the existing author checks/glb_load.json only; scene.glb was not independently loaded or hashed by this reviewer.
- Access declarations and inspected scripts/logs showed no unauthorized-input evidence; this is scoped review, not an operating-system or complete execution-history audit.
- This is the initial review only. A repaired candidate requires a later final review and a new scene hash.

## Paths intentionally read

Directory listings were restricted to `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M1` and `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M1`; listing a path did not mean its contents were read. Exact content/image reads, including reviewer-generated audit outputs, are:

- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/configs/review_contract.md`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/configs/modelling_contract.md`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M1/packet.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M1/contact_sheets/000_029.jpg`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M1/contact_sheets/030_059.jpg`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M1/contact_sheets/060_089.jpg`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M1/contact_sheets/090_119.jpg`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M1/contact_sheets/120_149.jpg`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M1/contact_sheets/150_179.jpg`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M1/rgb/0000.png`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M1/rgb/0045.png`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M1/rgb/0062.png`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M1/rgb/0080.png`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M1/rgb/0090.png`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M1/rgb/0135.png`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/inputs/M1/rgb/0179.png`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M1/checks/compare_v1_0000.jpg`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M1/checks/compare_v1_0045.jpg`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M1/checks/compare_v1_0090.jpg`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M1/checks/compare_v1_0135.jpg`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M1/checks/compare_v1_0179.jpg`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M1/modelling_manifest.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M1/layout.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M1/iteration_log.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M1/input_access_log.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M1/analysis/object_inventory.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M1/analysis/measurements.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M1/analysis/camera_checks.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M1/checks/glb_load.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M1/build_scene.py`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M1/prepare_cameras.py`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M1/objects.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M1/colliders.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M1/cameras.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M1/checks/build_v1.log`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M1/scene.blend`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M1/independent_review/artifact_inspection.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M1/independent_review/review_audit.py`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/models/M1/independent_review/structural_audit.json`
- `/home/hchen/Documents/astraBlenderTest/world_lobby_four_trajectory_20260929/astra_blender/tools/inspect_scene.py`

