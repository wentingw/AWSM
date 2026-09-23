# Publication layout

Recommended: **GitHub Pages for the bilingual article; Hugging Face for full model and experiment assets.** The completed static site is `dist/`, with relative URLs and no backend. GitHub history keeps text, plots, protocols and code reviewable. Hugging Face supports versioned downloads of larger `.blend`, `.glb`, trajectory and evaluation bundles without placing those files in the article repository.

The site already includes lightweight display GLBs and demonstration videos, so it remains functional before a Hugging Face repository is connected. Publishing the entire workspace is unnecessary: raw capture, runtime environments and old private project material are not part of the deployment bundle.

## GitHub Pages

The published site uses a **new public repository**, with Pages serving the root of the `main` branch. This deployment needs only public-repository authorization; it does not request private-repository or workflow permissions. The publish operation verifies the prepared site's hashes, commits an isolated copy, pushes it, and enables Pages through the GitHub API.

A project URL can later use a custom domain. All internal links are relative so the project path works. Existing projects and Pages deployments are not overwritten. The local GitHub Actions scaffold is optional and is not uploaded by the branch-deployment publisher.

## Hugging Face

`publish/huggingface_assets/README.md` is the prepared asset-repository card. `publish/model_asset_manifest.json` lists the full frozen Blender/GLB model paths and hashes; these are separate from the cutaway display copies. Upload selected frozen artifacts and evaluation reports under method-specific paths to a new HF model/data repository, then add immutable-revision links in the blog. An interactive Space is optional because the article already provides a static browser-based 3D viewer.

The packaging script itself performs no remote writes. Publication uses separate authenticated scripts. The selected GitHub account is `wentingw`; the prior `wtishere` authorization session was canceled before any GitHub repository was created. The HF assets are public at https://huggingface.co/datasets/Ooliva/astra-world-model-blog, frozen revision `241d313a264a3353bcb87f9fde30f7ef8a6f5bce`. The blog target is https://wentingw.github.io/astra-world-model-blog/. The local publication records store commit IDs and verification results without credentials.
