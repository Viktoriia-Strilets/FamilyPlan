import React, { useState } from 'react';
import ProfileDropdown from '../Profile/ProfileDropdown';

const tabs = [
  { id: 'budget', icon: '↗', label: 'Бюджет' },
  { id: 'shopping', icon: '▣', label: 'Покупки' },
  { id: 'analytics', icon: '▥', label: 'Аналітика' },
];

export default function Navbar(props) {
  const [showDropdown, setShowDropdown] = useState(false);
  const { user, activeTab, setActiveTab, familyMembers } = props;
  return (
    <header className="topbar">
      <div className="topbar-inner">
        <a className="brand" href="/" aria-label="FamilyPlan">
          <span className="brand-icon">⌂</span>
          <span>Family<span className="brand-accent">Plan</span></span>
        </a>
        {user.role !== 'admin' && (
          <nav className="main-nav">
            {tabs.map(tab => (
              <button key={tab.id} className={`nav-link ${activeTab === tab.id ? 'active' : ''}`} onClick={() => setActiveTab(tab.id)}>
                <span className="nav-icon">{tab.icon}</span>{tab.label}
              </button>
            ))}
          </nav>
        )}
        <div className="topbar-profile">
          <button className="profile-trigger" onClick={() => setShowDropdown(v => !v)} aria-expanded={showDropdown}>
            <span className="avatar">{(user.username || 'U').slice(0, 1).toUpperCase()}</span>
            <span className="profile-trigger-text"><strong>{user.username}</strong><small>{user.role === 'admin' ? 'Адміністратор' : user.role === 'head' ? 'Голова родини' : 'Учасник родини'}</small></span>
            <span className="chevron">⌄</span>
          </button>
          {showDropdown && <ProfileDropdown {...props} onClose={() => setShowDropdown(false)} />}
        </div>
      </div>
    </header>
  );
}