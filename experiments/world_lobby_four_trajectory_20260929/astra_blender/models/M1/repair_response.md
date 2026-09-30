# M1 v2 repair record

Coordinator summary of the original author's completed v2 and independent final-review evidence. This is not a retroactive author declaration. Geometry was unchanged.

## M1-I01 — PARTIALLY_FIXED

Foreground south furniture and right-wall mirrors now enter the forward views. Composition remains materially wrong: frame 0 shows much more foreground furniture; frames 45/179 show substantially more mirror cluster; frame 135 shows a wider, separated north seating arrangement and changed floor/wall perspective; frame 90 has changed planter/wall/column proportions. Current author-picked mirror_smalltop residuals are 178.25, 153.85 and 188.65 pixels at 45,135,179. These are recomputed conditional landmark errors, not independent pixel measurements.

## M1-I02 — PARTIALLY_FIXED

North bowl position improves: grass_N residuals are 3.92,4.29,26.95,36.79 pixels at 0,45,135,179. However, the final render has a shallow wide bowl with sparse radial blades and exposed dark soil; RGB has a fuller dense tuft and deeper-looking bowl. In 45/179 the column/bowl grouping still differs; column_base residuals are 69.20/60.33 pixels.

## M1-I03 — PARTIALLY_FIXED

Confirmed topology repair: passage_south replaces the closed south leaf, nine rays at y=4.4/4.8/5.2 and z=0.3/1.0/1.8 travel from x=7.0 to8.6 without a hit; no closed-door leaf intersects an east-wall panel in the targeted box test. Door semantics and clear jamb splits exist. Visual placement/width remain approximate: at frame90 the wall opening is a narrow dark strip, and at45/179 broad source metal-door surfaces are not reproduced.

## M1-I04 — FIXED_IN_TARGETED_CHECKS

East-wall colliders are now compound solid-component boxes. All12 sampled doorway points at z1 are free of wall parts; all compound-part bounds match actual inspected mesh bounds within1e-4. Passage return/lintel parts preserve its interior; closed door leaves have separate records.

## M1-I05 — PARTIALLY_FIXED

The circular cushion test now reports no penetrations greater than0.025 inferred units. Both table minima are z0.011999995 against inset top0.012, resolving the prior unsupported gap. Visual modular shape is unresolved: frames0/45/135/179 show separated cylindrical stools and straight-backed chairs instead of the tightly fitted curved source group. Seat feet still reach z0, a0.012 inset penetration, a minor support approximation.

## M1-I06 — PARTIALLY_FIXED

Actual pendant components now include woven_underside geometry and final renders show some added underside detail. The source fixtures remain much shallower and more intricately patterned; frames45/135/179 show major differences in centers, diameters and ceiling-band layout, while the model reads as repeated concentric bowls.

## M1-I07 — UNRESOLVED

All five comparisons lack the strong fine patterned floor highlights/reflections of RGB. The final black inset is a smooth dark mirror with large furniture/window reflections; actual material roughness is0.055 and has no normal-detail nodes. Oak and pale stone also appear flatter and brighter. RGB alone does not determine whether the missing pattern originates in surface relief, reflected ceiling geometry, or lighting.

## M1-I08 — PARTIALLY_FIXED

Vegetation was shortened and densified (current planter maxima about z1.57/1.58), but final frames0/45/135/179 form low thick yellow leaf bands instead of the source airy fine branches. Frame90 has overly large smooth planter fronts and dense foliage, with different front silhouettes/spacing.
