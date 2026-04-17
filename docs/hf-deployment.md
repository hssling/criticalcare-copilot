# Hugging Face Deployment

## Model repo
1. Train & merge adapter (or push adapter-only).
2. `python hf/publish_model.py --path <dir> --repo $HF_ORG/$HF_MODEL_REPO`.
3. Model card auto-generated from `eval/reports/latest.json` and `docs/model-card-template.md` via `hf/generate_model_card.py`.

## Inference Endpoint
1. Create a **private** Inference Endpoint pointing at the model repo.
2. Recommended: accelerator with ≥24GB VRAM for merged E4B; A10G / L4 tier.
3. Set custom handler if using adapter-only repo.
4. Copy the endpoint URL to `HF_ENDPOINT_URL` in Netlify env.
5. Copy a fine-grained token (inference only) to `HF_API_TOKEN`.

## Space demo
`hf/space_app.py` provides a minimal Gradio UI with a clear clinical disclaimer and a sample-case picker. Do NOT deploy Spaces with real PHI input.

```bash
huggingface-cli repo create $HF_ORG/$HF_MODEL_REPO-demo --type space --space_sdk gradio
git init && git remote add space https://huggingface.co/spaces/$HF_ORG/$HF_MODEL_REPO-demo
cp hf/space_app.py app.py
git add app.py && git commit -m "init space" && git push space main
```

## Dataset repo
Publish only benchmark summaries and safe synthetic examples. Never push PHI or restricted data. See `data/builders/` for output shape.

## Rotating tokens
- Use fine-grained tokens scoped per environment.
- Rotate quarterly or on any suspected leak.
- Update Netlify env → redeploy (Netlify re-injects on next function cold start).
