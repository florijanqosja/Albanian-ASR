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
- All API endpoints are rendered through the branded explorer defined in `api/docs.py`. Update that module when refreshing hero copy, tag descriptions, contact info, or server listings.
- Every routed function must include `tags`, `summary`, and `description` arguments so it displays correctly in Swagger/Redoc. Reuse the existing tag buckets; if a new capability emerges, extend `TAGS_METADATA` in `api/docs.py` with concise, commercial-grade copy.
- All functions and classes must include docstrings describing behavior, arguments, and return values.

## 6. UI & Design Patterns (Frontend)

### Frameworks & Libraries
- **Core**: Next.js 15 (App Router), React 18+.
- **UI Components**: Material UI (MUI) v7.
- **Styling**: Tailwind CSS (utility classes) + MUI `sx` prop (theme-aware styles).
- **Icons**: `lucide-react` (Standard). Avoid `react-icons` unless necessary for specific brand logos (e.g., Google).

### Component Implementation
- **MUI Grid (v7)**: Use the `size` prop instead of `item/xs/md`.
  - *Correct*: `<Grid size={{ xs: 12, md: 6 }}>`
  - *Incorrect*: `<Grid item xs={12} md={6}>`
- **Layouts**: Use `Box`, `Container`, and `Stack` for structural layout.
- **Cards/Surfaces**: Use `Paper` with `elevation={0}`, custom borders, and soft shadows for a modern, clean look.
  - *Example*: `sx={{ borderRadius: 4, border: '1px solid', borderColor: 'divider', boxShadow: '0 20px 40px -10px rgba(0,0,0,0.05)' }}`

### Styling Guidelines
- **Colors**: Use theme tokens (`primary.main`, `text.secondary`, `grey.50`) via `sx` prop or `useTheme()`. Avoid hardcoded hex values.
- **Typography**: Use MUI `Typography` component. Font family is `Khula`. Use `fontWeight` (e.g., 600, 800) to establish hierarchy.
- **Spacing**: Use MUI spacing units in `sx` (e.g., `p: 4` = 32px) or Tailwind classes (e.g., `p-8`).

### Modernization Checklist
- [ ] Replace `<img>` with `next/image`.
- [ ] Replace `<a>` with `next/link`.
- [ ] Ensure all inputs have proper labels and icons (`InputAdornment`).
- [ ] Use "Glassmorphism" or flat design with subtle borders instead of heavy material shadows.

## 7. Quality Expectations
- **No quick fixes**: Every bug fix or feature must trace the full flow (frontend, backend, data layers) before changing code. Partial patches that only treat symptoms are not allowed.
- **End-to-end validation**: Confirm how a change affects each stage of the splice pipeline (creation → labeling → validation → high quality) and document any assumptions.
- **Path & asset handling**: Never expose raw filesystem paths to clients; convert to the correct static mount (`/splices`, `/mp3`, `/mp4`) before returning data.
- **Shared logic first**: Reuse or extend common utilities (e.g., `useSpliceQueue`, service helpers) rather than duplicating request/response handling across components.
- **Fail gracefully**: When the API reports "no data", UI components must surface a clear empty state instead of leaving stale content onscreen.
