# G1 M3 GT static clearance audit

This is an independent static geometry audit. It imports only the metric GT USD wrapper and uses `results/M3/model_registration.json` to map G1 trajectory points into GT coordinates. It audits 18 successful G1 trajectories with torso, head, and fixed foot proxy points against a GT triangle BVH. The 12 planning failures have no motion trajectory and are omitted without fabrication.

Nearest-surface distances do not test inside/outside and do not replay MuJoCo dynamics. Foot values are fixed-offset proxies from the logged base pose; the GT floor estimate is the 0.5th percentile of GT mesh vertices and is only a height reference. This report makes no GT collision-transfer or real-world claim.
