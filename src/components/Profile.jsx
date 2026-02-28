import React, { useEffect, useMemo, useState } from 'react';
import { api } from '../utils/api';
import Notification from './Notification';
import './Profile.css';

const STATUS_OPTIONS = ['online', 'studying', 'challenge', 'offline'];

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
    return xp % 100;
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
    return <div className="profile-container"><h2 className="profile-title">Loading profile...</h2></div>;
  }

  return (
    <div className="profile-container">
      <Notification message={notification.message} type={notification.type} />
      <h1 className="profile-title">Profile</h1>

      <div className="profile-banner" style={{ backgroundImage: `url(${form.banner_url || ''})` }}>
        <div className="profile-overlay">
          <img
            src={form.avatar_url || 'https://placehold.co/120x120?text=Avatar'}
            alt="avatar"
            className="profile-avatar"
          />
          <div>
            <h2>{profile?.display_name || profile?.name}</h2>
            <p>@{profile?.username}</p>
          </div>
        </div>
      </div>

      <div className="profile-grid">
        <section className="profile-card">
          <h3>Identity</h3>
          <div className="profile-form-grid">
            <input value={form.username} onChange={(e) => handleFieldChange('username', e.target.value)} placeholder="username" />
            <input value={form.display_name} onChange={(e) => handleFieldChange('display_name', e.target.value)} placeholder="display name" />
            <input value={form.title} onChange={(e) => handleFieldChange('title', e.target.value)} placeholder="title" />
            <input value={form.country} onChange={(e) => handleFieldChange('country', e.target.value)} placeholder="country" />
            <input value={form.timezone} onChange={(e) => handleFieldChange('timezone', e.target.value)} placeholder="timezone" />
            <select value={form.privacy?.activity || 'friends'} onChange={(e) => handlePrivacyChange(e.target.value)}>
              <option value="public">Public activity</option>
              <option value="friends">Friends-only activity</option>
              <option value="private">Private activity</option>
            </select>
            <input value={form.avatar_url} onChange={(e) => handleFieldChange('avatar_url', e.target.value)} placeholder="avatar URL" />
            <input value={form.banner_url} onChange={(e) => handleFieldChange('banner_url', e.target.value)} placeholder="banner URL" />
          </div>
          <textarea value={form.bio} onChange={(e) => handleFieldChange('bio', e.target.value)} placeholder="bio" rows={4} />
          <button className="profile-save-btn" onClick={handleSaveProfile} disabled={saving}>
            {saving ? 'Saving...' : 'Save profile'}
          </button>
        </section>

        <section className="profile-card">
          <h3>Progress</h3>
          <div className="profile-kpis">
            <div><span>Level</span><strong>{profile?.progress?.level || 1}</strong></div>
            <div><span>XP</span><strong>{profile?.progress?.xp || 0}</strong></div>
            <div><span>Sessions</span><strong>{profile?.progress?.sessions || 0}</strong></div>
            <div><span>Solved</span><strong>{profile?.progress?.solved_items || 0}</strong></div>
            <div><span>Wins</span><strong>{profile?.progress?.wins || 0}</strong></div>
            <div><span>Streak</span><strong>{profile?.streak?.current || 0}</strong></div>
          </div>
          <div className="xp-track">
            <div className="xp-fill" style={{ width: `${xpPercent}%` }} />
          </div>
          <p className="profile-hint">{profile?.progress?.to_next_level || 0} XP to next level</p>

          <h4>Status</h4>
          <div className="status-list">
            {STATUS_OPTIONS.map((status) => (
              <button
                key={status}
                className={`status-pill ${profile?.status === status ? 'active' : ''}`}
                onClick={() => handleStatusChange(status)}
              >
                {status}
              </button>
            ))}
          </div>
        </section>
      </div>

      <div className="profile-grid">
        <section className="profile-card">
          <h3>Badges</h3>
          <div className="badge-grid">
            {(profile?.badges || []).map((badge) => (
              <div key={badge.id} className={`badge-card ${badge.is_locked ? 'locked' : 'unlocked'}`}>
                <strong>{badge.name}</strong>
                <p>{badge.description}</p>
                <small>{badge.is_locked ? 'Locked' : `Unlocked ${badge.earned_at ? '' : ''}`}</small>
              </div>
            ))}
          </div>
        </section>

        <section className="profile-card">
          <h3>Showcase (pick 3)</h3>
          <div className="showcase-grid">
            {unlockedBadges.length === 0 && <p className="profile-hint">Unlock badges to pin them here.</p>}
            {unlockedBadges.map((badge) => (
              <label key={badge.id} className="showcase-item">
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
        <h3>Activity Feed</h3>
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
