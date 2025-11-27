# Contributing to Albanian-ASR

Thank you for your interest in contributing to Albanian-ASR! We welcome contributions from everyone.

## Getting Started

1.  **Fork the repository** on GitHub.
2.  **Clone your fork** locally:
    ```bash
    git clone https://github.com/your-username/Albanian-ASR.git
    cd Albanian-ASR
    ```
3.  **Set up environment variables**:
    ```bash
    cp .env.example .env
    ```
    Adjust the values in `.env` if necessary.

4.  **Run with Docker**:
    ```bash
    docker-compose up --build
    ```
    The API will be available at `http://localhost:8000` and the Web UI at `http://localhost:3000`.

## Development Workflow

1.  Create a new branch for your feature or fix:
    ```bash
    git checkout -b feature/my-new-feature
    ```
2.  Make your changes.
3.  Ensure everything works by running the project locally.
4.  Commit your changes with clear messages.
5.  Push to your fork and submit a Pull Request.

## Code Style

*   **Python**: Follow PEP 8 guidelines.
*   **JavaScript/React**: Follow standard React best practices.

## Reporting Issues

If you find a bug or have a feature request, please open an issue on GitHub.
