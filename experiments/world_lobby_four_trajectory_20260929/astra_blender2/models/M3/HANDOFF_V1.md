M3 initial v1 is ready for independent review; status LIMITED and not frozen.

Artifacts: scene.blend, scene.glb, build_scene.py, layout.json; 79 semantic objects /788 mesh components. Native metric scale1 and exact180 cameras under recorded rigid transform. Required JSON records, measurements and v1 snapshots included.

Ten paired checks: 33,61,74,82,91,100,108,118,129,155; CPU Cycles12 samples640x480. All comparisons actually inspected. Predicted DA3 comparison MAE0.819m, AbsRel0.126, coverage99.943%. One full180 BVH input pass: MAE1.586m, AbsRel0.858, coverage99.950%. These compare against own predicted DA3, never ground truth. All hashes match scene.blend. Artifact inspection and GLB semantic mapping reports PASS.

Known problems and concrete regions/residuals: analysis/observed_issues_v1.json and analysis/paired_region_residuals_v1.json. Priorities: flat mirror and tabletop cap normals, chair back proportions/orientations, misplaced pendants, sparse shrubs, over-pale walls and rippled floor reflections, uncertain column/desk/crest placement. Preserve input contradictions, especially late-frame depth outliers; do not optimize one aggregate score.

Execution provenance limitation: the paired-helper invocation visible to this author returned already-complete. Matching current-v1 paired/full180/artifact reports were found in own output, and their original creating calls are not visible in this author transcript. Actual model/RGB/depth hashes, indices and180-frame count were verified. No attribution of those invocations is asserted. No duplicate render or full input pass was launched. visualize_checks was explicitly run successfully on saved pairs. See input_access_log.json.

Stop after initial phase. No repairs, self-certification, independent review or freeze performed. Remaining: independent review, requested evidence-grounded repairs, two further full180 passes, independent final review.
