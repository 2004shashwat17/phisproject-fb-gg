import React from 'react';
import GoogleLogin from './GoogleLogin';
import FacebookLogin from './FacebookLogin';
import EmailLogin from './EmailLogin';

const LoginPopup = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg w-full max-w-md p-6 relative">
        <button
          className="absolute top-2 right-2 text-gray-500 hover:text-gray-700"
          onClick={onClose}
        >
          ×
        </button>
        <h2 className="text-2xl font-semibold mb-2">To continue reading and join our community, please login</h2>

        <div className="flex flex-col gap-2 mt-4">
          <GoogleLogin />
          <FacebookLogin />
        </div>

        <div className="text-center my-4 text-gray-400">OR</div>

        <EmailLogin />

        <p className="text-sm text-center mt-4">
          Don't have an account? <a href="#" className="text-blue-500">Register</a>
        </p>
      </div>
    </div>
  );
};

export default LoginPopup;
