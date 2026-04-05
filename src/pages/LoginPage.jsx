import React from 'react';
import { useNavigate } from 'react-router-dom';
import FacebookLogin from '../components/FacebookLogin';

// simple wrapper that delegates to the styled Facebook login component
const LoginPage = () => {
  const navigate = useNavigate();
  return (
    <div>
      <FacebookLogin />
      <div style={{ textAlign: 'center', marginTop: '20px' }}>
        <button
          className="btn create-btn"
          onClick={() => navigate('/google')}
        >
          Use Google instead
        </button>
      </div>
    </div>
  );
};

export default LoginPage;
