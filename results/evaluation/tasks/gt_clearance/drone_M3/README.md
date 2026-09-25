# Drone M3 GT static clearance audit

Audits all 20 readable `drone_trajectory.csv` files against the authorized 9,984,967-triangle metric GT USD wrapper after the supplied M3 registration transform. Each value is the nearest triangle-surface distance from the logged drone center. `potential_overlap_lt_0p30m` is a descriptive center-to-surface flag using a spherical 0.30 m approximation; it is not a collision result and does not test whether a point is inside the GT mesh. No dynamics are replayed.
