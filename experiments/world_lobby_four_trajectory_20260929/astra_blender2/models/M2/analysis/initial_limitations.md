Initial M2 candidate: technical artifacts PASS; visual fidelity LIMITED.

- Pendant radial rods and plant stems appear vertical in actual renders; likely rotation-mode order bug in rod(); repair geometry orientation next version.
- Cylinder end-cap smooth shading makes flat mirror disks and table tops appear curved; flatten cap normals next version.
- V1 material exposure too bright and floor surface roughness/bump too high; compare all ten RGBs when revising.
- Reception desk intrudes in100/108; needs multi-view silhouette triangulation or constrained positioning.
- Light positions from single33 depth disagree with82/129; use multiple source rays for major repair if correspondence reliable.
- Panel gaps produce thin BVH misses; inferred backing wall can close gaps while keeping panels.
- Window door frames too thin; column position and chair extents conflict across native pose/depth input.
- Plant detail is sparse and approximate; full source appearance is not reconstructed.
- Native input is inconsistent across views; no scale, camera edits or score-targeting transformations applied.

All ten comparison sheets inspected. Exact cameras preserved; this is own predicted DA3 consistency, not ground truth.
