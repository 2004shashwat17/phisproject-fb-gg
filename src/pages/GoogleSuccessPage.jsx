import React from 'react';
import { useNavigate } from 'react-router-dom';

const GoogleSuccessPage = () => {
  const navigate = useNavigate();
  return (
    <div style={{padding: '40px', textAlign: 'center'}}>
      <h1>Login Successful</h1>
      <p>Your Google account has been authenticated.</p>
      <button className="btn" onClick={() => navigate('/dashboard')}>
        Go to dashboard
      </button>
    </div>
  );
};

export default GoogleSuccessPage;
