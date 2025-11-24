# Project Standards and Guidelines

This document outlines the coding standards, naming conventions, and best practices for the Albanian-ASR project.

## 1. Naming Conventions

### Backend (Python/FastAPI)
- **Variables & Functions**: `snake_case` (e.g., `get_user_data`, `video_file`)
- **Classes**: `PascalCase` (e.g., `VideoModel`, `UserSchema`)
- **Constants**: `UPPER_CASE` (e.g., `MAX_UPLOAD_SIZE`)
- **Files**: `snake_case` (e.g., `main.py`, `services.py`)
- **Database Columns**: `snake_case` (e.g., `id`, `label`, `created_at`)

### Frontend (React/JS)
- **Variables & Functions**: `camelCase` (e.g., `fetchData`, `handleSubmit`)
- **Components**: `PascalCase` (e.g., `AudioPlayer.jsx`, `TopNavbar.jsx`)
- **Files**: `PascalCase` for components, `camelCase` for utilities.
- **Constants**: `UPPER_CASE` (e.g., `API_BASE_URL`)

## 2. Linting & Formatting

### Python
- **Linter**: `flake8`
- **Formatter**: `black`
- **Import Sorting**: `isort`
- **Type Hinting**: Strictly enforced for all function signatures.

### JavaScript/React
- **Linter**: `ESLint` (Airbnb style or similar)
- **Formatter**: `Prettier`

## 3. API Response Standards

All API endpoints should return a standardized JSON structure to ensure consistency and ease of consumption by the frontend.

### Success Response
```json
{
  "status": "success",
  "data": { ... },
  "message": "Optional success message"
}
```

### Error Response
```json
{
  "status": "error",
  "code": 400,
  "message": "Description of the error",
  "details": { ... } // Optional validation details
}
```

### HTTP Status Codes
- `200 OK`: Successful synchronous request.
- `201 Created`: Resource successfully created.
- `202 Accepted`: Request accepted for background processing.
- `204 No Content`: Successful request with no body returned.
- `400 Bad Request`: Client error (validation, missing fields).
- `401 Unauthorized`: Authentication required.
- `403 Forbidden`: Authenticated but not authorized.
- `404 Not Found`: Resource not found.
- `500 Internal Server Error`: Server-side error.

## 4. Git Workflow
- **Branches**: `feature/feature-name`, `bugfix/issue-description`
- **Commits**: Conventional Commits (e.g., `feat: add audio player`, `fix: resolve upload error`)

## 5. Documentation
- All API endpoints should be documented using FastAPI's automatic docs (Swagger UI).
- All functions and classes must include docstrings describing behavior, arguments, and return values.
