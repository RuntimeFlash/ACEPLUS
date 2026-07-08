import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import Notification from './Notification';
import UpdatePopup from './UpdatePopup';
import LeaderboardPopup from './LeaderboardPopup';
import UnsubmittedExamPopup from './UnsubmittedExamPopup';
import { api } from '../utils/api';
import './body-content.css';

// Animation variants
const cardVariants = {
  hidden: { opacity: 0, scale: 0.9, y: 40 },
  visible: (index) => ({
    opacity: 1, 
    scale: 1, 
    y: 0,
    transition: { duration: 0.6, delay: index * 0.15, ease: "easeOut" }
  })
};

const fadeTransition = {
  hidden: { opacity: 0, scale: 0.95, filter: 'blur(10px)' },
  visible: {
    opacity: 1, scale: 1, filter: 'blur(0px)',
    transition: { duration: 0.5, ease: "easeOut" }
  },
  exit: {
    opacity: 0, scale: 1.05, filter: 'blur(10px)',
    transition: { duration: 0.3, ease: "easeIn" }
  }
};

function Content({ updateAuthState }) {
  const navigate = useNavigate();
  const [cardData, setCardData] = useState([
    { title: "Total Exams Attempted", value: "NA" },
    { title: "Total Marks Attempted", value: "NA" },
    { title: "Total Marks Gained", value: "NA" },
    { title: "Average Percentage", value: "NA" }
  ]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Popups and data state
  const [showUpdatePopup, setShowUpdatePopup] = useState(false);
  const [updates, setUpdates] = useState([]);
  const [showLeaderboardPopup, setShowLeaderboardPopup] = useState(false);
  const [leaderboardData, setLeaderboardData] = useState(null);
  const [currentLeaderboardId, setCurrentLeaderboardId] = useState(null);
  const [showUnsubmittedPopup, setShowUnsubmittedPopup] = useState(false);
  const [unsubmittedExams, setUnsubmittedExams] = useState([]);
  const [pendingAfterLeaderboard, setPendingAfterLeaderboard] = useState(false);
  const [animateNumbers, setAnimateNumbers] = useState(false);
  
  // Profile for greeting
  const [userProfile, setUserProfile] = useState(null);

  const subjects = [
    { id: 'math', name: 'Mathematics', class: 'math' },
    { id: 'science', name: 'Science', class: 'science' },
    { id: 'ss', name: 'Social Studies', class: 'ss' },
    { id: 'english', name: 'English', class: 'english' }
  ];

  useEffect(() => {
    const handleAnimateCards = () => setTimeout(() => setAnimateNumbers(true), 1500);
    window.addEventListener('animateCards', handleAnimateCards);
    return () => window.removeEventListener('animateCards', handleAnimateCards);
  }, []);

  const checkForUpdates = async () => {
    try {
      const data = await api.getUpdates();
      if (data && data.version) {
        const lastSeenUpdate = localStorage.getItem('lastSeenUpdate');
        if (!lastSeenUpdate || lastSeenUpdate !== data.version) {
          setUpdates([data]);
          setShowUpdatePopup(true);
        }
      }
    } catch (error) {
      console.error('Failed to fetch updates:', error);
    }
  };

  const fetchLeaderboard = async () => {
    try {
      const data = await api.getLeaderboard(1, 20); 
      const storedLeaderboardId = localStorage.getItem('lastSeenLeaderboardId'); 
      const newLeaderboardId = data.leaderboard_id; 
      setCurrentLeaderboardId(newLeaderboardId);

      const filteredLeaderboard = data.leaderboard
        .filter(entry => entry.name !== 'UNKNOWN')
        .map((entry, index) => ({ ...entry, rank: index + 1 })); 
      data.leaderboard = filteredLeaderboard;

      if (newLeaderboardId && newLeaderboardId !== storedLeaderboardId) {
        setLeaderboardData(data);
        setShowLeaderboardPopup(true);
      }
    } catch (error) {
      console.error('Failed to fetch leaderboard:', error);
    }
  };

  useEffect(() => {
    let isMounted = true; 
    const fetchData = async () => {
      try {
        if (!localStorage.getItem('token')) throw new Error('Unauthorized');

        const [userStatsResponse, _, __, unsubmittedResponse, profileResponse] = await Promise.all([
          api.getOverviewStats(),
          checkForUpdates(),
          fetchLeaderboard(),
          api.getUnsubmittedExams(),
          api.getMyProfile().catch(() => null)
        ]);

        if (isMounted) {
          setUnsubmittedExams(unsubmittedResponse?.unsubmitted_exams || []);
          if (profileResponse) setUserProfile(profileResponse);
        }

        if (userStatsResponse && userStatsResponse.version) {
          const clientVersion = localStorage.getItem('version');
          if (clientVersion !== userStatsResponse.version) {
            localStorage.clear();
            localStorage.setItem('version', userStatsResponse.version);
            if (updateAuthState) updateAuthState();
            navigate('/login');
            return;
          }
        }

        if (isMounted) {
          const overviewData = userStatsResponse?.stats;
          if (overviewData && Array.isArray(overviewData) && overviewData.length > 0) {
            setCardData([
              { title: "Total Exams Attempted", value: overviewData[0]?.total_exams || 0 },
              { title: "Total Marks Attempted", value: overviewData[1]?.total_marks || 0 },
              { title: "Total Marks Gained", value: overviewData[2]?.marks_gained || 0 },
              { title: "Average Percentage", value: overviewData[3]?.average_percentage || "0.00%" }
            ]);
          } else {
            setCardData([
              { title: "Total Exams Attempted", value: 0 },
              { title: "Total Marks Attempted", value: 0 },
              { title: "Total Marks Gained", value: 0 },
              { title: "Average Percentage", value: "0.00%" }
            ]);
          }
        }
      } catch (error) {
        if (isMounted) setError(error.message);
        if (error.message === 'Unauthorized access' || error.message === 'Unauthorized') {
          if (updateAuthState) updateAuthState();
          navigate('/login');
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    };
    fetchData();
    return () => { isMounted = false; };
  }, []);

  useEffect(() => {
    if (unsubmittedExams.length > 0 && !showUpdatePopup && !showLeaderboardPopup) {
      setShowUnsubmittedPopup(true);
    }
  }, [unsubmittedExams, showUpdatePopup, showLeaderboardPopup]);

  const handleCloseLeaderboard = () => {
    setShowLeaderboardPopup(false);
    window.dispatchEvent(new Event('animateCards'));
    if (currentLeaderboardId) localStorage.setItem('lastSeenLeaderboardId', currentLeaderboardId);
    if (pendingAfterLeaderboard && unsubmittedExams.length > 0) {
      setShowUnsubmittedPopup(true);
      setPendingAfterLeaderboard(false);
    }
  };

  const firstName = userProfile?.display_name?.split(' ')[0] || userProfile?.username || 'Student';

  return (
    <>
      <UpdatePopup
        isOpen={showUpdatePopup}
        onClose={() => {
          if (updates.length > 0) localStorage.setItem('lastSeenUpdate', updates[0].version);
          setShowUpdatePopup(false);
          if (leaderboardData) setShowLeaderboardPopup(true);
        }}
        updates={updates}
      />
      {leaderboardData && (
        <LeaderboardPopup
          isOpen={showLeaderboardPopup}
          onClose={handleCloseLeaderboard}
          leaderboardData={leaderboardData}
          updatePopupOpen={showUpdatePopup}
          leaderboardId={currentLeaderboardId}
        />
      )}
      {unsubmittedExams.length > 0 && (
        <UnsubmittedExamPopup
          isOpen={showUnsubmittedPopup}
          onClose={() => setShowUnsubmittedPopup(false)}
          unsubmittedExams={unsubmittedExams}
          onExamDeleted={(examId) => setUnsubmittedExams(prev => prev.filter(exam => exam['exam-id'] !== examId))}
        />
      )}

      <motion.div
        className="content"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1 }}
      >
        {error && <Notification message={error} type="error" />}
        
        <div className="greeting-area">
          <h1>Welcome back, {firstName}!</h1>
          <p>Ready to continue your preparation?</p>
        </div>

        <div>
          <h2 className="section-title">Overview Stats</h2>
          <div className="stats-container">
            {cardData.map((card, index) => (
              <motion.div
                key={index}
                className={`stat-card ${loading ? 'skeleton' : ''}`}
                variants={cardVariants}
                initial="hidden"
                animate="visible"
                custom={index}
                whileTap={{ scale: 0.98 }}
              >
                <AnimatePresence mode="wait">
                  {loading ? (
                    <motion.div key="skeleton" initial="hidden" animate="hidden" exit="exit" variants={fadeTransition} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                      <div className="skeleton-title"></div>
                      <div className="skeleton-value"></div>
                    </motion.div>
                  ) : (
                    <motion.div key="content" initial="hidden" animate="visible" variants={fadeTransition}>
                      <div className="info-text">{card.title}</div>
                      <motion.div
                        className="number"
                        initial={{ scale: animateNumbers ? 0 : 1, opacity: animateNumbers ? 0 : 1 }}
                        animate={{ scale: 1, opacity: 1 }}
                        transition={{ type: "spring", stiffness: 200, damping: 12, delay: index * 0.1 }}
                      >
                        {card.value}
                      </motion.div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            ))}
          </div>
        </div>

        <div>
          <h2 className="section-title">Subject Analysis</h2>
          <div className="subjects-container">
            {subjects.map((sub, index) => (
              <motion.div
                key={sub.id}
                variants={cardVariants}
                initial="hidden"
                animate="visible"
                custom={index + 4}
              >
                <Link to={`/analyse/${sub.id}`} className={`subject-card ${sub.class}`}>
                  <h3>{sub.name}</h3>
                </Link>
              </motion.div>
            ))}
          </div>
        </div>

      </motion.div>
    </>
  );
}

export default Content;
