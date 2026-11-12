import React from 'react';

export default function FamilyMembersDropdown({ members = [], currentUserId, userRole, onUpdateRole, onDeleteMember }) {
  if (!members.length) return <p className="empty-state compact">Поки що немає учасників родини.</p>;
  return (
    <div className="members-list">
      {members.map(member => {
        const isMe = String(member.id) === String(currentUserId);
        return (
          <div className="member-row" key={member.id}>
            <div className="member-avatar">{(member.username || '?').slice(0, 1).toUpperCase()}</div>
            <div className="member-info">
              <strong>{member.username}{isMe ? ' (ви)' : ''}</strong>
              <span>{member.email}</span>
            </div>
            {userRole === 'head' && !isMe ? (
              <div className="member-actions">
                <select aria-label={`Роль ${member.username}`} value={member.role} onChange={e => onUpdateRole(member, e.target.value, false)}>
                  <option value="member">Учасник</option>
                  <option value="head">Голова</option>
                </select>
                <button className="icon-button danger-text" title="Видалити учасника" onClick={() => onDeleteMember(member)}>×</button>
              </div>
            ) : <span className={`role-pill ${member.role}`}>{member.role === 'head' ? 'Голова' : member.role === 'admin' ? 'Адмін' : 'Учасник'}</span>}
          </div>
        );
      })}
    </div>
  );
}