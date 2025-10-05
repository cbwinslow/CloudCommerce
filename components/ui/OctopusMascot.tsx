import React, { useEffect, useRef, useState } from 'react';
import { motion, useAnimation, AnimatePresence } from 'framer-motion';
import { useTheme } from 'next-themes';

const OctopusMascot = () => {
  const [isHovered, setIsHovered] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const controls = useAnimation();
  const theme = useTheme();
  const isDark = theme.theme === 'dark';

  // Randomly show the octopus with different animations
  useEffect(() => {
    const interval = setInterval(() => {
      const shouldShow = Math.random() > 0.7; // 30% chance to show
      if (shouldShow) {
        setIsVisible(true);
        controls.start({
          y: [0, -20, 0],
          rotate: [0, 5, -5, 0],
          transition: { duration: 2, ease: "easeInOut" }
        });
        
        const timeout = setTimeout(() => {
          setIsVisible(false);
        }, 3000);
        
        return () => clearTimeout(timeout);
      }
    }, 10000); // Check every 10 seconds
    
    return () => clearInterval(interval);
  }, [controls]);

  const tentacleVariants = {
    initial: { pathLength: 0, opacity: 0 },
    animate: (i: number) => ({
      pathLength: 1,
      opacity: 1,
      transition: {
        pathLength: { delay: i * 0.1, type: "spring", duration: 1.5, bounce: 0 },
        opacity: { delay: i * 0.1, duration: 0.01 }
      }
    })
  };

  return (
    <motion.div
      className="relative w-24 h-24 cursor-pointer"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      animate={controls}
      initial={false}
    >
      <AnimatePresence>
        {isVisible && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ 
              opacity: 1, 
              y: 0,
              transition: { duration: 0.5 }
            }}
            exit={{ 
              opacity: 0, 
              y: 20,
              transition: { duration: 0.3 }
            }}
            className="absolute -top-20 -left-16 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-xl p-3 border border-purple-200 dark:border-purple-900"
          >
            <div className="text-xs text-purple-800 dark:text-purple-200">
              Need help? I'm your friendly octopus guide! 🐙
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      <svg 
        width="100%" 
        height="100%" 
        viewBox="0 0 200 200" 
        fill="none" 
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Body */}
        <motion.circle 
          cx="100" 
          cy="100" 
          r="40" 
          fill={isDark ? "#8b3dff" : "#7c3aed"}
          initial={{ scale: 0.9 }}
          animate={{ 
            scale: isHovered ? 1.05 : 0.95,
            transition: { 
              duration: 0.5,
              type: "spring",
              stiffness: 300,
              damping: 10
            }
          }}
        />
        
        {/* Eyes */}
        <motion.circle 
          cx="85" 
          cy="90" 
          r="8" 
          fill="white"
          initial={{ scale: 1 }}
          animate={{ 
            scale: isHovered ? 1.1 : 1,
            x: isHovered ? -2 : 0
          }}
        />
        <motion.circle 
          cx="115" 
          cy="90" 
          r="8" 
          fill="white"
          initial={{ scale: 1 }}
          animate={{ 
            scale: isHovered ? 1.1 : 1,
            x: isHovered ? 2 : 0
          }}
        />
        <motion.circle 
          cx={isHovered ? 82 : 85} 
          cy="90" 
          r="3" 
          fill="#ffd700"
          animate={{
            x: isHovered ? -3 : 0,
            transition: { 
              duration: 0.3,
              type: "spring",
              stiffness: 500,
              damping: 15
            }
          }}
        />
        <motion.circle 
          cx={isHovered ? 112 : 115} 
          cy="90" 
          r="3" 
          fill="#ffd700"
          animate={{
            x: isHovered ? -3 : 0,
            transition: { 
              duration: 0.3,
              type: "spring",
              stiffness: 500,
              damping: 15
            }
          }}
        />
        
        {/* Smile */}
        <motion.path 
          d="M85 120 Q100 130 115 120" 
          stroke={isDark ? "#ffffff" : "#4a044e"} 
          strokeWidth="3" 
          fill="none"
          strokeLinecap="round"
          initial={{ pathLength: 0 }}
          animate={{ 
            pathLength: 1,
            d: isHovered ? "M85 115 Q100 135 115 115" : "M85 120 Q100 130 115 120"
          }}
          transition={{ duration: 0.3 }}
        />
        
        {/* Tentacles */}
        {Array.from({ length: 8 }).map((_, i) => {
          const angle = (i / 8) * Math.PI * 2;
          const x = 100 + Math.cos(angle) * 40;
          const y = 100 + Math.sin(angle) * 40;
          const controlX1 = x + Math.cos(angle + 0.5) * 20;
          const controlY1 = y + Math.sin(angle + 0.5) * 20;
          const controlX2 = x + Math.cos(angle - 0.5) * 30;
          const controlY2 = y + Math.sin(angle - 0.5) * 30;
          
          return (
            <motion.path
              key={i}
              d={`M${x},${y} C${controlX1},${controlY1} ${controlX2},${controlY2} ${x},${y + 30}`}
              stroke={isDark ? "#b98bf2" : "#8b3dff"}
              strokeWidth="10"
              fill="none"
              strokeLinecap="round"
              initial="initial"
              animate={isHovered ? "animate" : "initial"}
              variants={tentacleVariants}
              custom={i}
            />
          );
        })}
      </svg>
    </motion.div>
  );
};

export default OctopusMascot;
