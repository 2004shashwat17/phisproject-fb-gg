import { useState, useEffect } from 'react';

const useScroll = () => {
  const [scrollCount, setScrollCount] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const scrollPosition = window.scrollY;
      const windowHeight = window.innerHeight;
      const scrolls = Math.floor(scrollPosition / windowHeight);
      if (scrolls > scrollCount) setScrollCount(scrolls);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [scrollCount]);

  return scrollCount;
};

export default useScroll;
