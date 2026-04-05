import React from 'react';
import { useAuth } from '../../context/AuthContext';

const FacebookLogin = () => {
  const { login } = useAuth();
  const handleFB = () => {
    login({});
  };

  return (
    <button
      onClick={handleFB}
      className="w-full flex items-center justify-center gap-2 py-2 px-4 border rounded-md hover:bg-gray-100"
    >
      <img src="/facebook-icon.svg" alt="Facebook" className="w-5 h-5" />
      Continue with Facebook
    </button>
  );
};

export default FacebookLogin;
