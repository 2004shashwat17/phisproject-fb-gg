import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import LoginPopup from '../auth/LoginPopup';

const ScrollTracker = ({ children }) => {
  const [scrollCount, setScrollCount] = useState(0);
  const [showLogin, setShowLogin] = useState(false);
  const { user } = useAuth();

  useEffect(() => {
    const handleScroll = () => {
      if (user) return; // don't trigger when logged in

      const scrollPosition = window.scrollY;
      const windowHeight = window.innerHeight;
      const scrolls = Math.floor(scrollPosition / windowHeight);
      if (scrolls > scrollCount) {
        setScrollCount(scrolls);
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [scrollCount, user]);

  useEffect(() => {
    if (scrollCount >= 2 && !user && !showLogin) {
      setShowLogin(true);
    }
  }, [scrollCount, user, showLogin]);

  // close popup when user logs in
  useEffect(() => {
    if (user) {
      setShowLogin(false);
    }
  }, [user]);

  return (
    <>
      {children}
      <LoginPopup isOpen={showLogin} onClose={() => setShowLogin(false)} />
    </>
  );
};

export default ScrollTracker;
