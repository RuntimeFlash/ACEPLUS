// components/ExamSkeletonLoading.jsx
import React from 'react';
import './ExamSkeletonLoading.css';

const ExamSkeletonLoading = () => {
  return (
    <div className="exam-skeleton-container">
      {[1, 2, 3, 4].map((item) => (
        <div key={item} className="exam-skeleton-card">
          <div className="exam-skeleton-question skeleton"></div>
          <div className="exam-skeleton-options">
            <div className="exam-skeleton-option skeleton"></div>
            <div className="exam-skeleton-option skeleton"></div>
            <div className="exam-skeleton-option skeleton"></div>
            <div className="exam-skeleton-option skeleton"></div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default ExamSkeletonLoading;