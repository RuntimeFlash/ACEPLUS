import React, { useState, useEffect } from 'react';
import { FaCoins } from 'react-icons/fa';
import { RiUser3Line, RiUserSharedLine, RiMenuLine } from 'react-icons/ri';
import { useNavigate, useLocation } from 'react-router-dom';
import { api } from '../utils/api';
import logo from './logo512.png';
import './Header.css';
import Coins from './Coins';

const Header = ({ completedTasks, onToggleSidebar, isMobile }) => {
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

  const handleCoinsClick = () => {
    setCoinsPopupOpen(true);
  };

  const handleClosePopup = () => {
    setCoinsPopupOpen(false);
  };

  return (
    <>
      <div className={`header ${isVisible ? '' : 'header--hidden'}`}>
        <div className="header-left">
          {isMobile && (
            <button
              className="header-menu-btn"
              onClick={onToggleSidebar}
              aria-label="Toggle navigation menu"
            >
              <RiMenuLine />
            </button>
          )}
          <img src={logo} alt="AcePlus Logo" className="header-logo" />
          <h1 className="header-text">ace+</h1>
        </div>
        {isAuthenticated && (
          <div className="header-actions">
            <button
              className={`header-action-btn ${location.pathname === '/profile' ? 'active' : ''}`}
              onClick={() => navigate('/profile')}
              aria-label="Open profile"
            >
              <RiUser3Line />
            </button>
            <button
              className={`header-action-btn ${location.pathname === '/friends' ? 'active' : ''}`}
              onClick={() => navigate('/friends')}
              aria-label="Open friends"
            >
              <RiUserSharedLine />
            </button>
          </div>
        )}
        {isAuthenticated && (
          <div className={`header-right ${isLoading ? 'is-loading' : 'is-loaded'}`} onClick={handleCoinsClick} style={{ cursor: 'pointer' }}>
            <div className="skeleton skeleton-coin"></div>
            <div className="coins-container">
              <FaCoins className="coins-icon" />
              <span className="coins-amount">{coins}</span>
            </div>
          </div>
        )}
      </div>
      {isAuthenticated && <Coins isOpen={isCoinsPopupOpen} onClose={handleClosePopup} tasks={tasks} coins={coins} />}
    </>
  );
};

export default Header;
