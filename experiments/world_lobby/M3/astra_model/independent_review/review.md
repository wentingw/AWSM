# M3 independent clean review — revision 2

结论：需要修复语义、局部布局与元数据；输入几何冲突已有诚实记录。本报告不含 GT 几何反馈。

仅阅读合同、M3 packet 及其 RGB/depth/poses、当前 astra_model 输出。亲自检查 render_contact_r2.jpg，并逐一对比 frame 5、60、90、105、126 的合法原图与 r2 渲染。未读其他方法、旧模型或评测；额外 CPU 渲染 0；未改模型。

已通过的核对：所有必需输出存在；175 个导出相机与 packet 位姿逐值一致；四份 T_input_model 均为 identity；floor top 在 manifest/plan/collider 中均为 -2.5382169319971153 m，与 objects 中 bounds 相差约 1.36e-7 m。独立从输入深度重算 5/90/105/126 帧地面 mode，结果与日志完全一致。原生深度冲突没有被缩放或坐标变换掩盖。2 次完整修订、10 张工具检查渲染，含 5 个独立输入视角。

计数应写为 **258 个命名模型元素**，其中 **195 个 trim、63 个非 trim 条目**；后者包括 10 个建筑实体与 53 个其他条目。此为模型库存统计，不是经证据核实的真实物体实例数，更不是 258 个语义物体重建成绩。

## R01 P1 — physical_layout

Views: 5, 60, 90, 126. Objects: seat_middle_left_back, seat_middle_center, seat_middle_right_front, seat_middle_right_back, seat_front_left, seat_front_center, seat_front_right.

Five pairs of generated seat cylinders physically intersect. This is established from the cylinder radii and overlapping height intervals in build_scene.py, not merely from conservative AABB overlap.

Repair: Resolve seat contacts by small, explicitly logged shape/placement changes within the uncertain furniture group; check the same RGB views. Re-export object bounds and colliders. Do not change packet poses or scale to hide the issue.

Repair level: `local_layout_revision`.

| Seat pair | Radial penetration (m) | Vertical overlap (m) |
|---|---:|---:|
| seat_middle_left_back / seat_middle_center | 0.095464 | 0.268750 |
| seat_middle_center / seat_middle_right_front | 0.020841 | 0.291500 |
| seat_middle_right_front / seat_middle_right_back | 0.088846 | 0.268750 |
| seat_front_left / seat_front_center | 0.106191 | 0.279750 |
| seat_front_center / seat_front_right | 0.066428 | 0.495000 |

These are overlaps of the actual generated seat cylinders, not an AABB-only warning.

## R02 P1 — same_view_layout

Views: 105, 126. Objects: glazed_door_-20.3, window_column_-18.8, reception.

Frame105 original double door is near horizontal image center; model door is much farther right, beside a column that is also displaced. Frame126 shows the same mismatch in the near column/door/reception relationship. The reception fills more of the right render and lacks the observed angled front.

Repair: Prioritize door/column/reception correspondences in 105 and 126 using only permitted RGB and supplied measurements. Preserve conflicting alternatives when a consistent localization cannot be established. This review supplies no target world coordinates.

Repair level: `multi_view_localization_or_explicit_unresolved`.

## R03 P1 — semantic_shape

Views: 105, 126. Objects: reception.

The observed reception has a strongly folded, angular front and visible counter opening/top structure; the rendered model is nearly a plain tall rectangular prism. Parametric code introduces only small corner offsets and does not recover the visually identifying faceted silhouette.

Repair: Model the visible front facets and counter top/opening from RGB as named parts of one reception object; retain inferred backsides separately. Distinguish this shape error from uncertain metric position.

Repair level: `local_geometry_revision`.

## R04 P1 — semantic_accounting

Views: metadata. Objects: inventory / scene graph.

modelling_manifest.json and artifact_checks.json call all 258 entries semantic_objects. Of these, 195 are category trim (mullions, panel joints, door frames and ceiling slats). Only 63 entries remain after excluding trim; these still include architecture and individually enumerated fixtures. They are not 258 independently observed scene-object instances.

Repair: Report 258 named model elements, 195 trim/structural-detail elements, 10 architectural entities and 53 other non-trim entries. These are model inventory counts, not verified object detection/coverage scores. Group parts with explicit parent or part_of relations; any count of real instances requires separate evidence-based correspondence.

Repair level: `metadata_only`.

## R05 P1 — navigation_unknown_extent

Views: 5, 60, 90, 105. Objects: mirror_wall, floor.

The mirror-side wall is intentionally absent beyond x=-13.5 while the floor and some objects continue there. README correctly calls this unknown environment, but colliders.json exposes only floor/obstacle AABBs and has no machine-readable unknown-region boundary. A consumer using only colliders could interpret the open missing side as free space.

Repair: Represent unsupported enclosure/unknown space explicitly, or mark this collision layer as unsuitable for navigation beyond observed support. Do not invent a closure that contradicts the camera path.

Repair level: `metadata_or_layout_layer`.

## R06 P2 — visible_semantic_omission

Views: 5, 60, 126. Objects: table_middle, reception_wall_emblem.

The small bowl on the middle coffee table is visible in original frames5 and60 and absent in the model. The reception wall has a white shield-like emblem plus a large dark U-shaped surrounding feature in frames5/126; the model retains only a small low-contrast rectangle and omits the surrounding feature.

Repair: Add a table-bowl instance and the visibly supported emblem components, or explicitly list them as omitted. Keep the emblem parts grouped as one wall installation, not independent scene-object credit.

Repair level: `local_semantic_addition`.

## R07 P2 — vegetation_semantics

Views: 5, 60, 90, 126. Objects: planter_window_mid, planter_mirror, planter_front_tall, planter_center_left, planter_center_right.

Several distinct vegetation forms become generic broad-leaf clumps or sparse round yellow leaves: window-side plant is fine grass-like foliage, mirror-side pot has fine bushy foliage, and frame60 tall planter has long upright leaves with an orange flower. This loses visible semantic distinctions even though containers are present.

Repair: Use a small number of appropriate leaf/blade/branch primitives per planter. The tall planter should retain its visible flower/leaf silhouette. Do not count foliage primitives as object instances.

Repair level: `local_geometry_revision`.

## R08 P2 — appearance_and_fixture_shape

Views: 5, 60, 90, 105, 126. Objects: carpet_main, window_wall, pendant_light.

Original dark floor inset has bright rectangular pattern and strong reflections; render looks like a matte dark carpet. The original pendant shades have open woven geometry, while the model has smooth closed gold dishes. Thin pale window mullions also understate the dark original frame. These are conspicuous in all reviewed views.

Repair: Keep floor material interpretation uncertain (category carpet is not established by RGB alone); improve visible pattern/specularity and pendant open-weave silhouette within budget. Record remaining simplifications.

Repair level: `local_material_and_shape_revision`.

## R09 P2 — provenance_consistency

Views: 5, 60, 90, 105, 126. Objects: ceiling, table_middle, seat_middle_left_front, seat_middle_left_back, seat_middle_center, seat_middle_right_front, seat_middle_right_back, planter_back_corner.

Conflict handling is honest in prose and retains measurements, but several machine fields contradict that prose: table_middle has conflicting_input_preserved=false while its selection_rule explicitly says frame5 depth conflicts; central-seat rules state low confidence but confidence remains medium. Ceiling provenance repeats the floor-median regularization text.

Repair: Define conflict-flag semantics, use an explicit conflict_present field, align confidence with the stated uncertainty, and describe the actual ceiling selection rule. Keep all retained native measurements.

Repair level: `metadata_only`.

## R10 P2 — scene_relations

Views: metadata. Objects: inventory / scene graph.

All 258 objects have only inside -> lobby, but lobby is not an exported semantic entity. There are no part_of, supported_by or furniture-group relations despite the substantial component inventory.

Repair: Declare a lobby scene root and meaningful part_of/support/group relations without inflating object counts. Ensure every relation target resolves.

Repair level: `metadata_only`.

## R11 P2 — collision_coverage

Views: 5, 60. Objects: floor_lamp_0, floor_lamp_1.

Each floor lamp has a 0.55 m diameter shade but only a 0.25 by 0.25 m collider over the whole height. Thus the global claim of conservative AABB hard bodies does not cover the complete visible lamp.

Repair: Use separate base/stand/shade colliders or declare shade exclusion explicitly; do not call the current full lamp collider conservative.

Repair level: `collider_or_metadata_only`.

## Limits and interpretation

The supplied depths support the reported inconsistency, and the unmodeled mirror-wall continuation is honestly disclosed. That does not excuse independent local errors such as interpenetrating seats, omitted visible objects, or contradictory metadata. No target world coordinates are proposed from outside permitted evidence.

The input-access log lists camera_imu.json as an explicitly authorized calibration source. It was not opened by this reviewer; session authorization cannot be verified from these permitted artifacts alone. The access log is a declaration, not a complete external audit.

优先修复 R01，并修正计数/关系/冲突字段；105/126 门柱前台定位若仍受输入冲突限制，应具体保留为未解决项。若冻结当前版本，应同时冻结这些缺陷，不宜宣称物理一致、导航可用或完整准确重建。
