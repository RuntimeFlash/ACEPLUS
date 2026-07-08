import React, { useState, useEffect } from 'react';
import { FaCoins } from 'react-icons/fa';
import { RiUser3Line, RiUserSharedLine, RiMenuLine, RiSparklingLine } from 'react-icons/ri';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '../utils/api';
import logo from './logo512.png';
import './Header.css';
import Coins from './Coins';

const Header = ({ completedTasks, onToggleSidebar, isMobile, isOpen }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [coins, setCoins] = useState(0);
  const [tasks, setTasks] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCoinsPopupOpen, setCoinsPopupOpen] = useState(false);
  const isAuthenticated = !!localStorage.getItem('token');
  const [isVisible, setIsVisible] = useState(true);
  const [lastScrollY, setLastScrollY] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      if (currentScrollY > lastScrollY && currentScrollY > 56) {
        setIsVisible(false);
      } else {
        setIsVisible(true);
      }
      setLastScrollY(currentScrollY);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [lastScrollY]);

  const fetchCoinData = async () => {
    if (!isAuthenticated) return;
    try {
      const data = await api.fetchCoins();
      setCoins(data.coins);
      setTasks(data.tasks || []);
    } catch (error) {
      console.error("Failed to fetch coins data", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      const timer = setTimeout(() => {
        fetchCoinData();
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (completedTasks && completedTasks.length > 0) {
      fetchCoinData();
    }
  }, [completedTasks]);

  return (
    <>
      <AnimatePresence>
        <motion.header 
          className={`premium-header ${isVisible ? '' : 'premium-header--hidden'}`}
          initial={{ y: -100 }}
          animate={{ y: 0 }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        >
          <div className="premium-header-content">
            
            {/* Left: Sidebar Toggle */}
            <div className="header-left">
              {isAuthenticated && (
                <motion.button
                  className="header-menu-btn"
                  onClick={onToggleSidebar}
                  whileHover={{ scale: 1.05, backgroundColor: 'var(--bg-hover)' }}
                  whileTap={{ scale: 0.95 }}
                  aria-label="Toggle sidebar"
                >
                  <RiMenuLine />
                </motion.button>
              )}
            </div>
              
            {/* Center: Logo & Brand */}
            <div className="header-center">
              <motion.div 
                className="header-brand"
                whileHover={{ scale: 1.02 }}
                onClick={() => navigate('/home')}
              >
                <div className="logo-wrapper">
                  <img src={logo} alt="AcePlus Logo" className="header-logo" />
                  <motion.div 
                    className="logo-glow"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
                  />
                </div>
                <div className="brand-text-wrapper">
                  <h1 className="header-text">ace+</h1>
                  <RiSparklingLine className="brand-sparkle" />
                </div>
              </motion.div>
            </div>

            {/* Right: Actions & Coins */}
            <div className="header-right">
            {isAuthenticated && (
              <>
                <motion.div 
                  className={`premium-coins-wrapper ${isLoading ? 'is-loading' : 'is-loaded'}`} 
                  onClick={() => setCoinsPopupOpen(true)}
                  whileHover={{ scale: 1.05, y: -2 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <div className="skeleton skeleton-coin"></div>
                  <div className="premium-coins">
                    <motion.div 
                      className="coin-icon-wrapper"
                      animate={{ y: [0, -3, 0] }}
                      transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                    >
                      <FaCoins className="coins-icon" />
                    </motion.div>
                    <span className="coins-amount">{coins}</span>
                  </div>
                </motion.div>

                <motion.button
                  className={`header-action-btn ${location.pathname === '/profile' ? 'active' : ''}`}
                  onClick={() => navigate('/profile')}
                  whileHover={{ scale: 1.05, y: -2 }}
                  whileTap={{ scale: 0.95 }}
                  aria-label="Open profile"
                >
                  <RiUser3Line />
                </motion.button>
              </>
            )}
            </div>
          </div>
          
          {/* Subtle gradient border bottom */}
          <div className="header-gradient-border" />
        </motion.header>
      </AnimatePresence>

      {isAuthenticated && (
        <Coins isOpen={isCoinsPopupOpen} onClose={() => setCoinsPopupOpen(false)} tasks={tasks} coins={coins} />
      )}
    </>
  );
};

export default Header;

