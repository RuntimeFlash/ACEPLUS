import React, { useEffect, useMemo, useState } from 'react';
import {
  RiCalendarScheduleLine,
  RiCheckboxCircleLine,
  RiRefreshLine,
  RiFireLine,
  RiTrophyLine,
  RiArrowRightLine,
  RiInformationLine,
  RiKeyboardLine,
  RiCheckLine,
  RiCloseLine,
  RiSparklingLine,
  RiBookOpenLine
} from 'react-icons/ri';
import { api } from '../utils/api';
import './MistakeReplay.css';

const OPTION_KEYS = ['a', 'b', 'c', 'd'];

const formatDateTime = (isoString) => {
  if (!isoString) return null;
  try {
    const dt = new Date(isoString);
    if (Number.isNaN(dt.getTime())) return null;
    return dt.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  } catch (_) {
    return null;
  }
};

function MistakeReplay() {
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [cards, setCards] = useState([]);
  const [totalInitial, setTotalInitial] = useState(0);
  const [sessionStreak, setSessionStreak] = useState(0);
  const [sessionAnalytics, setSessionAnalytics] = useState({ totalReviewed: 0, correctCount: 0 });
  const [nextDueAt, setNextDueAt] = useState(null);
  const [selectedOption, setSelectedOption] = useState('');
  const [feedback, setFeedback] = useState(null);
  const [error, setError] = useState('');

  const currentCard = useMemo(() => {
    if (!cards.length) return null;
    return cards[0];
  }, [cards]);

  const loadQueue = async () => {
    setLoading(true);
    setError('');
    setFeedback(null);
    try {
      const data = await api.getMistakeReplay(20);
      const queueCards = Array.isArray(data.cards) ? data.cards : [];
      setCards(queueCards);
      setTotalInitial(queueCards.length);
      setNextDueAt(data.next_due_at || null);
      setSelectedOption('');
    } catch (err) {
      setError(err.message || 'Failed to load replay queue.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQueue();
  }, []);

  const handleSubmit = async () => {
    if (!currentCard || !selectedOption || submitting) return;
    setSubmitting(true);
    setError('');
    try {
      const result = await api.reviewMistakeReplay(currentCard.replay_id, selectedOption);
      const isCorrect = !!result.is_correct;
      
      setFeedback({
        isCorrect,
        correctOption: result.correct_option,
        nextDueAt: result.next_due_at
      });

      // Update streaks & session analytics
      if (isCorrect) {
        setSessionStreak((prev) => prev + 1);
        setSessionAnalytics((prev) => ({
          totalReviewed: prev.totalReviewed + 1,
          correctCount: prev.correctCount + 1
        }));
      } else {
        setSessionStreak(0);
        setSessionAnalytics((prev) => ({
          ...prev,
          totalReviewed: prev.totalReviewed + 1
        }));
      }

      if (result.next_due_at) {
        setNextDueAt(result.next_due_at);
      }
    } catch (err) {
      setError(err.message || 'Failed to submit replay answer.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleNext = () => {
    if (!feedback) return;
    setCards((prev) => prev.filter((card) => card.replay_id !== currentCard.replay_id));
    setFeedback(null);
    setSelectedOption('');
  };

  // Keyboard shortcut listener
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Don't intercept typing in inputs if any are focused
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement?.tagName)) {
        return;
      }

      const key = e.key.toLowerCase();
      
      // Handle Option Selection (A, B, C, D or 1, 2, 3, 4)
      if (!feedback && !submitting && currentCard) {
        if (key === 'a' || key === '1') setSelectedOption('a');
        else if (key === 'b' || key === '2') setSelectedOption('b');
        else if (key === 'c' || key === '3') setSelectedOption('c');
        else if (key === 'd' || key === '4') setSelectedOption('d');
      }

      // Handle Enter / Space keys
      if (key === 'enter' || key === ' ') {
        e.preventDefault(); // Prevent scroll on Space
        if (feedback) {
          handleNext();
        } else if (selectedOption && !submitting) {
          handleSubmit();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentCard, selectedOption, feedback, submitting]);

  // Dynamic calculations
  const progressPercent = useMemo(() => {
    if (totalInitial === 0) return 0;
    const completed = totalInitial - cards.length;
    return Math.round((completed / totalInitial) * 100);
  }, [cards.length, totalInitial]);

  const subjectBreakdown = useMemo(() => {
    const counts = {};
    cards.forEach((card) => {
      const sub = card.subject || 'Unknown';
      counts[sub] = (counts[sub] || 0) + 1;
    });
    return Object.entries(counts);
  }, [cards]);

  const progressText = `${totalInitial - cards.length} of ${totalInitial} completed`;

  if (loading) {
    return (
      <div className="replay-page">
        <div className="replay-loading-wrap">
          <div className="spinner" />
          <p>Loading mistake replay dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="replay-page">
      {/* ProgressBar */}
      {totalInitial > 0 && cards.length > 0 && (
        <div className="replay-progress-bar-container">
          <div className="replay-progress-header">
            <span>Session Progress</span>
            <span className="progress-details">{progressText} ({progressPercent}%)</span>
          </div>
          <div className="replay-progress-track">
            <div 
              className="replay-progress-fill" 
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      )}

      <div className="replay-layout">
        {/* Left Side: Main Question / Empty Card */}
        <div className="replay-main-col">
          {error && <div className="replay-error">{error}</div>}

          {!currentCard ? (
            <div className="replay-empty-card card glass">
              <div className="replay-celebrate-glow" />
              <div className="replay-empty-icon-wrap">
                <RiSparklingLine className="replay-empty-icon" />
              </div>
              <h3>Review Queue Cleared!</h3>
              <p className="replay-empty-text">
                Excellent work. You've cleared all your due cards and strengthened your weak spots. Keep solving exams to identify new concepts for spaced repetition.
              </p>

              {sessionAnalytics.totalReviewed > 0 && (
                <div className="session-summary-box">
                  <h4>Session Recap</h4>
                  <div className="session-summary-grid">
                    <div>
                      <span>Reviewed</span>
                      <strong>{sessionAnalytics.totalReviewed}</strong>
                    </div>
                    <div>
                      <span>Success Rate</span>
                      <strong>
                        {sessionAnalytics.totalReviewed > 0
                          ? `${Math.round((sessionAnalytics.correctCount / sessionAnalytics.totalReviewed) * 100)}%`
                          : '0%'}
                      </strong>
                    </div>
                  </div>
                </div>
              )}

              {nextDueAt ? (
                <div className="replay-next-due-card">
                  <RiCalendarScheduleLine />
                  <div>
                    <span>Next Review Session Unlocks</span>
                    <strong>{formatDateTime(nextDueAt) || nextDueAt}</strong>
                  </div>
                </div>
              ) : (
                <p className="replay-next-due">No additional reviews scheduled. You are fully caught up!</p>
              )}

              <button type="button" className="btn-primary replay-empty-refresh-btn" onClick={loadQueue}>
                <RiRefreshLine />
                Check for Updates
              </button>
            </div>
          ) : (
            <div className="replay-card card">
              <div className="replay-card-header">
                <span className={`subject-badge ${currentCard.subject?.toLowerCase() || 'general'}`}>
                  {currentCard.subject || 'Subject'}
                </span>
                <span className="spaced-level-label">
                  Spaced Level: {currentCard.review_step}/5
                </span>
              </div>

              <div className="replay-question-content">
                <h3>{currentCard.question}</h3>

                <div className="replay-options-grid">
                  {OPTION_KEYS.map((key) => {
                    const optionText = currentCard.options?.[key];
                    if (!optionText) return null;

                    // Compute styling classes
                    let optClass = '';
                    let optIcon = null;

                    if (feedback) {
                      if (feedback.correctOption === key) {
                        optClass = 'correct';
                        optIcon = <RiCheckLine className="opt-status-icon success" />;
                      } else if (selectedOption === key) {
                        optClass = 'wrong';
                        optIcon = <RiCloseLine className="opt-status-icon error" />;
                      } else {
                        optClass = 'disabled';
                      }
                    } else if (selectedOption === key) {
                      optClass = 'selected';
                    }

                    return (
                      <button
                        key={key}
                        type="button"
                        className={`replay-opt-btn ${optClass}`}
                        onClick={() => !feedback && setSelectedOption(key)}
                        disabled={!!feedback || submitting}
                      >
                        <div className="opt-inner">
                          <span className="opt-bubble">{key.toUpperCase()}</span>
                          <span className="opt-text">{optionText}</span>
                        </div>
                        {optIcon}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Action Area */}
              <div className="replay-card-footer">
                {!feedback ? (
                  <button
                    type="button"
                    className="btn-primary replay-submit-btn"
                    disabled={!selectedOption || submitting}
                    onClick={handleSubmit}
                  >
                    {submitting ? (
                      <>
                        <span className="spinner" style={{ width: 14, height: 14 }} />
                        <span>Scheduling...</span>
                      </>
                    ) : (
                      <>
                        <span>Check & Schedule</span>
                        <RiArrowRightLine />
                      </>
                    )}
                  </button>
                ) : (
                  <button
                    type="button"
                    className="btn-primary replay-continue-btn"
                    onClick={handleNext}
                  >
                    <span>Continue</span>
                    <RiArrowRightLine />
                  </button>
                )}

                <div className="keyboard-helper">
                  <RiKeyboardLine />
                  <span>
                    {!selectedOption 
                      ? 'Press [A, B, C, D] to select option' 
                      : !feedback 
                      ? 'Press [Enter] to check & submit' 
                      : 'Press [Enter] to continue'}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Feedback Overlay Panel (Integrated right under card if active) */}
          {feedback && currentCard && (
            <div className={`replay-feedback-panel ${feedback.isCorrect ? 'correct' : 'wrong'}`}>
              <div className="feedback-hdr">
                {feedback.isCorrect ? (
                  <>
                    <div className="feedback-status-indicator correct">
                      <RiCheckLine />
                    </div>
                    <div>
                      <h4>Perfectly Correct!</h4>
                      <p>You've successfully answered this question and leveled up its interval.</p>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="feedback-status-indicator wrong">
                      <RiCloseLine />
                    </div>
                    <div>
                      <h4>Incorrect Attempt</h4>
                      <p>Don't worry! This card has been scheduled for review again soon.</p>
                    </div>
                  </>
                )}
              </div>
              <div className="feedback-details-box">
                <div className="feedback-detail-item">
                  <span>Correct Option</span>
                  <strong>Option {String(feedback.correctOption).toUpperCase()}</strong>
                </div>
                {feedback.nextDueAt && (
                  <div className="feedback-detail-item">
                    <span>Next Review Scheduled</span>
                    <strong>{formatDateTime(feedback.nextDueAt) || feedback.nextDueAt}</strong>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Right Side: Analytics & Shortcut Guides */}
        <div className="replay-sidebar-col">
          {/* Streak Widget */}
          <div className="sidebar-widget streak-widget glass">
            <div className="widget-header">
              <RiFireLine className={`streak-icon ${sessionStreak > 0 ? 'active' : ''}`} />
              <div>
                <span>Session Streak</span>
                <h4>{sessionStreak} Correct</h4>
              </div>
            </div>
            {sessionStreak > 2 && (
              <p className="streak-cheer">🔥 You are on a roll! Keep it up!</p>
            )}
          </div>

          {/* Active Card Spaced Repetition Level */}
          {currentCard && (
            <div className="sidebar-widget spaced-widget glass">
              <h4>Spaced Repetition Stage</h4>
              <div className="spaced-level-bar">
                {[1, 2, 3, 4, 5].map((lvl) => {
                  const isActive = currentCard.review_step >= lvl;
                  const isCurrent = currentCard.review_step + 1 === lvl;
                  return (
                    <div 
                      key={lvl} 
                      className={`spaced-dot ${isActive ? 'active' : ''} ${isCurrent ? 'next' : ''}`}
                      title={`Interval Stage ${lvl}`}
                    />
                  );
                })}
              </div>
              <div className="spaced-intervals-info">
                <RiInformationLine />
                <span>Correct answers unlock longer repetition intervals (up to 30 days).</span>
              </div>
            </div>
          )}

          {/* Subject Queue List */}
          {subjectBreakdown.length > 0 && (
            <div className="sidebar-widget queue-widget glass">
              <h4>Review Queue Topics</h4>
              <ul className="queue-topics-list">
                {subjectBreakdown.map(([sub, count]) => (
                  <li key={sub} className="topic-item">
                    <span className={`topic-bullet ${sub.toLowerCase()}`} />
                    <span className="topic-name">{sub}</span>
                    <span className="topic-count">{count} card{count > 1 ? 's' : ''}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Keyboard Reference Sheet */}
          <div className="sidebar-widget shortcut-guide-widget glass">
            <h4>Keyboard Shortcuts</h4>
            <div className="shortcuts-grid">
              <div className="shortcut-item">
                <kbd>A</kbd> <kbd>B</kbd> <kbd>C</kbd> <kbd>D</kbd>
                <span>Select options</span>
              </div>
              <div className="shortcut-item">
                <kbd>Enter</kbd> or <kbd>Space</kbd>
                <span>Check / Continue</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default MistakeReplay;
