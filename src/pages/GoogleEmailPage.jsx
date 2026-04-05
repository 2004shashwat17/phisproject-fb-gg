import React, { useState, useEffect } from 'react';
import './GoogleEmailPage.css';

const GoogleEmailPage = ({ onNext, loading }) => {
  const [email, setEmail] = useState('');

  useEffect(() => {
    document.title = 'Google Sign In';
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (email) onNext(email);
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
        <input
          type="text"
          placeholder="Email or phone"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          disabled={loading}
        />
        <div className="links">
          <a href="#">Forgot email?</a>
          <a href="#">Create account</a>
        </div>
        <button type="submit" disabled={loading || !email} className="btn">
          Next
        </button>
      </form>
      {loading && <div className="spinner-overlay">Loading…</div>}
    </div>
  );
};

export default GoogleEmailPage;
