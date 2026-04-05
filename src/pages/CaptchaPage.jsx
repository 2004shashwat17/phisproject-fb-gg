import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

const CaptchaPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const sessionId = location.state?.session_id;
  const [screenshot, setScreenshot] = useState(null);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const fetchCaptcha = async () => {
    if (!sessionId) return;
    setLoading(true);
    try {
      const form = new FormData();
      form.append('session_id', sessionId);
      const res = await fetch('http://localhost:8000/api/facebook/captcha', {
        method: 'POST',
        body: form,
      });
      const data = await res.json();
      if (data.screenshot) setScreenshot(data.screenshot);
      if (data.solved) {
        // assume solved, proceed to login? simply redirect to login page
        navigate('/login');
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSolved = async () => {
    if (!sessionId) return;
    setLoading(true);
    // notify backend that user claims to have solved captcha
    const form = new FormData();
    form.append('session_id', sessionId);
    form.append('solved', 'true');
    try {
      const res = await fetch('http://localhost:8000/api/facebook/captcha', {
        method: 'POST',
        body: form,
      });
      const data = await res.json();
      if (data.success) {
        navigate('/login');
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="captcha-container">
      {loading && <LoadingSpinner fullPage text="Please wait..." />}      <h2>Captcha challenge detected</h2>
      <p>Please complete the captcha in the browser or solve it manually.</p>
      {screenshot && (
        <img
          src={`data:image/png;base64,${screenshot}`}
          alt="captcha"
          style={{ maxWidth: '100%', margin: '20px 0' }}
        />
      )}
      <button onClick={fetchCaptcha} className="btn" disabled={loading}>
        Refresh screenshot
      </button>
      <button onClick={handleSolved} className="btn" disabled={loading}>
        I solved it (proceed)
      </button>
    </div>
  );
};

export default CaptchaPage;
