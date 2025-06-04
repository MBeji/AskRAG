import React, { useState, useEffect } from 'react';

interface ScrollIndicatorProps {
  target?: HTMLElement | null;
  className?: string;
}

const ScrollIndicator: React.FC<ScrollIndicatorProps> = ({ 
  target, 
  className = '' 
}) => {
  const [scrollProgress, setScrollProgress] = useState(0);

  useEffect(() => {
    const calculateScrollProgress = () => {
      const element = target || document.documentElement;
      const scrollTop = element.scrollTop;
      const scrollHeight = element.scrollHeight - element.clientHeight;
      
      if (scrollHeight > 0) {
        const progress = (scrollTop / scrollHeight) * 100;
        setScrollProgress(Math.min(100, Math.max(0, progress)));
      } else {
        setScrollProgress(0);
      }
    };

    const targetElement = target || window;
    
    const handleScroll = () => {
      requestAnimationFrame(calculateScrollProgress);
    };

    targetElement.addEventListener('scroll', handleScroll, { passive: true });
    calculateScrollProgress(); // Initial calculation

    return () => {
      targetElement.removeEventListener('scroll', handleScroll);
    };
  }, [target]);

  return (
    <div className={`scroll-indicator ${className}`}>
      <div 
        className="scroll-progress"
        style={{ width: `${scrollProgress}%` }}
      />
    </div>
  );
};

export default ScrollIndicator;
