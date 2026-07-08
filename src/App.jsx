import React, { useState, useEffect } from "react";
import {
  Route,
  Routes,
  Navigate,
  useLocation,
  useParams,
} from "react-router-dom";
import Sidebar from "./components/sidebar";
import Content from "./components/body-content";
import BottomNav from "./components/mobile-bottomnav";
import Exam from "./components/Exam";
import Login from "./components/Login";
import Register from "./components/Register";
import ProtectedRoute from "./components/ProtectedRoute";
import NotFound from "./components/NotFound";
import Analysis from "./components/AnalysisView";
import SubjectDetails from "./components/SubjectDetails";
import ExamTaking from "./components/ExamTaking";
import ExamResults from "./components/ExamResults";
import History from "./components/History";
import TestSeries from "./components/TestSeries";
import Header from "./components/Header";
import CreateTest from "./components/CreateTest";
import LandingPage from "./components/LandingPage";
import MistakeReplay from "./components/MistakeReplay";
import Profile from "./components/Profile";
import Friends from "./components/Friends";

import "./design-tokens.css";
import "./App.css";

const ScrollToTop = () => {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
};

const ExamLegacyRedirect = () => {
  const { id } = useParams();
  return <Navigate to={`/exam/g/${id}`} replace />;
};

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isHeaderVisible, setIsHeaderVisible] = useState(true);
  const [completedTasks, setCompletedTasks] = useState([]);
  const [refreshCoins, setRefreshCoins] = useState(false);
  const location = useLocation();

  // Sidebar toggle state
  const [sidebarOpen, setSidebarOpen] = useState(() => window.innerWidth > 768);
  const [isMobile, setIsMobile] = useState(() => window.innerWidth <= 768);

  // Track window resize for mobile detection
  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth <= 768;
      setIsMobile(mobile);
      if (mobile) {
        setSidebarOpen(false);
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const toggleSidebar = () => setSidebarOpen(prev => !prev);

  // PWA install logic
  const [isAndroid] = useState(() => /Android/i.test(navigator.userAgent));
  const [isInstalled, setIsInstalled] = useState(() => {
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
    const isIOSStandalone = window.navigator.standalone === true; 
    return isStandalone || isIOSStandalone;
  });
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [downloadFinished, setDownloadFinished] = useState(false);

  useEffect(() => {
    const checkInstallation = () => {
      const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
      const isIOSStandalone = window.navigator.standalone === true; 
      setIsInstalled(isStandalone || isIOSStandalone);
    };

    const mediaQuery = window.matchMedia('(display-mode: standalone)');
    mediaQuery.addEventListener('change', checkInstallation);

    const handleBeforeInstallPrompt = (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
    };

    const handleAppInstalled = () => {
      setDeferredPrompt(null);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('appinstalled', handleAppInstalled);

    return () => {
      mediaQuery.removeEventListener('change', checkInstallation);
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, []);

  const startDownloader = () => {
    setIsDownloading(true);
    setDownloadProgress(0);
    setDownloadFinished(false);

    const duration = 20000;
    const intervalTime = 100;
    const totalSteps = duration / intervalTime;
    let currentStep = 0;

    const timer = setInterval(() => {
      currentStep++;
      const progress = Math.min(Math.round((currentStep / totalSteps) * 100), 100);
      setDownloadProgress(progress);

      if (currentStep >= totalSteps) {
        clearInterval(timer);
        setIsDownloading(false);
        setDownloadFinished(true);
      }
    }, intervalTime);
  };

  const handleInstallClick = async () => {
    if (!deferredPrompt) {
      alert(
        "Direct installation trigger is not supported on this browser. " +
        "We will simulate setup; please click 'Add' or 'Install' if prompted, or use the menu icon (⋮) in Chrome's top-right corner to 'Install app' manually."
      );
      startDownloader();
      return;
    }
    try {
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      console.log(`User response to the install prompt: ${outcome}`);
      setDeferredPrompt(null);
    } catch (err) {
      console.error("Installation prompt error:", err);
    }
    startDownloader();
  };

  const handleTaskCompletion = (tasks) => {
    setCompletedTasks(tasks);
    setRefreshCoins(true);
  };

  const updateAuthState = () => {
    const token = localStorage.getItem("token");
    setIsAuthenticated(!!token);
  };

  useEffect(() => {
    updateAuthState();
  }, []);

  const getStatusText = (progress) => {
    if (progress < 20) return "Downloading application package...";
    if (progress < 45) return "Extracting bundle files...";
    if (progress < 70) return "Setting up offline resources...";
    if (progress < 90) return "Configuring application database...";
    return "Finalizing installation...";
  };

  // THE BLOCKADE: Show if they are on Android and haven't installed it yet
  if (isAndroid && !isInstalled) {
    return (
      <div className="pwa-blockade-container">
        <div className="pwa-card">
          {downloadFinished ? (
            <>
              <div className="pwa-success-icon">
                <i className="fa-solid fa-circle-check"></i>
              </div>
              <h2 className="pwa-success-title">App Ready! 🎉</h2>
              <p className="pwa-launch-tip">
                AcePlus has been successfully set up. Close this browser tab, look for the <strong>Ace+</strong> icon on your home screen or app list, and open it to begin!
              </p>
            </>
          ) : isDownloading ? (
            <>
              <h2 className="pwa-success-title" style={{ marginBottom: '24px' }}>Installing AcePlus</h2>
              <div className="pwa-downloader-container">
                <div className="pwa-progress-percentage">{downloadProgress}%</div>
                <div className="pwa-progress-bar-bg">
                  <div 
                    className="pwa-progress-bar-fill" 
                    style={{ width: `${downloadProgress}%` }}
                  ></div>
                </div>
                <div className="pwa-status-text">{getStatusText(downloadProgress)}</div>
              </div>
            </>
          ) : (
            <>
              <img src="/logo512.png" alt="AcePlus Logo" className="pwa-logo" />
              <h1 className="pwa-title">Install AcePlus</h1>
              <p className="pwa-description">
                To take exams, practice test series, and view your detailed performance analysis, you must install the AcePlus app on your phone.
              </p>
              
              <button className="pwa-btn-install" onClick={handleInstallClick}>
                <i className="fa-solid fa-download"></i>
                Install App to Unlock
              </button>

              <div className="pwa-manual-instructions">
                <h3 className="pwa-manual-title">Or Install Manually</h3>
                <ul className="pwa-steps">
                  <li>
                    <span className="pwa-step-num">1</span>
                    <span>Tap Chrome's menu icon <strong>(⋮)</strong> in the top-right corner.</span>
                  </li>
                  <li>
                    <span className="pwa-step-num">2</span>
                    <span>Select <strong>"Install app"</strong> or <strong>"Add to Home screen"</strong>.</span>
                  </li>
                  <li>
                    <span className="pwa-step-num">3</span>
                    <span>Open <strong>AcePlus</strong> from your home screen to log in.</span>
                  </li>
                </ul>
              </div>
            </>
          )}
        </div>
      </div>
    );
  }

  const showHeader = location.pathname !== '/';

  // Determine content class based on auth and sidebar state
  const getContentClass = () => {
    if (!isAuthenticated) return 'no-sidebar';
    if (isMobile) return 'sidebar-collapsed'; // On mobile, content never shifts
    return sidebarOpen ? 'sidebar-open' : 'sidebar-collapsed';
  };

  return (
    <div className={`App ${isHeaderVisible ? "" : "header-hidden"}`}>
      {showHeader && (
        <Header
          onVisibilityChange={setIsHeaderVisible}
          completedTasks={completedTasks}
          onToggleSidebar={toggleSidebar}
          isMobile={isMobile}
          isOpen={sidebarOpen}
        />
      )}

      <div className="app-layout">
        {isAuthenticated && !isMobile && (
          <Sidebar
            isOpen={sidebarOpen}
            onToggle={toggleSidebar}
            isMobile={false}
          />
        )}

        <main className={`app-content ${getContentClass()}`}>
          <Routes>
            <Route
              path="/"
              element={isAuthenticated ? <Navigate to="/home" /> : <LandingPage />}
            />
            <Route
              path="/home"
              element={
                <ProtectedRoute updateAuthState={updateAuthState}>
                  <Content updateAuthState={updateAuthState} />
                  <ScrollToTop />
                </ProtectedRoute>
              }
            />
            <Route
              path="/login"
              element={isAuthenticated ? <Navigate to="/home" /> : <Login />}
            />
            <Route
              path="/register"
              element={isAuthenticated ? <Navigate to="/home" /> : <Register />}
            />
            <Route
              path="/create"
              element={
                <ProtectedRoute updateAuthState={updateAuthState}>
                  <Exam />
                </ProtectedRoute>
              }
            />
            <Route
              path="/analyse"
              element={
                <ProtectedRoute updateAuthState={updateAuthState}>
                  <Analysis />
                </ProtectedRoute>
              }
            />
            <Route
              path="/analyse/:subject"
              element={
                <ProtectedRoute updateAuthState={updateAuthState}>
                  <SubjectDetails />
                </ProtectedRoute>
              }
            />
            <Route
              path="/history"
              element={
                <ProtectedRoute updateAuthState={updateAuthState}>
                  <History />
                </ProtectedRoute>
              }
            />
            <Route
              path="/replay"
              element={
                <ProtectedRoute updateAuthState={updateAuthState}>
                  <MistakeReplay />
                </ProtectedRoute>
              }
            />
            <Route
              path="/profile"
              element={
                <ProtectedRoute updateAuthState={updateAuthState}>
                  <Profile />
                </ProtectedRoute>
              }
            />
            <Route
              path="/friends"
              element={
                <ProtectedRoute updateAuthState={updateAuthState}>
                  <Friends />
                </ProtectedRoute>
              }
            />
            <Route
              path="/exam/g/:id"
              element={
                <ProtectedRoute updateAuthState={updateAuthState}>
                  <ExamTaking />
                </ProtectedRoute>
              }
            />
            <Route
              path="/exam/:id"
              element={
                <ProtectedRoute updateAuthState={updateAuthState}>
                  <ExamLegacyRedirect />
                </ProtectedRoute>
              }
            />
            <Route
              path="/test-series"
              element={
                <ProtectedRoute updateAuthState={updateAuthState}>
                  <TestSeries />
                </ProtectedRoute>
              }
            />
            <Route
              path="/create-test"
              element={
                <ProtectedRoute updateAuthState={updateAuthState}>
                  <CreateTest />
                </ProtectedRoute>
              }
            />
            {/* Catch-all route */}
            <Route
              path="*"
              element={isAuthenticated ? <NotFound /> : <Navigate to="/login" />}
            />
          </Routes>
        </main>
      </div>

      {isAuthenticated && isMobile && <BottomNav />}
    </div>
  );
}

export default App;
