# Albanian-ASR (DibraSpeaks) AI Instructions

## Project Overview
This is an AI-based transcription tool for the Albanian language, consisting of a **React frontend** (`web/`) and a **FastAPI backend** (`api/`), orchestrated via **Docker Compose**.

## Architecture & Data Flow
- **Frontend (`web/`)**: Next.js application using `styled-components`, Tailwind CSS, and `axios`. Interacts with the API to upload files and validate transcriptions.
- **Backend (`api/`)**: FastAPI service handling audio/video processing (`moviepy`, `pydub`, `librosa`), database interactions, and file management.
- **Database**: PostgreSQL storing metadata about videos, splices, and validations.
- **File Storage**: Audio/video files are stored in `audio_files/` (mounted as volumes in Docker) and processed into `mp3`, `mp4`, and `splices` directories.

## Development Workflow
- **Primary Run Command**: `docker-compose up --build` (starts Web on :3000, API on :8000, DB on :5432).
- **Frontend Local Dev**: `cd web && npm run dev` (requires running API separately or via Docker).
- **Backend Local Dev**: `cd api && uvicorn main:app --reload` (requires local DB or connection to Docker DB).
- **Environment**: Configuration is managed via `.env` files. Ensure `REACT_APP_API_DOMAIN_LOCAL` matches the API URL.

## Code Style & Conventions
Refer to `STANDARDS.md` for detailed rules.
- **Python (Backend)**:
  - **Style**: PEP 8, `snake_case` for functions/vars, `PascalCase` for classes.
  - **Typing**: Strict type hinting in function signatures.
  - **ORM**: SQLAlchemy with `snake_case` database columns.
- **JavaScript/TypeScript (Frontend)**:
  - **Style**: `camelCase` for functions/vars, `PascalCase` for components.
  - **Structure**: Components in `src/components/`, Pages in `app/`.
  - **Linting**: ESLint + Prettier.

## Key Files & Directories
- **`api/main.py`**: Application entry point, API routes, and static file configuration.
- **`api/database/`**: Contains `models.py` (DB tables), `schemas.py` (Pydantic models), and `services.py` (business logic).
- **`web/app/layout.tsx`**: Main frontend layout and theme provider.
- **`web/src/components/Sections/`**: Core UI sections like `AudioPlayer.tsx` and `AudioValidate.tsx`.
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
- **Design System**:
  - **Framework**: Material UI (v7) + Tailwind CSS.
  - **Directive**: Use MUI components for complex interactive elements and Tailwind CSS for layout and spacing.
- **Styling Strategy**:
  - **Colors**: NEVER hardcode hex values. Use the centralized theme.
    - **MUI**: Access via `useTheme()` hook (e.g., `theme.palette.primary.main`).
    - **Tailwind**: Use utility classes (e.g., `text-primary`, `bg-background`, `border-border`).
  - **Custom Styling**: Use `styled-components` when necessary, but prefer Tailwind utilities for standard spacing/sizing.
- **Global Theme**:
  - **Source of Truth**: `web/src/theme.ts` (MUI) and `web/app/globals.css` (Tailwind variables).
  - **Palette**:
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
