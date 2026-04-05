import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * Simple countdown timer hook
 * @param {number} initialSeconds - starting number of seconds (must be >= 0)
 * @param {() => void} onComplete - optional callback when timer reaches zero
 *
 * Returns object with:
 *   seconds, formatted, isActive, isComplete, start, pause, reset
 */
const pad = (n) => n.toString().padStart(2, '0');

export default function useCountdown(initialSeconds, onComplete) {
  const [seconds, setSeconds] = useState(() => Math.max(0, initialSeconds));
  const [isActive, setIsActive] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const intervalRef = useRef(null);
  const targetRef = useRef(seconds);

  const tick = useCallback(() => {
    setSeconds((s) => {
      if (s <= 1) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
        setIsActive(false);
        setIsComplete(true);
        if (onComplete) onComplete();
        return 0;
      }
      return s - 1;
    });
  }, [onComplete]);

  const start = useCallback(() => {
    setIsComplete(false);
    setSeconds((prev) => {
      const val = Math.max(0, initialSeconds);
      targetRef.current = val;
      return val;
    });
    if (intervalRef.current) clearInterval(intervalRef.current);
    setIsActive(true);
    intervalRef.current = setInterval(tick, 1000);
  }, [initialSeconds, tick]);

  const pause = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsActive(false);
  }, []);

  const reset = useCallback(() => {
    pause();
    setSeconds(Math.max(0, initialSeconds));
    setIsComplete(false);
  }, [initialSeconds, pause]);

  // ensure timer updates when initialSeconds changes
  useEffect(() => {
    setSeconds((s) => (s > initialSeconds ? initialSeconds : s));
    targetRef.current = initialSeconds;
  }, [initialSeconds]);

  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  const formatted = `${pad(Math.floor(seconds / 60))}:${pad(seconds % 60)}`;

  return { seconds, formatted, isActive, isComplete, start, pause, reset };
}
