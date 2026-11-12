import React, { useState } from 'react';
import { getGoogleLoginUrl } from '../../api/authService';

export default function AuthPage({ onLogin, onRegister,  googleRegistrationToken, oauthError, onGoogleRegister, }) {
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [username, setUsername] = useState('');
  const [inviteCode, setInviteCode] = useState('');
  const [familyName, setFamilyName] = useState('');
  const [createFamily, setCreateFamily] = useState(false);
  const [googleInvite, setGoogleInvite] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const [googlePassword, setGooglePassword] = useState('');
  const [googleConfirmPassword, setGoogleConfirmPassword] = useState('');
  const [googleUsername, setGoogleUsername] = useState('');
  const [googleCreateFamily, setGoogleCreateFamily] = useState(false);
  const [googleFamilyName, setGoogleFamilyName] = useState('');
  const [googleInviteCode, setGoogleInviteCode] = useState('');4

  const submit = async (event) => {
    event.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);
    try {
      if (mode === 'login') {
        await onLogin({ email, password });
      } else {
        await onRegister({
          username,
          email,
          password,
          invite_code: createFamily ? null : inviteCode.trim(),
          family_name: createFamily ? familyName.trim() : null,
          create_family: createFamily
        });
        setSuccess('Реєстрація успішна. Тепер увійдіть у систему.');
        setMode('login');
        setPassword('');
      }
    } catch (err) {
      setError(err.message || 'Не вдалося виконати запит.');
    } finally {
      setLoading(false);
    }
  };
  const submitGoogleRegistration = async (event) => {
    event.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (googlePassword !== googleConfirmPassword) {
        throw new Error('Паролі не збігаються.');
      }

      if (googlePassword.length < 6) {
        throw new Error('Пароль має містити щонайменше 6 символів.');
      }

      if (googleCreateFamily && !googleFamilyName.trim()) {
        throw new Error('Введіть назву родини.');
      }

      if (!googleCreateFamily && !googleInviteCode.trim()) {
        throw new Error('Введіть код запрошення родини.');
      }

      await onGoogleRegister({
        password: googlePassword,
        username: googleUsername,
        create_family: googleCreateFamily,
        family_name: googleFamilyName,
        invite_code: googleInviteCode,
      });
    } catch (err) {
      setError(err.message || 'Не вдалося завершити реєстрацію.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="auth-page">
      <section className="auth-card">
        <div className="brand-mark">⌂</div>
        <div className="eyebrow">СІМЕЙНИЙ ПРОСТІР</div>
        <h1>FamilyPlan</h1>
        <p className="auth-subtitle">Бюджет, покупки та плани — в одному місці</p>

        <div className="auth-tabs">
          <button type="button" className={mode === 'login' ? 'active' : ''} onClick={() => { setMode('login'); setError(''); setSuccess(''); }}>Увійти</button>
          <button type="button" className={mode === 'register' ? 'active' : ''} onClick={() => { setMode('register'); setError(''); setSuccess(''); }}>Реєстрація</button>
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}
        {googleRegistrationToken ? (
        <form
          className="form-stack"
          onSubmit={submitGoogleRegistration}
        >
          <h2>Завершення реєстрації через Google</h2>

          <p>
            Google успішно підтвердив ваш акаунт.
            Створіть пароль для входу у FamilyPlan.
          </p>

          <label>
            Ваше ім’я
            <input
              value={googleUsername}
              onChange={e => setGoogleUsername(e.target.value)}
              placeholder="Ваше ім’я"
            />
          </label>

          <label>
            Пароль FamilyPlan
            <input
              type="password"
              value={googlePassword}
              onChange={e => setGooglePassword(e.target.value)}
              minLength={6}
              autoComplete="new-password"
              required
            />
          </label>

          <label>
            Повторіть пароль
            <input
              type="password"
              value={googleConfirmPassword}
              onChange={e => setGoogleConfirmPassword(e.target.value)}
              minLength={6}
              autoComplete="new-password"
              required
            />
          </label>

          <label className="check-row">
            <input
              type="checkbox"
              checked={googleCreateFamily}
              onChange={e => setGoogleCreateFamily(e.target.checked)}
            />
            Створити нову родину
          </label>

          {googleCreateFamily ? (
            <label>
              Назва родини
              <input
                value={googleFamilyName}
                onChange={e => setGoogleFamilyName(e.target.value)}
                placeholder="Назва родини"
                required
              />
            </label>
          ) : (
            <label>
              Код запрошення
              <input
                value={googleInviteCode}
                onChange={e => setGoogleInviteCode(e.target.value)}
                placeholder="Код від голови родини"
                required
              />
            </label>
          )}

          <button
            className="button button-primary button-wide"
            type="submit"
            disabled={loading}
          >
            {loading ? 'Створення акаунта…' : 'Завершити реєстрацію'}
          </button>
        </form>
      ) : (

          <form className="form-stack" onSubmit={submit}>
            {mode === 'register' && (
              <>
                <label>Ваше ім’я<input value={username} onChange={e => setUsername(e.target.value)} placeholder="Наприклад, Олена" required /></label>
              </>
            )}
            <label>Електронна пошта<input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="name@example.com" autoComplete="email" required /></label>
            <label>Пароль<input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Введіть пароль" autoComplete={mode === 'login' ? 'current-password' : 'new-password'} required minLength={6} /></label>

            {mode === 'register' && (
              <>
                <label className="check-row"><input type="checkbox" checked={createFamily} onChange={e => setCreateFamily(e.target.checked)} /> Створити нову родину</label>
                {createFamily ? (
                  <label>Назва родини<input value={familyName} onChange={e => setFamilyName(e.target.value)} placeholder="Родина Іваненків" required /></label>
                ) : (
                  <label>Код запрошення<input value={inviteCode} onChange={e => setInviteCode(e.target.value)} placeholder="Код від голови родини" required /></label>
                )}
              </>
            )}
            <button className="button button-primary button-wide" type="submit" disabled={loading}>
              {loading ? 'Зачекайте…' : mode === 'login' ? 'Увійти до FamilyPlan' : 'Створити обліковий запис'}
            </button>
          </form>
      )}

        <div className="separator"><span>або</span></div>
        <label className="google-invite-label">Код запрошення для нової Google-реєстрації (необов’язково)
          <input value={googleInvite} onChange={e => setGoogleInvite(e.target.value)} placeholder="Код родини" />
        </label>
        <a
          className="button button-google button-wide"
          href={getGoogleLoginUrl()}
        >
          <span className="google-g">G</span>
          Продовжити з Google
        </a>
        {oauthError && (
          <div className="alert alert-error">
            {oauthError}
          </div>
        )}
        <p className="auth-footnote">Якщо акаунт уже існує, просто увійдіть звичайним способом або через Google.</p>
      </section>
    </main>
  );
}