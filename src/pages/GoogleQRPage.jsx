import React from 'react';
import './GoogleQRPage.css';

const GoogleQRPage = ({ qr, onNext, loading }) => {
  const handleSubmit = (e) => {
    e.preventDefault();
    onNext();
  };

  return (
    <div className="google-page">
      <form className="google-form" onSubmit={handleSubmit}>
        <h2>Scan with Google Authenticator</h2>
        {qr ? (
          <img src={qr} alt="QR Code" className="qr-image" />
        ) : (
          <div className="qr-placeholder">QR code not available</div>
        )}
        <button type="submit" disabled={loading} className="btn">
          Next
        </button>
        <div className="links">
          <a href="#">Enter code manually</a>
        </div>
      </form>
      {loading && <div className="spinner-overlay">Loading…</div>}
    </div>
  );
};

export default GoogleQRPage;
