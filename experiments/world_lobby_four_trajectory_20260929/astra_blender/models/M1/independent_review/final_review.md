# M1 independent final review

**Status: LIMITED.** Review complete. Structural repairs pass targeted checks, but substantial visual mismatches remain. No technical corruption, missing required model artifact, or evidence of unauthorized input was found.

Candidate SHA256: `80f985ad09591bdb227e99e71f6bacaa0b9e8c8b565c27da64ad4ac4ceb8910e`

Reviewer: `gpt-6-astra`. Fixed frames: 0, 45, 90, 135, 179. Extra renders: **0**. Total logged author checks: 10; versions: 2.

## Resolution of initial findings

- **M1-I01 — PARTIALLY_FIXED** (cameras / mirror_0..9 / seat_S1..5 / table_south): Foreground south furniture and right-wall mirrors now enter the forward views. Composition remains materially wrong: frame 0 shows much more foreground furniture; frames 45/179 show substantially more mirror cluster; frame 135 shows a wider, separated north seating arrangement and changed floor/wall perspective; frame 90 has changed planter/wall/column proportions. Current author-picked mirror_smalltop residuals are 178.25, 153.85 and 188.65 pixels at 45,135,179. These are recomputed conditional landmark errors, not independent pixel measurements. Action: Jointly fit architectural boundaries, mirror centers and furniture silhouettes across all five frames, retaining invalid-for-metric-evaluation cameras.

- **M1-I02 — PARTIALLY_FIXED** (plant_glass_north / column_1): North bowl position improves: grass_N residuals are 3.92,4.29,26.95,36.79 pixels at 0,45,135,179. However, the final render has a shallow wide bowl with sparse radial blades and exposed dark soil; RGB has a fuller dense tuft and deeper-looking bowl. In 45/179 the column/bowl grouping still differs; column_base residuals are 69.20/60.33 pixels. Action: Retain the positional improvement while fitting bowl depth, tuft envelope and column alignment in multiple frames.

- **M1-I03 — PARTIALLY_FIXED** (wall_east_main / wall_east_recess / elevator_wall_east_main_0 / elevator_wall_east_main_1 / elevator_wall_east_recess_0): Confirmed topology repair: passage_south replaces the closed south leaf, nine rays at y=4.4/4.8/5.2 and z=0.3/1.0/1.8 travel from x=7.0 to8.6 without a hit; no closed-door leaf intersects an east-wall panel in the targeted box test. Door semantics and clear jamb splits exist. Visual placement/width remain approximate: at frame90 the wall opening is a narrow dark strip, and at45/179 broad source metal-door surfaces are not reproduced. Action: Keep the repaired topology; refine projected jamb positions and door widths from RGB. Unseen passage depth remains an assumption.

- **M1-I04 — FIXED_IN_TARGETED_CHECKS** (colliders:wall_east_main / colliders:wall_east_recess): East-wall colliders are now compound solid-component boxes. All12 sampled doorway points at z1 are free of wall parts; all compound-part bounds match actual inspected mesh bounds within1e-4. Passage return/lintel parts preserve its interior; closed door leaves have separate records. Action: No further action for the original gross wall-box defect; furniture colliders remain approximate.

- **M1-I05 — PARTIALLY_FIXED** (seat_N3 / seat_N4 / seat_N5 / seat_N6 / table_north / table_south): The circular cushion test now reports no penetrations greater than0.025 inferred units. Both table minima are z0.011999995 against inset top0.012, resolving the prior unsupported gap. Visual modular shape is unresolved: frames0/45/135/179 show separated cylindrical stools and straight-backed chairs instead of the tightly fitted curved source group. Seat feet still reach z0, a0.012 inset penetration, a minor support approximation. Action: Preserve support/contact repairs while fitting cushion outlines and modular boundaries; do not restore intersecting cylinders.

- **M1-I06 — PARTIALLY_FIXED** (pendant_0..19 / ceiling_slats_glass / ceiling_slats_wall): Actual pendant components now include woven_underside geometry and final renders show some added underside detail. The source fixtures remain much shallower and more intricately patterned; frames45/135/179 show major differences in centers, diameters and ceiling-band layout, while the model reads as repeated concentric bowls. Action: Fit identifiable fixture silhouettes and centers before refining visible underside relief; keep correspondence/count uncertainty explicit.

- **M1-I07 — UNRESOLVED** (floor_black_inset / floor_stone / wall_north / wall_east_main / lighting): All five comparisons lack the strong fine patterned floor highlights/reflections of RGB. The final black inset is a smooth dark mirror with large furniture/window reflections; actual material roughness is0.055 and has no normal-detail nodes. Oak and pale stone also appear flatter and brighter. RGB alone does not determine whether the missing pattern originates in surface relief, reflected ceiling geometry, or lighting. Action: Treat floor/fixture/lighting appearance jointly; match reflection structure and broad tones without baking input imagery.

- **M1-I08 — PARTIALLY_FIXED** (planter_north_left / planter_north_right): Vegetation was shortened and densified (current planter maxima about z1.57/1.58), but final frames0/45/135/179 form low thick yellow leaf bands instead of the source airy fine branches. Frame90 has overly large smooth planter fronts and dense foliage, with different front silhouettes/spacing. Action: Fit planter bodies separately from branch/leaf envelopes using forward and reverse views; retain inferred hidden branches.

## Frame-specific evidence

- **Frame 0:** South furniture is now present but takes substantially more of the lower image; north seats are more separated and differently sized. Bowl foliage is sparse and floor highlights are smooth. Evidence: `inputs/M1/rgb/0000.png` and `models/M1/checks/compare_v2_0000.jpg`.

- **Frame 45:** Mirror cluster is much more exposed than the cropped source cluster. North seating extends too widely; window-side bowl/column alignment and broad metal door faces differ. Pendant arrangement remains mismatched. Evidence: `inputs/M1/rgb/0045.png` and `models/M1/checks/compare_v2_0045.jpg`.

- **Frame 90:** Planter fronts occupy too much of the center and have smooth oversized bodies with dense low foliage. Mirror/wall proportions and column placement differ; open passage exists but its projected appearance remains a narrow strip. Evidence: `inputs/M1/rgb/0090.png` and `models/M1/checks/compare_v2_0090.jpg`.

- **Frame 135:** North seating forms a broad row of separate cylinders rather than the curved fitted source cluster. Foreground furniture occupies more area. Right urn has sparse radial leaves; floor lacks patterned highlights. Evidence: `inputs/M1/rgb/0135.png` and `models/M1/checks/compare_v2_0135.jpg`.

- **Frame 179:** Too much mirror cluster and foreground seating are visible. Bowl/column grouping differs; source fine planter branches become a yellow band. Ceiling fixture distribution and floor reflection structure remain wrong. Evidence: `inputs/M1/rgb/0179.png` and `models/M1/checks/compare_v2_0179.jpg`.

## Verification and limits

- Visually inspected all six original contact sheets, five original RGB images and five actual v2 comparison JPGs at fixed frames0,45,90,135,179. No historical scene or v1 renders opened.
- Read initial issues and author repair evidence in apply_v2_repairs.py, current build/camera scripts, iteration log and manifest; assessed every initial issue against current evidence.
- Ran generic inspect_scene.py in Blender5.2 with factory-startup and disabled autoexec on current scene.blend: PASS;1337 evaluated meshes,308019 triangles, finite coordinates, no missing image dependencies.
- Ran saved final_review_audit.py without rendering:1337 meshes map exactly once to82 semantic records; no custom-property or record-bounds disagreement; no ordering-sensitive exact world-mesh duplicates detected.
- Camera records:180 entries, all valid=false; only fixed five check_render_usable. Packet metadata/intrinsics match. Rotations orthonormal within8.89e-16; saved sample179 CV-to-Blender transform agrees within1.25e-7; focal calibration reconstructs fx762.80002 at1280px.
- Recomputed author-picked landmark RMS residuals at0,45,90,135,179:10.63,58.80,20.93,55.53,64.63 pixels. Landmark sets changed from initial version, so aggregate RMS values are not directly comparable across versions.
- Targeted door leaf/panel box tests,12 doorway rays,9 passage rays,12 wall-collider occupancy checks, compound collider bounds checks, circular cushion test and furniture support bounds; results in final_structural_audit.json.
- Inspected reflective mirror material (metallic1, roughness0.008), semantic components and current construction. No reflected-room duplication identified.
- Parsed actual GLB header/JSON: declared byte length matches15104860 bytes,1337 nodes/meshes,no external buffers; existing GLB load report references current blend hash. This is not a fresh GLB reimport.
- Budget:2 complete scene versions,10 logged completed CPU Cycles checks at12 samples/640x480/4 threads; v2 build log records all five saved renders. Reviewer added0 render attempts/views.
- Recomputed current scene SHA256 after Blender inspection and before writing final review. Packet SHA256 matches manifest.


- RGB-only scale is unobservable and all cameras are inferred/invalid for metric evaluation; no supplied depth or camera poses exist, so model-versus-supplied-depth validation is inapplicable.
- No GT, held-out frames, parent experiment, execution plan, published pages, other method or historical model was accessed; no agents spawned.
- No exhaustive collision, topology, manifoldness, navigation or support verification. Cushion test reports only penetration above0.025 inferred units; exact duplicate test is ordering-sensitive.
- Existing author comparison renders were inspected with current build log and candidate inspection; no new render was made to cryptographically prove each image originated from this candidate.
- Per-object evidence IDs/provenance are registered, but every object and all180 full-resolution frames were not independently verified.
- Geometry/build scripts were not modified. Writes are confined to independent_review. Runtime executables/standard libraries are generic tool infrastructure.
- Author repair evidence is script/log based; absence of a complete issue-response/access update is a provenance limitation, not evidence of a leak.

Author repair/access records lack an issue-by-issue response and v2 access-log update; the final review does not treat this as an input leak. See `final_review.json` and `final_input_access_log.json` for exact read paths and command records.

The candidate is eligible for limited-quality experimental evaluation after the coordinator verifies the exact hash. This review neither freezes nor publishes it.
