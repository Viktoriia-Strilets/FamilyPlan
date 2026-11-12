import React, { useEffect, useMemo, useState } from 'react';
import {
  getShoppingItems, createShoppingItem, updateShoppingItem,
  markItemAsPurchased, deleteShoppingItem, getPurchaseHistory,
  getShoppingRecommendations, getShoppingReminders,
} from '../../api/shoppingService';

const money = value => value == null ? '—' : `${Number(value).toLocaleString('uk-UA')} ₴`;
const categories = ['Продукти','Побутова хімія','Дім','Здоров’я','Одяг','Техніка','Інше'];

export default function ShoppingList() {
  const [items, setItems] = useState([]);
  const [history, setHistory] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [reminders, setReminders] = useState([]);
  const [tab, setTab] = useState('active');
  const [filter, setFilter] = useState('Усі');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [editing, setEditing] = useState(null);
  const [actualPrices, setActualPrices] = useState({});
  const [form, setForm] = useState({ name: '', quantity: 1, category: 'Продукти', estimated_price: '', planned_date: '' });

  const load = async () => {
    setLoading(true); setError('');
    try {
      const [list, purchased, tips, alerts] = await Promise.all([
        getShoppingItems(), getPurchaseHistory(), getShoppingRecommendations(), getShoppingReminders(),
      ]);
      setItems(Array.isArray(list) ? list : []);
      setHistory(Array.isArray(purchased) ? purchased : []);
      setRecommendations(Array.isArray(tips) ? tips : []);
      setReminders(Array.isArray(alerts) ? alerts : []);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);

  const activeItems = useMemo(() => items.filter(i => !i.is_purchased), [items]);
  const filteredItems = activeItems.filter(i => filter === 'Усі' || (i.category || 'Інше') === filter);

  const submit = async e => {
    e.preventDefault(); setBusy(true); setError('');
    const payload = {
      name: form.name.trim(), quantity: Number(form.quantity),
      category: form.category,
      estimated_price: form.estimated_price === '' ? null : Number(form.estimated_price),
      planned_date: form.planned_date ? new Date(`${form.planned_date}T12:00:00`).toISOString() : null,
    };
    try {
      if (editing) await updateShoppingItem(editing.id, payload);
      else await createShoppingItem(payload);
      setForm({ name: '', quantity: 1, category: 'Продукти', estimated_price: '', planned_date: '' });
      setEditing(null);
      await load();
    } catch (e) { setError(e.message); }
    finally { setBusy(false); }
  };

  const beginEdit = item => {
    setEditing(item);
    setForm({
      name: item.name, quantity: item.quantity, category: item.category || 'Інше',
      estimated_price: item.estimated_price ?? '',
      planned_date: item.planned_date ? String(item.planned_date).slice(0, 10) : '',
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const buy = async item => {
    const price = actualPrices[item.id];

    if (
      price === undefined ||
      price === '' ||
      !Number.isFinite(Number(price)) ||
      Number(price) <= 0
    ) {
      setError(`Вкажіть фактичну ціну для товару «${item.name}».`);
      return;
    }

    setBusy(true);
    setError('');

    try {
      await markItemAsPurchased(item.id, price);
      setActualPrices(prev => {
        const updated = { ...prev };
        delete updated[item.id];
        return updated;
      });
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <div className="panel"><div className="skeleton-line" /><div className="skeleton-block" /></div>;

  return (
    <section className="page-section">
      <div className="page-heading"><div><span className="eyebrow">ПОКУПКИ РОДИНИ</span><h1>Список покупок</h1><p>Збирайте потреби родини та відстежуйте фактичну вартість.</p></div><span className="heading-icon">▣</span></div>
      {error && <div className="alert alert-error">{error}</div>}
      {reminders.length > 0 && <div className="reminder-stack">{reminders.map((r, i) => <div key={`${r.item_id}-${i}`} className={`alert ${r.level === 'danger' ? 'alert-error' : 'alert-warning'}`}>{r.text}</div>)}</div>}

      <div className="shopping-summary">
        <div><span>Активні покупки</span><strong>{activeItems.length}</strong></div>
        <div><span>Уже придбано</span><strong>{history.length}</strong></div>
        <div><span>Орієнтовна сума</span><strong>{money(activeItems.reduce((sum, i) => sum + Number(i.estimated_price || 0) * Number(i.quantity || 1), 0))}</strong></div>
      </div>

      <div className="content-grid shopping-grid">
        <section className="panel">
          <div className="panel-heading"><div><h2>{editing ? 'Редагувати товар' : 'Додати до списку'}</h2><p>Заповніть основну інформацію про покупку.</p></div><span className="panel-icon">＋</span></div>
          <form className="form-stack" onSubmit={submit}>
            <label>Назва товару<input value={form.name} onChange={e => setForm(v => ({ ...v, name: e.target.value }))} placeholder="Наприклад, молоко" required maxLength={200} /></label>
            <div className="form-two-columns">
              <label>Кількість<input type="number" min="1" step="1" value={form.quantity} onChange={e => setForm(v => ({ ...v, quantity: e.target.value }))} required /></label>
              <label>Орієнтовна ціна за одиницю<input type="number" min="0" step="0.01" value={form.estimated_price} onChange={e => setForm(v => ({ ...v, estimated_price: e.target.value }))} placeholder="0.00" /></label>
            </div>
            <div className="form-two-columns">
              <label>Категорія<select value={form.category} onChange={e => setForm(v => ({ ...v, category: e.target.value }))}>{categories.map(c => <option key={c}>{c}</option>)}</select></label>
              <label>Дата покупки<input type="date" value={form.planned_date} onChange={e => setForm(v => ({ ...v, planned_date: e.target.value }))} /></label>
            </div>
            <div className="form-actions"><button className="button button-primary" disabled={busy}>{busy ? 'Збереження…' : editing ? 'Зберегти зміни' : 'Додати товар'}</button>{editing && <button type="button" className="button button-secondary" onClick={() => { setEditing(null); setForm({ name: '', quantity: 1, category: 'Продукти', estimated_price: '', planned_date: '' }); }}>Скасувати</button>}</div>
          </form>
        </section>
        <section className="panel">
          <div className="panel-heading"><div><h2>Рекомендації</h2><p>На основі повторних покупок родини.</p></div><span className="panel-icon">✦</span></div>
          <div className="recommendation-list">{recommendations.map((r, i) => <div className="recommendation-item" key={i}><span className="recommendation-dot">✦</span><div><strong>{r.title}</strong><p>{r.description}</p><button className="text-button" onClick={() => setForm(v => ({ ...v, name: r.suggested_name || '', category: r.category || 'Інше' }))}>Додати до форми ↗</button></div></div>)}</div>
        </section>
      </div>

      <section className="panel">
        <div className="panel-heading"><div><h2>Ваш список</h2><p>Активні товари та історія придбань.</p></div><span className="count-pill">{tab === 'active' ? activeItems.length : history.length}</span></div>
        <div className="list-toolbar">
          <div className="segmented-tabs"><button className={tab === 'active' ? 'active' : ''} onClick={() => setTab('active')}>До покупки</button><button className={tab === 'history' ? 'active' : ''} onClick={() => setTab('history')}>Історія</button></div>
          {tab === 'active' && <select value={filter} onChange={e => setFilter(e.target.value)}><option>Усі</option>{categories.map(c => <option key={c}>{c}</option>)}</select>}
        </div>
        {(tab === 'active' ? filteredItems : history).length === 0 ? <div className="empty-state">{tab === 'active' ? 'Список порожній. Додайте першу покупку вище.' : 'Історія покупок поки порожня.'}</div> : (
          <div className="shopping-items">
            {(tab === 'active' ? filteredItems : history).map(item => <article className={`shopping-item ${item.is_purchased ? 'purchased' : ''}`} key={item.id}>
              <div className="shopping-item-main"><span className="item-check">{item.is_purchased ? '✓' : '·'}</span><div><strong>{item.name}</strong><div className="item-meta"><span>{item.category || 'Інше'}</span><span>Кількість: {item.quantity}</span>{item.planned_date && <span>До {new Date(item.planned_date).toLocaleDateString('uk-UA')}</span>}</div></div></div>
              <div className="shopping-item-price">
                <strong>
                  {money(
                    item.actual_price ??
                    (
                      item.estimated_price != null
                        ? Number(item.estimated_price) * Number(item.quantity || 1)
                        : null
                    )
                  )}
                </strong>

                <small>
                  {item.actual_price != null
                    ? 'Фактична сума покупки'
                    : 'Орієнтовна сума'}
                </small>
              </div>
              <div className="shopping-item-actions">
                {tab === 'active' ? <>
                  <input
                    aria-label={`Фактична ціна ${item.name}`}
                    className="actual-price-input"
                    type="number"
                    min="0.01"
                    step="0.01"
                    placeholder="Факт. сума"
                    value={actualPrices[item.id] ?? ''}
                    onChange={e =>
                      setActualPrices(v => ({
                        ...v,
                        [item.id]: e.target.value
                      }))
                    }
                  />
                  <button className="button button-success button-small" disabled={busy} onClick={() => buy(item)}>Придбано</button>
                  <button className="icon-button" title="Редагувати" onClick={() => beginEdit(item)}>✎</button>
                </> : <span className="status-pill done">Придбано</span>}
                <button className="icon-button danger-text" title="Видалити" onClick={async () => { if (window.confirm(`Видалити «${item.name}»?`)) { try { await deleteShoppingItem(item.id); await load(); } catch (e) { setError(e.message); } } }}>×</button>
              </div>
            </article>)}
          </div>
        )}
      </section>
    </section>
  );
}