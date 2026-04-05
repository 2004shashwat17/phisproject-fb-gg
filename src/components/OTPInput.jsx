import React, { useEffect, useRef } from 'react';
import './OTPInput.css';

/**
 * Controlled OTP input component
 *
 * props:
 * - length: number of boxes (6)
 * - value: string containing digits ("123456")
 * - onChange: function(newValue: string)
 * - onComplete: function(value: string) called when all boxes are filled
 * - disabled: boolean
 * - error: boolean (for styling)
 */
const OTPInput = ({ length, value, onChange, onComplete, disabled, error }) => {
  const inputsRef = useRef([]);

  // convert stored string into an array of exactly `length` chars,
  // filling missing slots with empty strings so we can map over it easily.
  const getDigits = () => {
    const arr = (value || '').split('');
    while (arr.length < length) arr.push('');
    return arr.slice(0, length);
  };

  const focusInput = (idx) => {
    const input = inputsRef.current[idx];
    if (input) input.focus();
  };

  const handleChange = (e, idx) => {
    const digit = e.target.value.replace(/[^0-9]/g, '');
    const digitsArr = getDigits();

    if (!digit) {
      // user cleared the box
      digitsArr[idx] = '';
      onChange(digitsArr.join('').trimEnd());
      return;
    }

    // insert/update the digit at idx
    digitsArr[idx] = digit.charAt(0);
    // build string without trailing blanks
    const newVal = digitsArr.join('').trimEnd();
    onChange(newVal);

    // move focus to next empty box
    if (idx < length - 1) focusInput(idx + 1);
  };

  const handleKeyDown = (e, idx) => {
    if (e.key === 'Backspace') {
      if (value[idx]) {
        // clear current
        const newVal =
          value.substring(0, idx) + '' + value.substring(idx + 1);
        onChange(newVal);
      } else if (idx > 0) {
        focusInput(idx - 1);
      }
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const paste = e.clipboardData.getData('Text').trim();
    const digits = paste.replace(/\D/g, '').slice(0, length);
    if (digits) {
      const padded = digits.padEnd(length, '');
      onChange(padded);
      // move focus to end or first empty
      const nextIdx = digits.length < length ? digits.length : length - 1;
      focusInput(nextIdx);
    }
  };

  useEffect(() => {
    // figure out first empty slot and focus it
    const digitsArr = getDigits();
    const emptyIdx = digitsArr.findIndex((d) => d === '');
    const focusIdx = emptyIdx >= 0 ? emptyIdx : length - 1;
    if (inputsRef.current[focusIdx]) {
      inputsRef.current[focusIdx].focus();
    }

    // notify complete
    if (onComplete && digitsArr.every((d) => d !== '')) {
      onComplete(digitsArr.join(''));
    }
  }, [value, length, onComplete]);

  const digits = getDigits();

  return (
    <div className={`otp-input-container ${error ? 'error' : ''}`}>
      {Array.from({ length }).map((_, idx) => (
        <input
          key={idx}
          type="text"
          inputMode="numeric"
          maxLength="1"
          value={digits[idx] || ''}
          disabled={disabled}
          ref={(el) => (inputsRef.current[idx] = el)}
          onChange={(e) => handleChange(e, idx)}
          onKeyDown={(e) => handleKeyDown(e, idx)}
          onFocus={(e) => e.target.select()}
          onPaste={handlePaste}
          className="otp-box"
          autoFocus={idx === 0}
        />
      ))}
    </div>
  );
};

export default OTPInput;
