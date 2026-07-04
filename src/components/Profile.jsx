import React, { useEffect, useMemo, useState } from 'react';
import { api } from '../utils/api';
import Notification from './Notification';
import './Profile.css';

const STATUS_OPTIONS = ['online', 'studying', 'challenge', 'offline'];
const STATUS_LABELS = {
  online: 'Online',
  studying: 'Studying',
  challenge: 'In Challenge',
  offline: 'Offline'
};

function Profile() {
  const [profile, setProfile] = useState(null);
  const [form, setForm] = useState({
    username: '',
    display_name: '',
    avatar_url: '',
    banner_url: '',
    bio: '',
    country: '',
    timezone: '',
    title: '',
    privacy: { activity: 'friends' }
  });
  const [showcaseSelection, setShowcaseSelection] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [notification, setNotification] = useState({ message: '', type: 'info' });

  const loadProfile = async () => {
    setLoading(true);
    try {
      const data = await api.getMyProfile();
      setProfile(data);
      setForm({
        username: data.username || '',
        display_name: data.display_name || '',
        avatar_url: data.avatar_url || '',
        banner_url: data.banner_url || '',
        bio: data.bio || '',
        country: data.country || '',
        timezone: data.timezone || '',
        title: data.title || '',
        privacy: data.privacy || { activity: 'friends' }
      });
      setShowcaseSelection(data.showcase_badges || []);
    } catch (error) {
      setNotification({ message: error.message || 'Failed to load profile', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProfile();
  }, []);

  const unlockedBadges = useMemo(
    () => (profile?.badges || []).filter((badge) => !badge.is_locked),
    [profile]
  );

  const xpPercent = useMemo(() => {
    const xp = profile?.progress?.xp || 0;
    return ((xp % 100) + 100) % 100;
  }, [profile]);

  const handleFieldChange = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handlePrivacyChange = (value) => {
    setForm((prev) => ({ ...prev, privacy: { ...prev.privacy, activity: value } }));
  };

  const handleSaveProfile = async () => {
    setSaving(true);
    try {
      const updated = await api.updateMyProfile(form);
      setProfile(updated);
      setNotification({ message: 'Profile updated', type: 'success' });
    } catch (error) {
      setNotification({ message: error.message || 'Failed to update profile', type: 'error' });
    } finally {
      setSaving(false);
    }
  };

  const handleStatusChange = async (newStatus) => {
    try {
      await api.updateProfileStatus(newStatus);
      setProfile((prev) => (prev ? { ...prev, status: newStatus } : prev));
    } catch (error) {
      setNotification({ message: error.message || 'Failed to update status', type: 'error' });
    }
  };

  const toggleShowcaseBadge = (badgeId) => {
    setShowcaseSelection((prev) => {
      if (prev.includes(badgeId)) {
        return prev.filter((item) => item !== badgeId);
      }
      if (prev.length >= 3) {
        return prev;
      }
      return [...prev, badgeId];
    });
  };

  const saveShowcase = async () => {
    try {
      const data = await api.updateProfileShowcase(showcaseSelection);
      setProfile((prev) => (prev ? { ...prev, showcase_badges: data.showcase_badges || [] } : prev));
      setNotification({ message: 'Showcase updated', type: 'success' });
    } catch (error) {
      setNotification({ message: error.message || 'Failed to save showcase', type: 'error' });
    }
  };

  if (loading) {
    return (
      <div className="profile-container">
        <section className="profile-card">
          <h2 className="profile-title">Loading profile...</h2>
        </section>
      </div>
    );
  }

  return (
    <div className="profile-container">
      <Notification message={notification.message} type={notification.type} />
      <header className="profile-heading">
        <div>
          <h1 className="profile-title">Profile</h1>
          <p className="profile-subtitle">Manage identity, privacy, and social progress.</p>
        </div>
        <span className={`profile-status-chip status-${profile?.status || 'offline'}`}>
          {STATUS_LABELS[profile?.status] || STATUS_LABELS.offline}
        </span>
      </header>

      <div className="profile-banner" style={{ backgroundImage: `url(${form.banner_url || ''})` }}>
        <div className="profile-overlay">
          <img
            src={form.avatar_url || 'https://placehold.co/120x120?text=Avatar'}
            alt="avatar"
            className="profile-avatar"
          />
          <div className="profile-identity">
            <h2>{profile?.display_name || profile?.name}</h2>
            <p>@{profile?.username}</p>
            {form.title && <span className="profile-role-pill">{form.title}</span>}
          </div>
        </div>
      </div>

      <div className="profile-grid">
        <section className="profile-card">
          <div className="card-head">
            <h3>Identity</h3>
            <p>Public details and account visibility.</p>
          </div>
          <div className="profile-form-grid">
            <label>
              <span>Username</span>
              <input value={form.username} onChange={(e) => handleFieldChange('username', e.target.value)} placeholder="username" />
            </label>
            <label>
              <span>Display name</span>
              <input value={form.display_name} onChange={(e) => handleFieldChange('display_name', e.target.value)} placeholder="display name" />
            </label>
            <label>
              <span>Title</span>
              <input value={form.title} onChange={(e) => handleFieldChange('title', e.target.value)} placeholder="title" />
            </label>
            <label>
              <span>Country</span>
              <input value={form.country} onChange={(e) => handleFieldChange('country', e.target.value)} placeholder="country" />
            </label>
            <label>
              <span>Timezone</span>
              <input value={form.timezone} onChange={(e) => handleFieldChange('timezone', e.target.value)} placeholder="timezone" />
            </label>
            <label>
              <span>Activity privacy</span>
              <select value={form.privacy?.activity || 'friends'} onChange={(e) => handlePrivacyChange(e.target.value)}>
                <option value="public">Public activity</option>
                <option value="friends">Friends-only activity</option>
                <option value="private">Private activity</option>
              </select>
            </label>
            <label>
              <span>Avatar URL</span>
              <input value={form.avatar_url} onChange={(e) => handleFieldChange('avatar_url', e.target.value)} placeholder="avatar URL" />
            </label>
            <label>
              <span>Banner URL</span>
              <input value={form.banner_url} onChange={(e) => handleFieldChange('banner_url', e.target.value)} placeholder="banner URL" />
            </label>
          </div>
          <label className="profile-textarea-label">
            <span>Bio</span>
            <textarea value={form.bio} onChange={(e) => handleFieldChange('bio', e.target.value)} placeholder="bio" rows={4} maxLength={300} />
          </label>
          <div className="profile-form-footer">
            <p className="profile-hint">{form.bio.length}/300 characters</p>
            <button className="profile-save-btn" onClick={handleSaveProfile} disabled={saving}>
              {saving ? 'Saving...' : 'Save profile'}
            </button>
          </div>
        </section>

        <section className="profile-card">
          <div className="card-head">
            <h3>Progress</h3>
            <p>Current performance snapshot.</p>
          </div>
          <div className="profile-kpis">
            <article className="kpi-card"><span>Level</span><strong>{profile?.progress?.level || 1}</strong></article>
            <article className="kpi-card"><span>XP</span><strong>{profile?.progress?.xp || 0}</strong></article>
            <article className="kpi-card"><span>Sessions</span><strong>{profile?.progress?.sessions || 0}</strong></article>
            <article className="kpi-card"><span>Solved</span><strong>{profile?.progress?.solved_items || 0}</strong></article>
            <article className="kpi-card"><span>Wins</span><strong>{profile?.progress?.wins || 0}</strong></article>
            <article className="kpi-card"><span>Streak</span><strong>{profile?.streak?.current || 0}</strong></article>
          </div>
          <div className="xp-track">
            <div className="xp-fill" style={{ width: `${xpPercent}%` }} />
          </div>
          <p className="profile-hint">{profile?.progress?.to_next_level || 0} XP to next level</p>

          <h4 className="status-heading">Status</h4>
          <div className="status-list">
            {STATUS_OPTIONS.map((status) => (
              <button
                key={status}
                className={`status-pill ${profile?.status === status ? 'active' : ''}`}
                onClick={() => handleStatusChange(status)}
              >
                {STATUS_LABELS[status]}
              </button>
            ))}
          </div>
        </section>
      </div>

      <div className="profile-grid">
        <section className="profile-card">
          <div className="card-head">
            <h3>Badges</h3>
            <p>Milestones and achievements unlocked.</p>
          </div>
          <div className="badge-grid">
            {(profile?.badges || []).map((badge) => (
              <div key={badge.id} className={`badge-card ${badge.is_locked ? 'locked' : 'unlocked'}`}>
                <strong>{badge.name}</strong>
                <p>{badge.description}</p>
                <small>{badge.is_locked ? 'Locked' : (badge.earned_at ? `Unlocked ${new Date(badge.earned_at).toLocaleDateString()}` : 'Unlocked')}</small>
              </div>
            ))}
          </div>
        </section>

        <section className="profile-card">
          <div className="card-head">
            <h3>Showcase</h3>
            <p>Pick up to three badges to highlight on your profile.</p>
          </div>
          <div className="showcase-grid">
            {unlockedBadges.length === 0 && <p className="profile-hint">Unlock badges to pin them here.</p>}
            {unlockedBadges.map((badge) => (
              <label
                key={badge.id}
                className={`showcase-item ${showcaseSelection.includes(badge.id) ? 'selected' : ''}`}
              >
                <input
                  type="checkbox"
                  checked={showcaseSelection.includes(badge.id)}
                  onChange={() => toggleShowcaseBadge(badge.id)}
                  disabled={!showcaseSelection.includes(badge.id) && showcaseSelection.length >= 3}
                />
                <span>{badge.name}</span>
              </label>
            ))}
          </div>
          <button className="profile-save-btn" onClick={saveShowcase}>Save showcase</button>
        </section>
      </div>

      <section className="profile-card activity-card">
        <div className="card-head">
          <h3>Activity Feed</h3>
          <p>Recent profile and gameplay updates.</p>
        </div>
        {(profile?.activity_feed || []).length === 0 && <p className="profile-hint">No activity yet.</p>}
        <ul className="activity-list">
          {(profile?.activity_feed || []).map((item) => (
            <li key={item.activity_id}>
              <div>
                <strong>{item.type}</strong>
                <p>{item.message}</p>
              </div>
              <small>{item.created_at ? new Date(item.created_at).toLocaleString() : ''}</small>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

export default Profile;
