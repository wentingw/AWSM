# M2 clean-review response — final revision 5

Status: `frozen_for_independent_GT_evaluation`. All changes used the existing permitted RGB/ViPE evidence and this clean review; no GT was read.

- **M2-R1 — addressed**: Included each fixed table disk in iterative seat clearance constraints; preserved table centers. Reduced uncertain foreground seat radii 12% from RGB evidence. Per-seat displacements recorded in object attributes.
- **M2-R2 — addressed**: Recalculated the existing closed reception mesh winding outward; no vertex position or dimensions changed.
- **M2-R3 — addressed_static_closed_door**: Split fixed window colliders around the portal. Added two explicit static closed glass leaves and separate fixed frame colliders. Opening motion and threshold traversability are not claimed.
- **M2-R4 — addressed_geometry_with_reflection_residual**: Refit ten circles personally identified in legal frame65 RGB to the same wall plane through supplied camera rays; crossed against frames0 and85. Removed unsupported extra circle.
- **M2-R5 — addressed**: Stored legal Blender pixel aspect (fy/fx,1), avoiding Blender clamp on values below1. Exact GLB perspective fields encode supplied fx/fy without extrinsic or world transform changes.

Actual Blender checks: minimum seat–table clearance 0.0406 m, minimum seat–seat clearance 0.0470 m; reception desk closed manifold with positive signed volume 1.5007 m³; fixed window portal sample clear while the static closed leaf blocks the door sample. Camera JSON SHA is unchanged from revision 3; GLB intrinsic error is 0 px to numeric precision.

All five final views were personally inspected in `checks_v5`. These are local checks after an independent clean review; the corrected scene has not received a second independent review.

Unresolved:

- Native ViPE depth and pose disagreement remains; reflective surfaces and distant geometry are not exact metric truth.
- Planter vegetation remains denser/taller than source RGB and botanical species are inferred.
- Dark floor inlay has overly strong linear reflections compared with source fine weave and light-dot pattern.
- Strong wall-floor dark seam remains visible; cause was not isolated in remaining engineering budget.
- Mirror reflected content/contrast, particularly frame85, remains approximate despite corrected landmark geometry.
- Several inferred lathed pots/bowls have open boundary loops; hidden thickness and undersides remain approximate.
- Entry is modelled as a static closed door; no opening animation or demonstrated traversable threshold is provided.
- Unobserved wall backs, joins, foreground closure and physical coefficients remain inferred.
