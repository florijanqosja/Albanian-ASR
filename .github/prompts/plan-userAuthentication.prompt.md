## Plan: User Authentication & Profile Management

We will implement a full user account system with Google/Standard login, profile management, and activity tracking ("My Labels").

### Steps

1.  **Backend: Database Schema Updates**
    *   Create `User` model in `api/database/models.py` with fields: `id` (UUID), `name`, `surname`, `email`, `phone_number`, `age`, `nationality`, `created_at`, `modified_at`, `accent`, `region`.
    *   Add `user_id` column (ForeignKey to `User`) to `Splice`, `LabeledSplice`, `HighQualityLabeledSplice`, `DeletedSplice`, and `SpliceBeingProcessed` tables.
    *   Create a startup script in `api/main.py` to seed "System" and "Anonymous" users if missing.

2.  **Backend: Authentication Service**
    *   Install `python-jose`, `passlib`, `google-auth` in `api/requirements.txt`.
    *   Create `api/routers/auth.py` with endpoints:
        *   `POST /auth/register`: Create new user.
        *   `POST /auth/login`: Standard email/password login (returns JWT).
        *   `POST /auth/google`: Verify Google token and return JWT.
    *   Create `api/routers/users.py` for `/users/profile` (GET/PUT) and `/users/stats` (GET).

3.  **Frontend: Auth Context & Login Page**
    *   Create `web/src/context/AuthContext.tsx` to manage session state (user, token, login/logout).
    *   Create `web/app/login/page.tsx` using MUI Treasury components, supporting Google Sign-In and standard form.
    *   Update `web/src/components/Nav/TopNavbar.tsx` to show Avatar/Dropdown when logged in.

4.  **Frontend: Profile & My Labels Pages**
    *   Create `web/app/profile/page.tsx` for editing user info and password.
    *   Create `web/app/my-labels/page.tsx` with:
        *   **Stats Cards**: Labeled count, Validated count, Hours labeled/validated.
        *   **Table**: List of 10 most recent actions (Index, Audio Player, Label).

5.  **Integration: Labeling & Validation Logic**
    *   Update `api/main.py` endpoints (`label_splice`, `validate_splice`) to require `user_id`.
    *   Update `web/src/components/Sections/AudioValidate.tsx`:
        *   If logged out: Show "Register/Skip" modal on submit.
        *   If "Skip": Use "Anonymous" user UUID.
        *   If logged in: Send JWT token in headers.

### Further Considerations
1.  **Migration Strategy**: Since there is no Alembic, we will need to drop and recreate tables locally or manually add columns. Is it acceptable to reset the local database for this feature?
2.  **Google Client ID**: You will need to provide a Google Client ID in `.env` for the frontend to initialize the Google Sign-In button.
3.  **Anonymous Tracking**: We will use a single "Anonymous" user record for all skipped actions to satisfy the non-nullable database constraint.
