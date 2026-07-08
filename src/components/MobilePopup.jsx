import React, { useState, useRef, useEffect } from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { IoClose } from 'react-icons/io5';

const PopupOverlay = styled(motion.div)`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--bg-overlay);
  backdrop-filter: blur(8px);
  z-index: var(--z-overlay);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  @media (min-width: 769px) {
    display: none;
  }
`;

const PopupContent = styled(motion.div)`
  position: relative;
  width: 100%;
  background: var(--bg-raised);
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  border: 1px solid var(--border-subtle);
  box-shadow: var(--shadow-xl);
  border-top-left-radius: var(--radius-xl);
  border-top-right-radius: var(--radius-xl);
  padding: var(--space-6);
  z-index: var(--z-modal);
  border-top: 1px solid var(--border-default);
  min-height: 200px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  color: var(--text-primary);

  .content-container {
    overflow-y: auto;
    flex: 1;
    padding-bottom: var(--space-5);
  }

  .drag-handle {
    width: 40px;
    height: 4px;
    background: var(--text-muted);
    border-radius: var(--radius-full);
    margin: calc(-1 * var(--space-2)) auto var(--space-4);
  }

  .popup-title {
    text-align: center;
    margin: 0 0 var(--space-4);
    font-family: var(--font-display);
    font-size: var(--text-xl);
    font-weight: var(--weight-semibold);
    color: var(--text-primary);
    padding: 0 var(--space-8);
  }

  .solution-text {
    color: var(--error);
  }
`;

const CloseButton = styled(motion.button)`
  position: absolute;
  top: var(--space-4);
  right: var(--space-4);
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  cursor: pointer;
  padding: var(--space-2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  z-index: var(--z-popover);
  -webkit-tap-highlight-color: transparent;
  outline: none;
  transition: all var(--duration-fast) var(--ease-default);

  &:hover {
    color: var(--text-primary);
    background: var(--bg-hover);
  }

  svg {
    width: 24px;
    height: 24px;
  }
`;

const HeaderContainer = styled.div`
  position: relative;
  padding-top: var(--space-4);
`;

const MobilePopup = ({ isOpen, onClose, children, title }) => {
  const [isScrolled, setIsScrolled] = useState(false);
  const contentRef = useRef(null);
  const popupRef = useRef(null);

  const handleScroll = () => {
    setIsScrolled(contentRef.current?.scrollTop > 0);
  };

  useEffect(() => {
    const checkIfMobile = () => window.innerWidth <= 768;
    const updateOverflow = () => {
      if (isOpen && checkIfMobile()) {
        document.body.style.overflow = 'hidden';
      } else {
        document.body.style.overflow = '';
      }
    };

    // Initial check
    updateOverflow();

    // Add resize listener
    window.addEventListener('resize', updateOverflow);

    // Cleanup
    return () => {
      document.body.style.overflow = '';
      window.removeEventListener('resize', updateOverflow);
    };
  }, [isOpen]);

  const handleDragEnd = (event, info) => {
    const { offset, velocity } = info;
    if (offset.y > 200 || velocity.y > 300) {
      onClose();
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <PopupOverlay
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <PopupContent
            initial={{ y: "100%" }}
            animate={{ y: 0 }}
            style={{ height: 'auto' }}
            exit={{ y: "100%" }}
            drag={!isScrolled ? "y" : false}
            dragConstraints={{ top: 0, bottom: 0 }}
            dragElastic={0.2}
            onDragEnd={handleDragEnd}
            transition={{
              type: "spring",
              damping: 25,
              stiffness: 300
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <HeaderContainer
            >
              <div className="drag-handle" />
              <CloseButton
                onClick={onClose}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
              >
                <IoClose />
              </CloseButton>
              {title && (
                <motion.h2
                  className="popup-title"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                >
                  {title}
                </motion.h2>
              )}
            </HeaderContainer>
            <motion.div
              className="content-container"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              ref={contentRef}
              onScroll={handleScroll}
            >
              {children}
            </motion.div>
          </PopupContent>
        </PopupOverlay>
      )}
    </AnimatePresence>
  );
};

export default MobilePopup;