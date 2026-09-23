# M4 revision 2 独立视觉复核

结论：**建议修订后再冻结**。整体大厅分区及主要语义类别可对应输入，但近处家具完整性/投影尺度、椅背端面、高盆栽可见性，以及吊灯和门的位置仍有具体问题。本报告只使用允许的 M4 输入与本轮模型输出，不知道真实几何，也不是 GT 精度评测。

亲自查看 comparison_v2.jpg，并以相同显示尺寸复看输入与渲染帧 0、60、90、108、138。新增渲染 0；没有修改模型。

## 优先修正

### M4-R01 · P1 · semantic_completeness

视角：60；对象：lounge_seat_5, lounge_seat_6, lounge_seat_7, missing_foreground_ottoman。

Allowed RGB frame60 shows four separate near-group seating pieces: a left ottoman, two backed chairs, and another round ottoman cut by the bottom edge. The current group has only three semantic objects and the bottom-edge ottoman is absent.

建议：Inspect adjacent permitted views to locate and add the missing foreground ottoman; record its evidence and inferred underside. Preserve the existing supplied camera frame.

可信度：high。

### M4-R02 · P1 · mesh_visibility

视角：0, 60, 138；对象：lounge_seat_5, lounge_seat_7。

Near chairs have solid black wedge/crescent patches at the backrest ends and seat junctions. The RGB has continuous upholstered surfaces there. In build_scene.py the two backrest end caps use the same radial/bottom-to-top winding; the final end cap therefore opposes the expected outward orientation. Bevel interaction may contribute.

建议：Reverse the final backrest end-cap winding, check manifold orientation and bevel intersections, then inspect frames60/138. Treat this as a geometry/normal defect before changing the material.

可信度：high for visible defect; high for inconsistent end-cap winding; exact rendered causal contribution untested。

### M4-R03 · P1 · layout_and_projected_size

视角：0, 60, 138；对象：lounge_seat_5, lounge_seat_6, lounge_seat_7, coffee_table_1。

The near furniture occupies too much of the foreground and has different overlaps. In frame0 the rendered near chair/ottoman extend farther upward and dominate the lower-right corner; in frame138 the table and chair are much more strongly cropped than their RGB counterparts. In frame60 the near tabletop and seats appear wider and bulkier. The far seating group is a closer match.

建议：Refit near-group centers and radii jointly against silhouettes in frames0/60/138 using the existing calibrated rays. Check actual silhouettes and inter-object occlusion, not just one center point. Keep metric uncertainties explicit and do not apply a global scale correction.

可信度：high for projected mismatch; medium for whether placement or dimensions dominate。

### M4-R04 · P1 · object_visibility_and_layout

视角：60, 90；对象：tropical_front_0。

The tall bird-of-paradise planter is a prominent right-edge object in RGB frame60 but is entirely absent from the render. Projecting its exported AABB with the verified frame60 camera gives x=551.6..736.9 at width518, wholly beyond the right edge. It exists in the reverse-view model, so this is a placement/extent issue rather than a missing category.

建议：Reconcile tropical_front_0 placement and plant/container silhouette using frame60 plus adjacent/reverse permitted RGB views. Restore its right-edge visibility without moving the input camera.

可信度：high。

### M4-R05 · P2 · ceiling_layout_and_size

视角：0, 60, 90, 108, 138；对象：pendant_00..pendant_13, pendant_front_00, pendant_front_02, pendant_front_04, pendant_reverse_0, pendant_reverse_2, pendant_reverse_6。

Pendant projected centers, overlap and apparent diameters remain visibly inconsistent across the five views. Frame108 RGB contains several broad overlapping foreground bowls, whereas the model has a different set of smaller/lower-looking bowls and greater empty gaps. Frame60 has extra clustered fixtures toward the upper left and different isolated bowl positions. This is apparent before evaluating wicker detail or brightness.

建议：Prioritize a few unambiguous multi-view pendant correspondences, with explicit accepted/rejected matches. Verify the same fixtures in both forward and reverse views and retain unresolved identity/height uncertainty rather than adding fixtures from a single view alone.

可信度：high for screen-space mismatch; individual correspondence and true 3D position remain uncertain。

### M4-R06 · P2 · opening_layout_and_silhouette

视角：108；对象：glazed_double_door_0, glazed_double_door_1, curtain_wall。

The main door has noticeably narrower projected frame/stiles than RGB. The model also shows part of another brass door on the extreme left of frame108, where the RGB shows plain glazing. Current door0 AABB projects to x=-56.8..31.3, explaining that additional visible edge.

建议：Recheck both door centers and widths against permitted views, including the main door silhouette at108 and the second door in other views. Increase stile/rail silhouette only as supported by RGB; verify door0 should lie outside this view or change its position accordingly.

可信度：high for visible mismatch; medium for exact dimensional correction。

### M4-R07 · P3 · collision_contact_surface

视角：接口/元数据；对象：floor_stone, floor_dark_inset。

The role=floor collider is present and valid, but its top is z=0.025m, while visible floor_dark_inset reaches about z=0.041m and has no collider. Therefore a generic contact consumer will place objects about16mm below that visible finish unless it handles this offset.

建议：Either include the visible finish in the collision floor surface or document the 16mm render-versus-contact offset explicitly. This is a contact-interface limitation, not a failed dynamic-physics test.

可信度：high; numerical metadata check。

### M4-R08 · P3 · semantic_metadata_and_uncertainty

视角：接口/元数据；对象：coffee_table_0, coffee_table_1, round_wall_mirror_0..9, pendant lights, potted plants。

All74 records contain required fields, but only10 have nonempty spatial_relations and most geometry_provenance text is generic. Important obvious support/mounting relations are absent. Numeric uncertainty values0.12/0.2/0.6m have no calibration or estimation method attached. The manifest correctly avoids a quantitative fidelity claim.

建议：Add supported_by/mounted_on/suspended_from relations where observed, and label uncertainty numbers as heuristic author estimates unless an estimation method is supplied. Where feasible link measured objects to the specific source measurement record, not only a frame list.

可信度：high。

### M4-R09 · P3 · appearance_after_geometry

视角：0, 60, 90, 108, 138；对象：floor_dark_inset, coffee_table_1, pendant lights, lounge seats。

The model floor and tabletop have blurred broad reflections, the RGB floor has crisp gold pattern and concentrated light reflections, and the chair fabric is flatter/brighter. Pendant central white discs are much more prominent in the render. These are secondary to the layout, completeness and chair mesh problems above.

建议：After geometry fixes, tune roughness, light/diffuser appearance and upholstery microstructure from permitted RGB; keep all inferred material/light properties identified as such.

可信度：high。

## 输入与接口核对

- 9 项规定产物全部存在且非空；74 个语义对象 ID 唯一，必需字段齐全，bounds 为有效的有限 2×3 数组。
- 35 个碰撞体全部关联已有对象，bounds 与对象逐一相同；floor_stone 明确具有 role=floor。AABB 包含植物与曲面空隙的保守性质已有披露。
- 180 组相机 K、camera_to_world 和图像尺寸与 packet geometry 完全一致；180 RGB + 180 geometry 的哈希独立重算全部匹配。
- 输入到模型的变换为单位矩阵，单位 m，Z 向上；相机 OpenCV→Blender 转换和 GLB 原生 Z-up 导出在源码/manifest 中一致。
- GLB 头和字节长度有效，包含 74 个语义根节点，没有缺失的 object_id。未直接重算 BLEND 中所有几何边界。
- 已检查 input_access_log 的 1051 条声明记录，均在允许输入或本模型目录内；日志核对不能替代独立系统访问审计。
- 摩擦/恢复系数明确标为假设、未测量；manifest 没有定量保真声明。0.12/0.2/0.6 m 不确定度应说明属于启发式估计；未做动态物理验证。
- 修订预算记录为 2/5，已有检查视角 10/60；本复核没有新增渲染。

主修顺序：缺失圆凳 → 椅背端面 → frame60 高盆栽 → 近处家具投影 → 门位置/轮廓 → 吊灯跨视角一致性。外观与元数据补充随后处理。

完整结构化结果及本次所审产物 SHA-256 见 review.json。
