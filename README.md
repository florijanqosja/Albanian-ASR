# Albanian Transcriber using Machine Learning | DibraSpeaks

<p align="center">
  <img src="https://github.com/florijanqosja/Albanian-ASR/assets/55300217/8d2dec67-b6d0-47c4-8107-7ff4cd834411" alt="Logo" width="200">
</p>

This project is an AI-based transcription tool for the Albanian language. It includes a web interface for labeling and validating speech data, and an API for processing audio.

## Features

- Automatic speech recognition for Albanian language.
- User-friendly interface to label and validate speech data.
- Dataset management tools.

## Utterance Segmentation

Uploaded media is segmented into labeling-ready utterances by
`api/services/segmentation.py`:

1. Audio is decoded to 16 kHz mono via ffmpeg.
2. Speech is detected with [Silero VAD](https://github.com/snakers4/silero-vad)
   (ONNX model vendored in `api/assets/`, runs on CPU via onnxruntime — no
   torch dependency), so music, jingles, and silence never enter the labeling
   queue.
3. Speech regions are assembled into 1–15 s utterances (short regions merged
   across small pauses, overlong regions split at the least-speech-like frame).
4. Near-silent, clipped, or mostly non-speech segments are rejected.
5. Each utterance is exported as 16 kHz mono 16-bit PCM WAV — the exact format
   the training pipeline consumes.

Tuning knobs are environment variables documented in `.env.example`
(`SEGMENTER_*`). The labeled corpus can be exported as a training manifest via
`GET /dataset/export` (NeMo-style JSONL or LJSpeech-style CSV).

## Project Structure

- `api/`: FastAPI backend service.
- `web/`: React frontend application.
- `scripts/`: Utility scripts for data processing and automation.
- `notebooks/`: Jupyter notebooks for model training and experiments.

## Getting Started

### Prerequisites

- Docker and Docker Compose

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/florijanqosja/Albanian-ASR.git
    cd Albanian-ASR
    ```

2.  Set up environment variables:
    ```bash
    cp .env.example .env
    ```

3.  Run the application:
    ```bash
    docker-compose up --build -d
    ```

4.  Access the services:
    - **Web Interface**: [http://localhost:3000](http://localhost:3000)
    - **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
