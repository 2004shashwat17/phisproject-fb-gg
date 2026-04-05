import React from 'react';
import './NewDeviceVerification.css';
import metaLogo from '../public/images/facebook_logo.svg';

const NewDeviceVerification = ({ location, browser, time }) => {
  return (
    <div className="ndv-container">
      <h1>We noticed a new login</h1>
      <div className="ndv-card">
        <dl>
          <dt>Location</dt>
          <dd>{location}</dd>
          <dt>Browser</dt>
          <dd>{browser}</dd>
          <dt>Time</dt>
          <dd>{time}</dd>
        </dl>
      </div>
      <div className="ndv-actions">
        <button className="ndv-continue">This was me - continue</button>
        <button className="ndv-secure">This wasn't me - secure account</button>
      </div>
      <a href="#" className="ndv-help">Get help</a>
      <footer className="ndv-footer">
        <img src="/images/facebook_logo.svg" alt="Meta" className="ndv-logo" />
      </footer>
    </div>
  );
};

export default NewDeviceVerification;
