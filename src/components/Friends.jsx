import React, { useEffect, useMemo, useState } from 'react';
import { api } from '../utils/api';
import Notification from './Notification';
import './Friends.css';

const LEADERBOARD_METRICS = ['xp', 'wins', 'streak'];
const GOAL_TYPES = ['xp', 'wins', 'streak', 'sessions'];
const METRIC_LABELS = {
  xp: 'XP',
  wins: 'Wins',
  streak: 'Streak',
  sessions: 'Sessions'
};

function Friends() {
  const [profile, setProfile] = useState(null);
  const [friends, setFriends] = useState([]);
  const [requests, setRequests] = useState({ incoming: [], outgoing: [] });
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [leaderboardMetric, setLeaderboardMetric] = useState('xp');
  const [leaderboard, setLeaderboard] = useState([]);
  const [challenges, setChallenges] = useState([]);
  const [squads, setSquads] = useState([]);
  const [nudges, setNudges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [notification, setNotification] = useState({ message: '', type: 'info' });

  const [challengeForm, setChallengeForm] = useState({
    title: '',
    goal_type: 'xp',
    goal_value: 100,
    participant_ids: [],
    end_date: ''
  });

  const [squadForm, setSquadForm] = useState({
    name: '',
    member_ids: [],
    goal_title: '',
    goal_type: 'sessions',
    goal_target: 5,
    goal_deadline: ''
  });

  const loadData = async () => {
    setLoading(true);
    try {
      const [me, friendList, reqs, lb, challengeData, squadData, nudgeData] = await Promise.all([
        api.getMyProfile(),
        api.getFriends(),
        api.getFriendRequests(),
        api.getFriendLeaderboard(leaderboardMetric),
        api.getChallenges(),
        api.getSquads(),
        api.getNudges()
      ]);
      setProfile(me);
      setFriends(friendList.friends || []);
      setRequests(reqs);
      setLeaderboard(lb.leaderboard || []);
      setChallenges(challengeData.challenges || []);
      setSquads(squadData.squads || []);
      setNudges(nudgeData.nudges || []);
    } catch (error) {
      setNotification({ message: error.message || 'Failed to load friends data', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    const loadLeaderboard = async () => {
      try {
        const lb = await api.getFriendLeaderboard(leaderboardMetric);
        setLeaderboard(lb.leaderboard || []);
      } catch (error) {
        setNotification({ message: error.message || 'Failed to load leaderboard', type: 'error' });
      }
    };
    if (!loading) {
      loadLeaderboard();
    }
  }, [leaderboardMetric]);

  const friendOptions = useMemo(() => friends.map((f) => f.user_id), [friends]);

  const runSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }
    try {
      const data = await api.searchFriends(searchQuery, 20);
      setSearchResults(data.results || []);
    } catch (error) {
      setNotification({ message: error.message || 'Search failed', type: 'error' });
    }
  };

  const sendFriendRequest = async (identifier) => {
    const normalizedIdentifier = typeof identifier === 'string' ? identifier.trim() : identifier;
    if (!normalizedIdentifier) {
      setNotification({ message: 'Enter a username, ID, or friend code first', type: 'error' });
      return;
    }
    try {
      await api.sendFriendRequest(normalizedIdentifier);
      setNotification({ message: 'Friend request sent', type: 'success' });
      await loadData();
    } catch (error) {
      setNotification({ message: error.message || 'Failed to send request', type: 'error' });
    }
  };

  const respondRequest = async (requestId, action) => {
    try {
      await api.respondFriendRequest(requestId, action);
      await loadData();
    } catch (error) {
      setNotification({ message: error.message || 'Failed to respond request', type: 'error' });
    }
  };

  const removeFriend = async (friendId) => {
    try {
      await api.removeFriend(friendId);
      await loadData();
    } catch (error) {
      setNotification({ message: error.message || 'Failed to remove friend', type: 'error' });
    }
  };

  const sendNudge = async (friendId) => {
    try {
      await api.sendNudge(friendId, 'study', 'Join my study session');
      setNotification({ message: 'Nudge sent', type: 'success' });
      await loadData();
    } catch (error) {
      setNotification({ message: error.message || 'Failed to send nudge', type: 'error' });
    }
  };

  const createChallenge = async () => {
    try {
      await api.createChallenge({
        title: challengeForm.title,
        goal_type: challengeForm.goal_type,
        goal_value: Number(challengeForm.goal_value),
        participant_ids: challengeForm.participant_ids,
        end_date: challengeForm.end_date || undefined
      });
      setChallengeForm({ title: '', goal_type: 'xp', goal_value: 100, participant_ids: [], end_date: '' });
      await loadData();
    } catch (error) {
      setNotification({ message: error.message || 'Failed to create challenge', type: 'error' });
    }
  };

  const createSquad = async () => {
    try {
      await api.createSquad({
        name: squadForm.name,
        member_ids: squadForm.member_ids,
        goal: {
          title: squadForm.goal_title,
          type: squadForm.goal_type,
          target: Number(squadForm.goal_target),
          deadline: squadForm.goal_deadline || undefined
        }
      });
      setSquadForm({
        name: '',
        member_ids: [],
        goal_title: '',
        goal_type: 'sessions',
        goal_target: 5,
        goal_deadline: ''
      });
      await loadData();
    } catch (error) {
      setNotification({ message: error.message || 'Failed to create squad', type: 'error' });
    }
  };

  const markNudgeRead = async (nudgeId) => {
    try {
      await api.markNudgeRead(nudgeId);
      setNudges((prev) => prev.map((item) => (item.nudge_id === nudgeId ? { ...item, read: true } : item)));
    } catch (error) {
      setNotification({ message: error.message || 'Failed to mark nudge as read', type: 'error' });
    }
  };

  const toggleSelection = (field, userId, formSetter) => {
    formSetter((prev) => {
      const current = prev[field];
      const exists = current.includes(userId);
      return { ...prev, [field]: exists ? current.filter((id) => id !== userId) : [...current, userId] };
    });
  };

  if (loading) {
    return (
      <div className="friends-container">
        <section className="friends-card">
          <h2 className="friends-title">Loading friends...</h2>
        </section>
      </div>
    );
  }

  return (
    <div className="friends-container">
      <Notification message={notification.message} type={notification.type} />
      <header className="friends-heading">
        <div>
          <h1 className="friends-title">Friends</h1>
          <p className="friends-subtitle">Build your circle, compete weekly, and stay accountable.</p>
        </div>
        <div className="friends-stats">
          <div className="friends-stat-pill">
            <span>Friends</span>
            <strong>{friends.length}</strong>
          </div>
          <div className="friends-stat-pill">
            <span>Incoming</span>
            <strong>{(requests.incoming || []).length}</strong>
          </div>
          <div className="friends-stat-pill">
            <span>Nudges</span>
            <strong>{nudges.filter((item) => !item.read).length}</strong>
          </div>
        </div>
      </header>

      <section className="friends-card">
        <div className="card-head">
          <h3>Friend Code</h3>
          <p className="friends-muted">Share this code so others can add you quickly.</p>
        </div>
        <div className="friend-code-row">
          <code>{profile?.friend_code || 'N/A'}</code>
          <button onClick={() => navigator.clipboard.writeText(profile?.friend_code || '')}>Copy code</button>
        </div>
      </section>

      <section className="friends-card">
        <div className="card-head">
          <h3>Add Friends</h3>
          <p className="friends-muted">Search by user ID, username, or friend code.</p>
        </div>
        <div className="friends-input-row">
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by user ID, username, or friend code"
          />
          <button onClick={runSearch} disabled={!searchQuery.trim()}>Search</button>
          <button onClick={() => sendFriendRequest(searchQuery)} disabled={!searchQuery.trim()}>Send request</button>
        </div>
        <div className="search-results">
          {searchResults.length === 0 && <p className="friends-muted">No search results yet.</p>}
          {searchResults.map((item) => (
            <div key={item.user_id} className="result-row">
              <div>
                <strong>{item.name}</strong>
                <p>@{item.username} - {item.status}</p>
              </div>
              <button onClick={() => sendFriendRequest(item.user_id)} disabled={item.is_friend}>
                {item.is_friend ? 'Friend' : 'Add'}
              </button>
            </div>
          ))}
        </div>
      </section>

      <div className="friends-grid">
        <section className="friends-card">
          <div className="card-head">
            <h3>Incoming Requests</h3>
            <p className="friends-muted">Accept or decline pending invites.</p>
          </div>
          {(requests.incoming || []).length === 0 && <p className="friends-muted">No incoming requests.</p>}
          {(requests.incoming || []).map((item) => (
            <div key={item.request_id} className="request-row">
              <span>{item.peer?.name} (@{item.peer?.username})</span>
              <div className="row-actions">
                <button onClick={() => respondRequest(item.request_id, 'accept')}>Accept</button>
                <button className="danger" onClick={() => respondRequest(item.request_id, 'decline')}>Decline</button>
              </div>
            </div>
          ))}
          <h4 className="subsection-title">Outgoing Requests</h4>
          {(requests.outgoing || []).length === 0 && <p className="friends-muted">No pending outgoing requests.</p>}
          {(requests.outgoing || []).map((item) => (
            <div key={item.request_id} className="request-row">
              <span>{item.peer?.name} (@{item.peer?.username})</span>
              <small className="friends-muted">Pending</small>
            </div>
          ))}
        </section>

        <section className="friends-card">
          <div className="card-head">
            <h3>Friends List</h3>
            <p className="friends-muted">Send nudges or remove connections.</p>
          </div>
          {friends.length === 0 && <p className="friends-muted">No friends yet.</p>}
          {friends.map((friend) => (
            <div key={friend.user_id} className="friend-row">
              <div>
                <strong>{friend.name}</strong>
                <p>@{friend.username} - {friend.status}</p>
              </div>
              <div className="row-actions">
                <button onClick={() => sendNudge(friend.user_id)}>Nudge</button>
                <button className="danger" onClick={() => removeFriend(friend.user_id)}>Remove</button>
              </div>
            </div>
          ))}
        </section>
      </div>

      <section className="friends-card">
        <div className="card-head">
          <h3>Weekly Leaderboard</h3>
          <p className="friends-muted">Compare top metrics across your network.</p>
        </div>
        <div className="metric-switch">
          {LEADERBOARD_METRICS.map((metric) => (
            <button
              key={metric}
              className={leaderboardMetric === metric ? 'active' : ''}
              onClick={() => setLeaderboardMetric(metric)}
            >
              {METRIC_LABELS[metric]}
            </button>
          ))}
        </div>
        <table className="leaderboard-table">
          <thead>
            <tr><th>Rank</th><th>User</th><th>{METRIC_LABELS[leaderboardMetric]} score</th></tr>
          </thead>
          <tbody>
            {leaderboard.length === 0 && (
              <tr>
                <td colSpan={3} className="table-empty">No leaderboard data yet.</td>
              </tr>
            )}
            {leaderboard.map((entry) => (
              <tr key={`${entry.rank}-${entry.user?.user_id}`}>
                <td>{entry.rank}</td>
                <td>{entry.user?.name}</td>
                <td>{entry.score}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <div className="friends-grid">
        <section className="friends-card">
          <div className="card-head">
            <h3>Create Challenge</h3>
            <p className="friends-muted">Set a target and invite friends to compete.</p>
          </div>
          <div className="friends-form-grid">
            <input
              value={challengeForm.title}
              onChange={(e) => setChallengeForm((prev) => ({ ...prev, title: e.target.value }))}
              placeholder="Challenge title"
            />
            <select value={challengeForm.goal_type} onChange={(e) => setChallengeForm((prev) => ({ ...prev, goal_type: e.target.value }))}>
              {GOAL_TYPES.map((type) => <option key={type} value={type}>{type}</option>)}
            </select>
            <input
              type="number"
              value={challengeForm.goal_value}
              onChange={(e) => setChallengeForm((prev) => ({ ...prev, goal_value: e.target.value }))}
              placeholder="Goal value"
            />
            <input
              type="datetime-local"
              value={challengeForm.end_date}
              onChange={(e) => setChallengeForm((prev) => ({ ...prev, end_date: e.target.value }))}
            />
          </div>
          <div className="member-selector">
            {friendOptions.length === 0 && <p className="friends-muted">Add friends to select participants.</p>}
            {friendOptions.map((id) => (
              <label key={id}>
                <input
                  type="checkbox"
                  checked={challengeForm.participant_ids.includes(id)}
                  onChange={() => toggleSelection('participant_ids', id, setChallengeForm)}
                />
                {id}
              </label>
            ))}
          </div>
          <button onClick={createChallenge}>Create challenge</button>
          <div className="list-stack">
            {challenges.map((challenge) => (
              <div key={challenge.challenge_id} className="mini-card">
                <strong>{challenge.title}</strong>
                <p>{METRIC_LABELS[challenge.goal_type] || challenge.goal_type} target: {challenge.goal_value} - {challenge.status}</p>
                {challenge.participants?.map((participant) => (
                  <small key={participant.user?.user_id}>
                    {participant.user?.name}: {participant.progress} {participant.completed ? '(done)' : ''}
                  </small>
                ))}
              </div>
            ))}
          </div>
        </section>

        <section className="friends-card">
          <div className="card-head">
            <h3>Create Study Squad</h3>
            <p className="friends-muted">Coordinate recurring goals with a small team.</p>
          </div>
          <div className="friends-form-grid">
            <input
              value={squadForm.name}
              onChange={(e) => setSquadForm((prev) => ({ ...prev, name: e.target.value }))}
              placeholder="Squad name"
            />
            <input
              value={squadForm.goal_title}
              onChange={(e) => setSquadForm((prev) => ({ ...prev, goal_title: e.target.value }))}
              placeholder="Goal title"
            />
            <select value={squadForm.goal_type} onChange={(e) => setSquadForm((prev) => ({ ...prev, goal_type: e.target.value }))}>
              {GOAL_TYPES.map((type) => <option key={type} value={type}>{type}</option>)}
            </select>
            <input
              type="number"
              value={squadForm.goal_target}
              onChange={(e) => setSquadForm((prev) => ({ ...prev, goal_target: e.target.value }))}
              placeholder="Goal target"
            />
            <input
              type="datetime-local"
              value={squadForm.goal_deadline}
              onChange={(e) => setSquadForm((prev) => ({ ...prev, goal_deadline: e.target.value }))}
            />
          </div>
          <div className="member-selector">
            {friendOptions.length === 0 && <p className="friends-muted">Add friends to build a squad.</p>}
            {friendOptions.map((id) => (
              <label key={id}>
                <input
                  type="checkbox"
                  checked={squadForm.member_ids.includes(id)}
                  onChange={() => toggleSelection('member_ids', id, setSquadForm)}
                />
                {id}
              </label>
            ))}
          </div>
          <button onClick={createSquad}>Create squad</button>
          <div className="list-stack">
            {squads.map((squad) => (
              <div key={squad.squad_id} className="mini-card">
                <strong>{squad.name}</strong>
                <p>{squad.goal?.title} ({squad.goal?.type}: {squad.goal?.target})</p>
                <small>Members: {(squad.members || []).map((m) => m.name).join(', ')}</small>
              </div>
            ))}
          </div>
        </section>
      </div>

      <section className="friends-card nudges-card">
        <div className="card-head">
          <h3>Nudges</h3>
          <p className="friends-muted">Quick reminders from your network.</p>
        </div>
        {nudges.length === 0 && <p className="friends-muted">No nudges yet.</p>}
        {nudges.map((nudge) => (
          <div key={nudge.nudge_id} className={`nudge-row ${nudge.read ? 'read' : 'unread'}`}>
            <div>
              <strong>{nudge.from_user?.name}</strong>
              <p>{nudge.message}</p>
            </div>
            {!nudge.read && <button onClick={() => markNudgeRead(nudge.nudge_id)}>Mark read</button>}
          </div>
        ))}
      </section>
    </div>
  );
}

export default Friends;
