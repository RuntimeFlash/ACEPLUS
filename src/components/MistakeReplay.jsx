import React, { useEffect, useMemo, useState } from 'react';
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
      setCards(Array.isArray(data.cards) ? data.cards : []);
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
      setFeedback({
        isCorrect: !!result.is_correct,
        correctOption: result.correct_option,
        nextDueAt: result.next_due_at
      });
      setCards((prev) => prev.filter((card) => card.replay_id !== currentCard.replay_id));
      setSelectedOption('');
      if (result.next_due_at) {
        setNextDueAt(result.next_due_at);
      }
    } catch (err) {
      setError(err.message || 'Failed to submit replay answer.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="replay-page">
        <div className="replay-panel">
          <h2>Mistake Replay</h2>
          <p>Loading your due cards...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="replay-page">
      <div className="replay-panel">
        <div className="replay-header">
          <h2>Mistake Replay</h2>
          <button type="button" className="replay-refresh-btn" onClick={loadQueue}>
            Refresh
          </button>
        </div>

        {feedback && (
          <div className={`replay-feedback ${feedback.isCorrect ? 'correct' : 'wrong'}`}>
            {feedback.isCorrect ? 'Correct. ' : 'Incorrect. '}
            Correct answer: {String(feedback.correctOption || '').toUpperCase()}
            {feedback.nextDueAt ? ` | Next review: ${formatDateTime(feedback.nextDueAt) || feedback.nextDueAt}` : ''}
          </div>
        )}

        {error && <div className="replay-error">{error}</div>}

        {!currentCard ? (
          <div className="replay-empty">
            <p>No cards are due right now.</p>
            {nextDueAt && (
              <p className="replay-next-due">
                Next card due at: {formatDateTime(nextDueAt) || nextDueAt}
              </p>
            )}
          </div>
        ) : (
          <>
            <p className="replay-meta">
              Due now: {cards.length} | Subject: {currentCard.subject} | Spaced level: {currentCard.review_step}/5
            </p>
            <div className="replay-question-card">
              <h3>{currentCard.question}</h3>
              <div className="replay-options">
                {OPTION_KEYS.map((key) => {
                  const optionText = currentCard.options?.[key];
                  if (!optionText) return null;
                  return (
                    <button
                      key={key}
                      type="button"
                      className={`replay-option-btn ${selectedOption === key ? 'selected' : ''}`}
                      onClick={() => setSelectedOption(key)}
                    >
                      <span className="opt-key">{key.toUpperCase()})</span> {optionText}
                    </button>
                  );
                })}
              </div>
            </div>
            <div className="replay-actions">
              <button
                type="button"
                className="replay-submit-btn"
                disabled={!selectedOption || submitting}
                onClick={handleSubmit}
              >
                {submitting ? 'Submitting...' : 'Check & Schedule'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default MistakeReplay;
