import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { RiDashboardLine, RiFileAddLine, RiFileTextLine, RiBarChartLine, RiHistoryLine, RiLoopLeftLine } from 'react-icons/ri';

function Sidebar({ isHeaderHidden }) {
  const navigate = useNavigate();
  const location = useLocation();

  const isHomeActive = location.pathname === '/' || location.pathname === '/home';

  return (
    <div className={`sidebar ${isHeaderHidden ? 'header-hidden' : ''}`}>
      <button onClick={() => navigate('/home')} className={`btn ${isHomeActive ? 'active' : ''}`}>
        <RiDashboardLine />
        <span>Home</span>
      </button>
      <button onClick={() => navigate('/create')} className={`btn ${location.pathname === '/create' ? 'active' : ''}`}>
        <RiFileAddLine />
        <span>Create Exam</span>
      </button>
      <button onClick={() => navigate('/test-series')} className={`btn ${location.pathname === '/test-series' ? 'active' : ''}`}>
        <RiFileTextLine />
        <span>Test Series</span>
      </button>
      <button onClick={() => navigate('/analyse')} className={`btn ${location.pathname === '/analyse' ? 'active' : ''}`}>
        <RiBarChartLine />
        <span>Analyse</span>
      </button>
      <button onClick={() => navigate('/history')} className={`btn ${location.pathname === '/history' ? 'active' : ''}`}>
        <RiHistoryLine />
        <span>History</span>
      </button>
      <button onClick={() => navigate('/replay')} className={`btn ${location.pathname === '/replay' ? 'active' : ''}`}>
        <RiLoopLeftLine />
        <span>Replay</span>
      </button>
    </div>
  );
}

export default Sidebar;
