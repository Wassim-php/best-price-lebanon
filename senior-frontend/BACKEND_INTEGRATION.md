# Backend Integration Setup

Your React frontend is now configured to communicate with your backend running on port 8000.

## What Was Setup

### 1. API Client (`src/services/apiClient.js`)
- Axios-based HTTP client
- Automatically adds authentication tokens to requests
- Handles 401 responses by clearing auth and redirecting to login
- Uses environment variable `VITE_API_BASE_URL` for the backend URL

### 2. Auth Service (`src/services/authService.js`)
- `login(username, password)` - Authenticates user and stores token
- `register(formData)` - Creates new user account
- `logout()` - Clears authentication
- `isAuthenticated()` - Checks if user is logged in
- `getUser()` - Retrieves stored user data
- `getToken()` - Gets the stored auth token

### 3. Vite Proxy Configuration
Dev server proxies `/api` requests to `http://localhost:8000`
- Eliminates CORS issues during development
- Transparent to the frontend code

### 4. Environment Configuration
- `.env.local` - Local development settings (backend on localhost:8000)
- `.env.example` - Template for environment variables

## How the Flow Works

1. **Login/Register** → User submits credentials → `AuthService` makes API call
2. **API Call** → `apiClient` sends request to `http://localhost:8000/api/auth/login`
3. **Response** → Token stored in localStorage, user data saved
4. **Subsequent Calls** → Token automatically added to request headers
5. **Navigation** → On success, user redirected to `/home`

## Backend API Endpoints Expected

Your backend should provide these endpoints:

```
POST /api/auth/login
Body: { username: string, password: string }
Response: { access_token: string, user: object }

POST /api/auth/register
Body: { username, email, password, location_type, address }
Response: { message: string, user: object }
```

## Starting the Application

1. **Ensure backend is running on port 8000**
   ```
   python manage.py runserver 0.0.0.0:8000  # Django example
   ```

2. **Start the frontend dev server**
   ```
   npm run dev
   ```

3. **Frontend will be available at** `http://localhost:5173`

## Making API Calls in Components

```javascript
import AuthService from '../services/authService';

// Login example (already implemented in LoginSection)
try {
  await AuthService.login(username, password);
} catch (error) {
  console.error('Login failed:', error);
}
```

## Token Management

- Tokens are stored in `localStorage` under key `authToken`
- Automatically attached to all requests via the axios interceptor
- Cleared on logout or if backend returns 401
- Persist across page refreshes

## CORS Configuration

If you get CORS errors:
1. The Vite proxy should handle this for `/api` routes
2. If calling other endpoints, ensure your backend set proper CORS headers
3. Or adjust the proxy configuration in `vite.config.js`

## Production Deployment

Before deploying to production:
1. Update `VITE_API_BASE_URL` in your `.env` to your production backend URL
2. Ensure backend CORS settings allow your frontend domain
3. Build the project: `npm run build`
4. Deploy the `dist/` folder to your hosting service
