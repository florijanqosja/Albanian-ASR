# Albanian-ASR (DibraSpeaks) AI Instructions

## Project Overview
This is an AI-based transcription tool for the Albanian language, consisting of a **React frontend** (`web/`) and a **FastAPI backend** (`api/`), orchestrated via **Docker Compose**.

## Architecture & Data Flow
- **Frontend (`web/`)**: React 17 application using `styled-components` and `axios`. Interacts with the API to upload files and validate transcriptions.
- **Backend (`api/`)**: FastAPI service handling audio/video processing (`moviepy`, `pydub`, `librosa`), database interactions, and file management.
- **Database**: PostgreSQL storing metadata about videos, splices, and validations.
- **File Storage**: Audio/video files are stored in `audio_files/` (mounted as volumes in Docker) and processed into `mp3`, `mp4`, and `splices` directories.

## Development Workflow
- **Primary Run Command**: `docker-compose up --build` (starts Web on :3000, API on :8000, DB on :5432).
- **Frontend Local Dev**: `cd web && npm start` (requires running API separately or via Docker).
- **Backend Local Dev**: `cd api && uvicorn main:app --reload` (requires local DB or connection to Docker DB).
- **Environment**: Configuration is managed via `.env` files. Ensure `REACT_APP_API_DOMAIN_LOCAL` matches the API URL.

## Code Style & Conventions
Refer to `STANDARDS.md` for detailed rules.
- **Python (Backend)**:
  - **Style**: PEP 8, `snake_case` for functions/vars, `PascalCase` for classes.
  - **Typing**: Strict type hinting in function signatures.
  - **ORM**: SQLAlchemy with `snake_case` database columns.
- **JavaScript (Frontend)**:
  - **Style**: `camelCase` for functions/vars, `PascalCase` for components.
  - **Structure**: Components in `src/components/`, Screens in `src/screens/`.
  - **Linting**: ESLint + Prettier.

## Key Files & Directories
- **`api/main.py`**: Application entry point, API routes, and static file configuration.
- **`api/database/`**: Contains `models.py` (DB tables), `schemas.py` (Pydantic models), and `services.py` (business logic).
- **`web/src/App.js`**: Main frontend router and layout.
- **`web/src/components/Sections/`**: Core UI sections like `Audioplayer.jsx` and `Audiovalidate.jsx`.
- **`docker-compose.yml`**: Defines service orchestration and volume mappings.

## Common Tasks
- **Adding an API Endpoint**:
  1. Define the Pydantic schema in `api/database/schemas.py`.
  2. Add the CRUD logic in `api/database/services.py`.
  3. Create the route in `api/main.py`.
- **Database Changes**:
  - Modify `api/database/models.py`. Note: No Alembic detected; schema changes may require manual DB updates or container resets in dev.
- **Audio Processing**:
  - Logic for splitting/converting audio resides in `api/main.py` or `scripts/`. Ensure `audio_files/` directory structure is respected.

## UI & Design Guidelines
- **Design System (MUI Treasury)**:
  - **Primary Reference**: [MUI Treasury](https://www.mui-treasury.com/).
  - **Directive**: All frontend development must follow the patterns, aesthetics, and component designs from MUI Treasury.
  - **Implementation**: Use the installed `@material-ui/core` (v4) library to implement these designs.
- **Styling Strategy**:
  - Use `styled-components` for custom layouts or when wrapping MUI components.
  - Adopt MUI's styling solution (JSS/makeStyles) if copying components directly from MUI Treasury examples, but ensure consistency.
- **Global Theme**:
  - **Colors**:
    - **Primary**: `#A64D4A` (Soft Red)
    - **Text**: `#404040` (Neutral Dark Gray)
    - **Background**: `#ffffff` (White)
    - **Accent**: `#FFE4E6` (Soft Rose)
    - **Secondary/Muted**: `#F3F4F6` (Light Gray)
    - **Border**: `#FECACA` (Light Red)
  - **Typography**: `Khula` font family.
- **Component Reuse**:
  - Prioritize implementing components from MUI Treasury over creating custom ones from scratch.
  - Refactor existing components to match MUI Treasury styles when touching them.
