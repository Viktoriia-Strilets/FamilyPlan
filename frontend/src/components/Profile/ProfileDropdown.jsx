import React, { useState } from 'react';
import FamilyMembersDropdown from './FamilyMembersDropdown';
import { changePassword } from '../../api/userService';

export default function ProfileDropdown({
  user, familyMembers = [], onLogout, onProfileUpdated, onFamilyNameUpdated,
  onUserAdded, onUpdateRole, onDeleteMember,   onDeleteAccount,
  onDeleteFamily, onLinkGoogle, onClose,
}) {
  const [username, setUsername] = useState(user.username || '');
  const [familyName, setFamilyName] = useState(user.familyName || '');
  const [showEdit, setShowEdit] = useState(false);
  const [showAdd, setShowAdd] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');

  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const run = async (callback, value, successMessage) => {
    setBusy(true);
    setMessage('');

    try {
      await callback(value);
      setMessage(successMessage);
      return true;
    } catch (error) {
      setMessage(error.message || 'Не вдалося виконати дію.');
      return false;
    } finally {
      setBusy(false);
    }
  };

  const submitProfile = async e => {
    e.preventDefault();
    await run(async () => {
      if (username.trim() && username.trim() !== user.username) await onProfileUpdated(username.trim());
      if (user.role === 'head' && familyName.trim() && familyName.trim() !== user.familyName) await onFamilyNameUpdated(familyName.trim());
    }, null, 'Профіль оновлено.');
  };

  const submitAdd = async e => {
    e.preventDefault();
    const form = e.currentTarget;
    await run(() => onUserAdded({
      username: form.elements.username.value,
      email: form.elements.email.value,
      password: form.elements.password.value,
    }), null, 'Учасника додано до родини.');
    if (!busy) form.reset();
  };
  const handleDeleteAccount = async () => {
    const confirmed = window.confirm(
      'Ви впевнені, що хочете видалити свій акаунт? Цю дію неможливо скасувати.'
    );

    if (!confirmed) return;

    await run(
      onDeleteAccount,
      null,
      'Акаунт видалено.'
    );
  };

  const handleDeleteFamily = async () => {
    const confirmed = window.confirm(
      'Увага! Ви хочете видалити всю родину та всіх її учасників. Продовжити?'
    );

    if (!confirmed) return;

    await run(
      onDeleteFamily,
      null,
      'Родину видалено.'
    );
  };

  const submitPassword = async (e) => {
    e.preventDefault();

    if (newPassword !== confirmPassword) {
      setMessage('Нові паролі не збігаються.');
      return;
    }

    if (newPassword.length < 6) {
      setMessage('Новий пароль має містити щонайменше 6 символів.');
      return;
    }

    const success = await run(
      () => changePassword({
        old_password: user.hasPassword ? oldPassword : null,
        new_password: newPassword,
      }),
      null,
      user.hasPassword
        ? 'Пароль успішно змінено.'
        : 'Пароль успішно встановлено.'
    );

    if (success) {
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setShowPasswordForm(false);
    }
  };

  return (
    <div className="profile-menu">
      <div className="profile-menu-head">
        <span className="avatar avatar-large">{(user.username || 'U').slice(0, 1).toUpperCase()}</span>
        <div><strong>{user.username}</strong><span>{user.role === 'admin' ? 'Адміністратор' : user.familyName || 'Моя родина'}</span></div>
        <button className="icon-button close-menu" onClick={onClose} aria-label="Закрити">×</button>
      </div>

      {message && <div className="inline-message">{message}</div>}
      <div className="profile-menu-section">
        <div className="section-heading"><strong>Мій профіль</strong><button className="text-button" onClick={() => setShowEdit(v => !v)}>{showEdit ? 'Скасувати' : 'Редагувати'}</button></div>
        {showEdit && (
          <form className="form-stack compact-form" onSubmit={submitProfile}>
            <label>Ім’я<input value={username} onChange={e => setUsername(e.target.value)} required /></label>
            {user.role === 'head' && <label>Назва родини<input value={familyName} onChange={e => setFamilyName(e.target.value)} required /></label>}
            <button className="button button-primary button-small" disabled={busy}>Зберегти</button>
          </form>
        )}
      </div>
      <div className="profile-menu-section">
      
      <div className="section-heading">
        <strong>Безпека</strong>
        <button
          type="button"
          className="text-button"
          onClick={() => setShowPasswordForm(v => !v)}
        >
          {showPasswordForm ? 'Скасувати' : 'Змінити пароль'}
        </button>
      </div>

      {showPasswordForm && (
        <form
          className="form-stack compact-form"
          onSubmit={submitPassword}
        >
          {user.hasPassword && (
            <label>
              Поточний пароль
              <input
                type="password"
                value={oldPassword}
                onChange={e => setOldPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
            </label>
          )}

          <label>
            Новий пароль
            <input
              type="password"
              value={newPassword}
              onChange={e => setNewPassword(e.target.value)}
              minLength={6}
              autoComplete="new-password"
              required
            />
          </label>

          <label>
            Повторіть новий пароль
            <input
              type="password"
              value={confirmPassword}
              onChange={e => setConfirmPassword(e.target.value)}
              minLength={6}
              autoComplete="new-password"
              required
            />
          </label>

          <button
            type="submit"
            className="button button-primary button-small"
            disabled={busy}
          >
            {busy
              ? 'Збереження...'
              : user.hasPassword
                ? 'Оновити пароль'
                : 'Встановити пароль'}
          </button>
        
          <div className="section-heading">
            <strong>Google</strong>
          </div>

          <button
            type="button"
            className="button button-google button-wide"
            disabled={busy}
            onClick={() => run(
              onLinkGoogle,
              null,
              'Google успішно прив’язано.'
            )}
          >
            <span className="google-g">G</span>
            Прив'язати Google
          </button>
        </form>  
      )}
</div>

      {user.role !== 'admin' && (
        <div className="profile-menu-section">
          <div className="section-heading"><strong>Учасники родини</strong><span className="count-pill">{familyMembers.length}</span></div>
          <FamilyMembersDropdown
            members={familyMembers}
            currentUserId={user.userId}
            userRole={user.role}
            onUpdateRole={(member, role, isMe) => run(() => onUpdateRole(member, role, isMe), null, 'Роль оновлено.')}
            onDeleteMember={member => { if (window.confirm(`Видалити учасника ${member.username}?`)) run(() => onDeleteMember(member), null, 'Учасника видалено.'); }}
          />
          {user.role === 'head' && (
            <>
              <button className="text-button add-member-toggle" onClick={() => setShowAdd(v => !v)}>{showAdd ? '− Сховати форму' : '+ Додати учасника'}</button>
              {showAdd && <form className="form-stack compact-form" onSubmit={submitAdd}>
                <label>Ім’я<input name="username" required /></label>
                <label>Email<input name="email" type="email" required /></label>
                <label>Тимчасовий пароль<input name="password" type="password" minLength="6" required /></label>
                <button className="button button-primary button-small" disabled={busy}>Додати</button>
              </form>}
              {user.inviteCode && <div className="invite-code"><span>Код запрошення</span><strong>{user.inviteCode}</strong><button className="text-button" onClick={() => navigator.clipboard?.writeText(user.inviteCode)}>Копіювати</button></div>}
            </>
          )}
        </div>
      )}
      {user.role !== 'admin' && (
        <div className="profile-menu-section danger-section">
          <div className="section-heading">
            <strong>Небезпечні дії</strong>
          </div>

          <div className="danger-actions">
            {user.role === 'head' && (
              <div className="danger-action-card">
                <div className="danger-action-icon">⌂</div>

                <div className="danger-action-info">
                  <strong>Видалити родину</strong>
                  <span>Видалити родину та всіх її учасників</span>
                </div>

                <button
                  type="button"
                  className="danger-action-button"
                  disabled={busy}
                  onClick={handleDeleteFamily}
                >
                  Видалити
                </button>
              </div>
            )}

            <div className="danger-action-card">
              <div className="danger-action-icon">♙</div>

              <div className="danger-action-info">
                <strong>Видалити мій акаунт</strong>
                <span>Назавжди видалити свій обліковий запис</span>
              </div>

              <button
                type="button"
                className="danger-action-button"
                disabled={busy}
                onClick={handleDeleteAccount}
              >
                Видалити
              </button>
            </div>
          </div>
        </div>
      )}
      <button className="logout-button" onClick={() => { onClose?.(); onLogout(); }}>Вийти з акаунта <span>↗</span></button>
    </div>
  );
}