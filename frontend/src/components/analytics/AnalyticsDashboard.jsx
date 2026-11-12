import React, { useEffect, useMemo, useState } from 'react';
import { getReports, createReport, deleteReport, getForecast, getCategoryStatistics } from '../../api/analyticsService';

const money = value => `${Number(value || 0).toLocaleString('uk-UA', { maximumFractionDigits: 2 })} ₴`;
const currentPeriod = new Date().toISOString().slice(0, 7);

export default function AnalyticsDashboard() {
  const [reports, setReports] = useState([]);
  const [forecast, setForecast] = useState(null);
  const [categories, setCategories] = useState([]);
  const [period, setPeriod] = useState(currentPeriod);
  const [form, setForm] = useState({ period: currentPeriod, total_spent: '', recommendations_text: '' });
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const load = async selectedPeriod => {
    setLoading(true); setError('');
    try {
      const [reportData, forecastData, categoryData] = await Promise.all([
        getReports(), getForecast(), getCategoryStatistics(selectedPeriod),
      ]);
      setReports(Array.isArray(reportData) ? reportData : []);
      setForecast(forecastData);
      setCategories(Array.isArray(categoryData) ? categoryData : []);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(period); }, []);
  useEffect(() => { getCategoryStatistics(period).then(data => setCategories(Array.isArray(data) ? data : [])).catch(e => setError(e.message)); }, [period]);

  const total = reports.reduce((sum, r) => sum + Number(r.total_spent || 0), 0);
  const average = reports.length ? total / reports.length : 0;
  const maxCategory = Math.max(...categories.map(c => Number(c.total_amount || 0)), 1);

  const submit = async e => {
    e.preventDefault(); setBusy(true); setError('');
    try {
      await createReport({
        period: form.period,
        total_spent: Number(form.total_spent),
        recommendations_text: form.recommendations_text || null,
      });
      setForm(v => ({ ...v, total_spent: '', recommendations_text: '' }));
      setPeriod(form.period);
      await load(form.period);
    } catch (e) { setError(e.message); }
    finally { setBusy(false); }
  };

  if (loading) return <div className="panel"><div className="skeleton-line" /><div className="skeleton-block" /></div>;

  return (
    <section className="page-section">
      <div className="page-heading"><div><span className="eyebrow">ФІНАНСОВА КАРТИНА</span><h1>Аналітика та звіти</h1><p>Переглядайте динаміку витрат і плануйте наступний місяць.</p></div><span className="heading-icon">▥</span></div>
      {error && <div className="alert alert-error">{error}</div>}

      <div className="stats-grid analytics-stats">
        <article className="stat-card"><span>Кількість звітів</span><strong>{reports.length}</strong><small>Збережені періоди</small></article>
        <article className="stat-card"><span>Загальні витрати</span><strong>{money(total)}</strong><small>За всіма звітами</small></article>
        <article className="stat-card"><span>Середні витрати</span><strong>{money(average)}</strong><small>На один звітний період</small></article>
        <article className="stat-card accent-stat"><span>Прогноз на місяць</span><strong>{forecast ? money(forecast.predicted_amount) : '—'}</strong><small>{forecast?.period || 'Недоступно'}</small></article>
      </div>

      <div className="content-grid">
        <section className="panel">
          <div className="panel-heading"><div><h2>Прогноз витрат</h2><p>Оцінка на основі збережених звітів.</p></div><span className="panel-icon">↗</span></div>
          {forecast ? <div className="forecast-highlight"><strong>{money(forecast.predicted_amount)}</strong><p>{forecast.basis_description}</p></div> : <p className="empty-state">Немає даних для прогнозу.</p>}
        </section>
        <section className="panel">
          <div className="panel-heading"><div><h2>Витрати за категоріями</h2><p>Статистика обраного місяця.</p></div></div>
          <label className="period-picker">Звітний період<input type="month" value={period} onChange={e => setPeriod(e.target.value)} /></label>
          {categories.length ? <div className="category-chart">{categories.map(c => <div className="category-bar-row" key={c.category}><div className="category-bar-label"><strong>{c.category}</strong><span>{money(c.total_amount)} · {Number(c.percentage).toFixed(1)}%</span></div><div className="progress-track"><span style={{ width: `${Math.min(100, Number(c.total_amount) / maxCategory * 100)}%` }} /></div></div>)}</div> : <p className="empty-state compact">Для цього місяця ще немає статистики за категоріями.</p>}
        </section>
      </div>

      <div className="content-grid">
        <section className="panel">
          <div className="panel-heading"><div><h2>Створити звіт</h2><p>Додайте підсумок витрат за місяць.</p></div><span className="panel-icon">＋</span></div>
          <form className="form-stack" onSubmit={submit}>
            <div className="form-two-columns"><label>Період<input type="month" value={form.period} onChange={e => setForm(v => ({ ...v, period: e.target.value }))} required /></label><label>Витрачено, ₴<input type="number" min="0" step="0.01" value={form.total_spent} onChange={e => setForm(v => ({ ...v, total_spent: e.target.value }))} required /></label></div>
            <label>Рекомендації / нотатки<textarea rows="3" value={form.recommendations_text} onChange={e => setForm(v => ({ ...v, recommendations_text: e.target.value }))} placeholder="На чому можна заощадити…" /></label>
            <button className="button button-primary" disabled={busy}>{busy ? 'Збереження…' : 'Зберегти звіт'}</button>
          </form>
        </section>
        <section className="panel">
          <div className="panel-heading"><div><h2>Історія звітів</h2><p>Збережені підсумки родини.</p></div><span className="count-pill">{reports.length}</span></div>
          {!reports.length ? <p className="empty-state">Звітів ще немає. Створіть перший.</p> : <div className="report-list">{reports.map(report => <article className="report-row" key={report.id}><div><strong>{report.period}</strong><span>{report.recommendations_text || 'Без додаткових нотаток'}</span></div><strong>{money(report.total_spent)}</strong><button className="icon-button danger-text" title="Видалити звіт" onClick={async () => { if (window.confirm('Видалити звіт?')) { try { await deleteReport(report.id); await load(period); } catch (e) { setError(e.message); } } }}>×</button></article>)}</div>}
        </section>
      </div>
    </section>
  );
}