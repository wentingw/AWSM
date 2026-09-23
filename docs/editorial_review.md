# Editorial and technical review of the English article

## Verdict

The article is suitable as a research blog draft after the pending result slots are filled from frozen manifests. Its main claim is correctly scoped: Astra is a scene-program author in a measured workflow, not proof that 3D modelling, SLAM, or embodied intelligence has already been overturned.

## Claims checked

- The four methods match the experiment contract. M2 is called near-metric; M3 uses OpenVINS and MapAnything; M4 is explicitly oracle-pose.
- M1’s historical model and Sim(3) registration are labelled supplementary and diagnostic. No native metric pose is attributed to Astra.
- The reported M2 values match results/evaluation/depth/M2_native/depth_metrics.json and results/evaluation/pose/current/report.json: AbsRel 0.0738038, RMSE 0.9331203 m, delta1 0.9428148, pose translation RMSE 0.1175969 m, rotation RMSE 0.3122952 degrees.
- The reported M3 values match the common175 SE(3) report: translation RMSE 2.5945236 m, rotation RMSE 1.1163797 degrees, and 10-second relative translation RMSE 0.7957988 m. The 6.79 m at 180 seconds is a separately labelled first-pose diagnostic, not the global ATE.
- The M3 geometry numbers match surface_metrics.json: model-to-GT mean 0.4590202 m, observed GT-to-model mean 0.7361196 m, symmetric sampled Chamfer 2.8259452 m.
- The 258/195 inventory statement and review failures are supported by the M3 independent review. The article does not convert inventory count into semantic precision or recall.
- New views are described as same-scene synthetic views, not independent real-world generalization.
- Drone and G1 sections deliberately reserve outcome slots and do not claim real hardware transfer, unrestricted language, or GT dynamics transfer.

## Required publication checks

Before publishing, replace every RESULTS_* marker with a generated artifact and preserve the metric definition beside the number. Add M4 final pose/depth results only after its full run and verify the method manifest says oracle pose. Add the final 5x4 figure only after M2/M3/M4 render lighting and camera provenance are frozen. Keep the trajectory labels for M1 supplementary RGB-COLMAP and M4 GT input.

The comparison table must distinguish M1–M4 from direct baselines (ViPE-only, MapAnything-only, and any B1/B2/B2p system). If the table has six systems, do not title it “five methods.” Native frontend depth and rendered model depth must remain separate rows. Report valid coverage and invalid prediction penalties; never silently mask invalid pixels.

The geometry table must state the GT wrapper, sample domain, one global transform, and “no ICP.” Full-scene Chamfer must not be used as object-level semantic accuracy. Include observed-region coverage separately, because the M3 review identifies unsupported space.

The verifier paragraph should remain factual after revisions. If R01 seat contacts, R02 door localization, or R11 lamp collider remain unresolved, say so in the final artifact review. A successful Blender run or collision-free synthetic route cannot be used to infer true friction, mass, inertia, or physical realism.

## Related-work guardrails

Keep primary links and evidence in references/research_sources.json. Hydra, ConceptFusion, and VLMaps are semantic mapping precedents; SceneScript and Real2Code are structured/programmatic neighbours; Holodeck is language-generated environment synthesis; Kitchen Twin and LiteReality-Agent are engineering demonstrations. Do not claim any of them is an identical baseline or attribute results not present in the cited source.

## Editorial quality

The article leads with the measurable contribution, explains the four inputs before discussing implications, and treats failures as evidence. It avoids “industry disruption” as a measured fact and distinguishes capabilities documented by the Astra model page from results measured in this workspace. Before release, link the final figures and result bundle from the site and run a markdown link/marker check.
