# Bundled model assets

## silero_vad.onnx

- **What**: Silero VAD v5 voice-activity-detection model (ONNX opset 16, 8 kHz + 16 kHz).
- **Source**: https://github.com/snakers4/silero-vad (tag `v5.1.2`, `src/silero_vad/data/silero_vad.onnx`).
- **License**: MIT (Silero Team).
- **SHA-256**: `2623a2953f6ff3d2c1e61740c6cdb7168133479b267dfef114a4a3cc5bdd788f`
- **Why vendored**: production containers run behind a Cloudflare tunnel with no
  egress for runtime downloads, and bundling the 2.3 MB model avoids a torch
  dependency (the official `silero-vad` pip package hard-requires torch).
  Inference runs through `onnxruntime` — see `api/services/segmentation.py`.
