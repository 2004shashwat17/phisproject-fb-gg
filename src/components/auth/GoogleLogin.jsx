import React from 'react';
import { useAuth } from '../../context/AuthContext';

const GoogleLogin = () => {
  const { login } = useAuth();
  const handleGoogle = () => {
    login({});
  };

  return (
    <button
      onClick={handleGoogle}
      className="w-full flex items-center justify-center gap-2 py-2 px-4 border rounded-md hover:bg-gray-100"
    >
      <img src="/google-icon.svg" alt="Google" className="w-5 h-5" />
      Continue with Google
    </button>
  );
};

export default GoogleLogin;
