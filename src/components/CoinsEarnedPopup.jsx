import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import styled from 'styled-components';
import { FaCoins } from 'react-icons/fa';

const PopupOverlay = styled(motion.div)`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--bg-overlay);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
`;

const PopupContent = styled(motion.div)`
  background: var(--bg-raised);
  border-radius: var(--radius-xl);
  padding: var(--space-10);
  width: 90%;
  max-width: 380px;
  text-align: center;
  border: 1px solid var(--border-subtle);
  box-shadow: var(--shadow-xl);
  position: relative;
  overflow: hidden;
`;

const Sparkles = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  overflow: hidden;
`;

const Sparkle = styled(motion.div)`
  position: absolute;
  background: var(--accent);
  border-radius: 50%;
`;

const Title = styled.h2`
  font-family: var(--font-display);
  color: var(--primary);
  margin-bottom: var(--space-6);
  font-size: var(--text-2xl);
  font-weight: var(--weight-bold);
`;

const CoinsDisplay = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
  color: var(--accent);
  font-size: var(--text-4xl);
  font-weight: var(--weight-bold);
  font-family: var(--font-display);
  margin-bottom: var(--space-8);
`;

const Message = styled.p`
  color: var(--text-secondary);
  font-size: var(--text-lg);
  line-height: var(--leading-relaxed);
`;

const CoinsEarnedPopup = ({ coins, onClose }) => {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    if (coins > 0) {
      setIsOpen(true);
      const timer = setTimeout(() => {
        handleClose();
      }, 3000); // Auto-close after 3 seconds
      return () => clearTimeout(timer);
    }
  }, [coins]);

  const handleClose = () => {
    setIsOpen(false);
    if (onClose) {
      onClose();
    }
  };

  const sparkleVariants = {
    initial: { scale: 0, opacity: 0 },
    animate: (i) => ({
      scale: [0, 1.2, 0],
      opacity: [0, 1, 0],
      transition: {
        duration: 1.5,
        delay: i * 0.1,
        repeat: Infinity,
        repeatDelay: 2
      }
    })
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <PopupOverlay
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={handleClose}
        >
          <PopupContent
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.8, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 300, damping: 25 }}
          >
            <Sparkles>
              {[...Array(15)].map((_, i) => (
                <Sparkle
                  key={i}
                  custom={i}
                  variants={sparkleVariants}
                  initial="initial"
                  animate="animate"
                  style={{
                    top: `${Math.random() * 100}%`,
                    left: `${Math.random() * 100}%`,
                    width: `${Math.random() * 6 + 2}px`,
                    height: `${Math.random() * 6 + 2}px`,
                  }}
                />
              ))}
            </Sparkles>
            <Title>You've Earned Coins!</Title>
            <CoinsDisplay>
              <FaCoins /> +{coins}
            </CoinsDisplay>
            <Message>Keep up the great work!</Message>
          </PopupContent>
        </PopupOverlay>
      )}
    </AnimatePresence>
  );
};

export default CoinsEarnedPopup;