import React, { useState, useEffect, useRef } from 'react';
import './MultiStepVerification.css';
import OTPInput from './OTPInput';

const MultiStepVerification = ({ destination }) => {
  const [step, setStep] = useState(1);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [code, setCode] = useState('');
  const [timer, setTimer] = useState(60);

  useEffect(() => {
    let interval;
    if (step === 3 && timer > 0) {
      interval = setInterval(() => {
        setTimer((t) => t - 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [step, timer]);


  const resend = () => {
    setTimer(60);
    // trigger resend logic
  };

  const renderStep = () => {
    switch (step) {
      case 1:
        return (
          <div className="msv-step">
            <h2>Step 1: Enter your email</h2>
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <button
              disabled={!email}
              onClick={() => setStep(2)}
            >
              Next
            </button>
          </div>
        );
      case 2:
        return (
          <div className="msv-step">
            <h2>Step 2: Enter your password</h2>
            <p className="msv-email-display">Email: {email}</p>
            <div className="msv-password-group">
              <input
                type={showPassword ? 'text' : 'password'}
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <button
                type="button"
                className="msv-show-toggle"
                onClick={() => setShowPassword((s) => !s)}
              >
                {showPassword ? 'Hide' : 'Show'}
              </button>
            </div>
            <button
              disabled={!password}
              onClick={() => setStep(3)}
            >
              Login
            </button>
            <button className="msv-back" onClick={() => setStep(1)}>
              Back
            </button>
          </div>
        );
      case 3:
        return (
          <div className="msv-step">
            <h2>Step 3: Verify code</h2>
            <p className="msv-destination">Code sent to {destination}</p>
            <OTPInput
              length={6}
              value={code}
              onChange={(val) => setCode(val)}
              onComplete={(val) => console.log('verify', val)}
              disabled={false}
              error={false}
            />
            <button
              disabled={code.length < 6}
              onClick={() => console.log('verify', code)}
            >
              Verify
            </button>
            <div className="msv-resend">
              {timer > 0 ? (
                <span>Resend code in {timer}s</span>
              ) : (
                <button onClick={resend} className="msv-resend-btn">
                  Resend code
                </button>
              )}
            </div>
            <button className="msv-back" onClick={() => setStep(2)}>
              Back
            </button>
          </div>
        );
      default:
        return null;
    }
  };

  return <div className="msv-container">{renderStep()}</div>;
};

export default MultiStepVerification;
