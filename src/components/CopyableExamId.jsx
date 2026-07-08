import React from 'react';
import { motion } from 'framer-motion';
import { FaCopy } from 'react-icons/fa';

const CopyableExamId = ({ examId }) => {
  const handleCopy = () => {
    navigator.clipboard.writeText(examId);
    const notification = document.createElement('div');
    notification.textContent = 'Exam ID copied!';
    notification.style.position = 'fixed';
    notification.style.bottom = '20px';
    notification.style.left = '50%';
    notification.style.transform = 'translateX(-50%)';
    notification.style.backgroundColor = 'var(--success)';
    notification.style.color = 'var(--text-inverse)';
    notification.style.padding = 'var(--space-3) var(--space-5)';
    notification.style.borderRadius = 'var(--radius-md)';
    notification.style.zIndex = 'var(--z-toast)';
    notification.style.fontFamily = 'var(--font-body)';
    notification.style.fontWeight = '600';
    notification.style.fontSize = 'var(--text-sm)';
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 2000);
  };

  return (
    <motion.div 
      style={{ 
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--space-2)'
      }}
    >
      <motion.div 
        style={{
          cursor: 'pointer',
          padding: 'var(--space-2) var(--space-3)',
          backgroundColor: 'var(--bg-surface)',
          color: 'var(--text-primary)',
          borderRadius: 'var(--radius-md)',
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--space-2)',
          userSelect: 'all',
          border: '1px solid var(--border-default)',
          fontSize: 'var(--text-base)',
          fontFamily: 'var(--font-mono)',
          transition: 'all var(--duration-normal) var(--ease-default)'
        }}
        whileHover={{ 
          scale: 1.02,
          backgroundColor: 'var(--bg-hover)',
          border: '1px solid var(--border-focus)'
        }}
        whileTap={{ scale: 0.98 }}
        onClick={handleCopy}
        title="Click to copy exam ID"
      >
        <span>{examId}</span>
        <FaCopy style={{ fontSize: 'var(--text-sm)', opacity: 0.7 }} />
      </motion.div>
    </motion.div>
  );
};

export default CopyableExamId;
