import React, { useEffect, useState } from 'react';
import { getAdminFamilies, deleteAdminFamily } from '../../api/userService';

export default function AdminDashboard() {
  const [families, setFamilies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busyId, setBusyId] = useState(null);

  const load = async () => {
    setLoading(true); setError('');
    try {
      const data = await getAdminFamilies();
      setFamilies(Array.isArray(data) ? data : []);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  const remove = async family => {
    if (!family.can_be_deleted) {
      setError('Цю родину не можна видалити: вона не відповідає критеріям неактивності.');
      return;
    }
    if (!window.confirm(`Видалити родину «${family.name}» та всіх її учасників?`)) return;
    setBusyId(family.id); setError('');
    try { await deleteAdminFamily(family.id); await load(); }
    catch (e) { setError(e.message); }
    finally { setBusyId(null); }
  };

  return (
    <section className="page-section">
      <div className="page-heading"><div><span className="eyebrow">КЕРУВАННЯ СИСТЕМОЮ</span><h1>Адміністративна панель</h1><p>Огляд родин, активності та доступності видалення.</p></div><span className="heading-icon">⚙</span></div>
      {error && <div className="alert alert-error">{error}</div>}
      <div className="stats-grid">
        <article className="stat-card"><span>Усього родин</span><strong>{families.length}</strong><small>Зареєстровані в системі</small></article>
        <article className="stat-card"><span>Неактивні</span><strong>{families.filter(f => f.is_inactive).length}</strong><small>Без активності понад 6 місяців</small></article>
        <article className="stat-card"><span>Можна видалити</span><strong>{families.filter(f => f.can_be_deleted).length}</strong><small>За критеріями системи</small></article>
      </div>
      <section className="panel">
        <div className="panel-heading"><div><h2>Родини</h2><p>Системний список сімейних просторів.</p></div><button className="button button-secondary button-small" onClick={load}>Оновити</button></div>
        {loading ? <div className="skeleton-block" /> : !families.length ? <p className="empty-state">Родин поки немає.</p> : <div className="table-wrap"><table className="data-table"><thead><tr><th>Родина</th><th>Учасники</th><th>Голова</th><th>Остання активність</th><th>Статус</th><th /></tr></thead><tbody>{families.map(f => <tr key={f.id}><td><strong>{f.name}</strong><small className="table-subtitle">ID: {f.id}</small></td><td>{f.members_count}</td><td>{(f.head_emails || [f.head_email]).filter(Boolean).join(', ') || '—'}</td><td>{f.last_activity_at ? new Date(f.last_activity_at).toLocaleDateString('uk-UA') : '—'}</td><td><span className={`status-pill ${f.is_inactive ? 'planned' : 'done'}`}>{f.is_inactive ? 'Неактивна' : 'Активна'}</span></td><td><button className="button button-danger button-small" disabled={!f.can_be_deleted || busyId === f.id} onClick={() => remove(f)}>{busyId === f.id ? 'Видалення…' : 'Видалити'}</button></td></tr>)}</tbody></table></div>}
      </section>
    </section>
  );
}