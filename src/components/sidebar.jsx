import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  RiDashboardLine,
  RiFileAddLine,
  RiFileTextLine,
  RiBarChartLine,
  RiHistoryLine,
  RiLoopLeftLine,
  RiUser3Line,
  RiUserSharedLine,
  RiMenuFoldLine,
  RiMenuUnfoldLine
} from 'react-icons/ri';
import './sidebar.css';

const navItems = [
  { path: '/home', label: 'Home', icon: RiDashboardLine, matchPaths: ['/', '/home'] },
  { path: '/create', label: 'Create Exam', icon: RiFileAddLine },
  { path: '/test-series', label: 'Test Series', icon: RiFileTextLine },
  { path: '/analyse', label: 'Analyse', icon: RiBarChartLine },
  { path: '/history', label: 'History', icon: RiHistoryLine },
  { path: '/replay', label: 'Replay', icon: RiLoopLeftLine },
  { path: '/profile', label: 'Profile', icon: RiUser3Line },
  { path: '/friends', label: 'Friends', icon: RiUserSharedLine },
];

function Sidebar({ isOpen, onToggle, isMobile }) {
  const navigate = useNavigate();
  const location = useLocation();

  const handleNav = (path) => {
    navigate(path);
    // Close sidebar on mobile after navigation
    if (isMobile && onToggle) {
      onToggle();
    }
  };

  return (
    <aside className={`sidebar ${isOpen ? 'expanded' : ''} ${isMobile && isOpen ? 'mobile-open' : ''}`}>
      <nav className="sidebar-nav">
        {navItems.map(({ path, label, icon: Icon, matchPaths }) => {
          const isActive = matchPaths
            ? matchPaths.includes(location.pathname)
            : location.pathname === path;

          return (
            <button
              key={path}
              onClick={() => handleNav(path)}
              className={`sidebar-btn ${isActive ? 'active' : ''}`}
              title={!isOpen ? label : undefined}
            >
              <span className="sidebar-btn-icon"><Icon /></span>
              <span className="sidebar-btn-label">{label}</span>
            </button>
          );
        })}
      </nav>
    </aside>
  );
}

export default Sidebar;
