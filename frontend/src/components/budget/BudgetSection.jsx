import React, { useEffect, useState } from 'react';

import {
  getFamilyBudgets,
  saveBudget,
  updateBudget,
  deleteBudget,
  addExpenseOrPlan,
  updateExpenseOrPlan,
  deleteExpenseOrPlan,
} from '../../api/budgetService';

const money = value => `${Number(value || 0).toLocaleString('uk-UA', { maximumFractionDigits: 2 })} ₴`;
const dateInput = date => date ? String(date).slice(0, 10) : '';
const getLocalDate = () => {
  const now = new Date();
  const offset = now.getTimezoneOffset();

  return new Date(now.getTime() - offset * 60000)
    .toISOString()
    .slice(0, 10);
};

export default function BudgetSection({ user }) {
  const [budgets, setBudgets] = useState([]);
  const [selectedId, setSelectedId] = useState('');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [budgetForm, setBudgetForm] = useState({ total_planned_budget: '', start_date: '', end_date: '', currency: 'UAH' });
  const [editingBudget, setEditingBudget] = useState(null);
  const [expenseForm, setExpenseForm] = useState({
      title: '',
      amount: '',
      category: 'Продукти',
      date: getLocalDate(),
    });
  const [editingExpense, setEditingExpense] = useState(null);

  const isHead = user?.role === 'head';
  const isAllPeriods = selectedId === 'all';

  const selected = isAllPeriods
    ? null
    : budgets.find(b => String(b.id) === String(selectedId)) || budgets[0];

  const allExpenses = budgets.flatMap(budget =>
    (budget.expenses || []).map(expense => ({
      ...expense,
      budgetStartDate: budget.start_date,
      budgetEndDate: budget.end_date,
    }))
  );

  const displayedExpenses = isAllPeriods
    ? allExpenses
    : selected?.expenses || [];

  const totalBudget = isAllPeriods
    ? budgets.reduce((sum, b) => sum + Number(b.total_planned_budget || 0), 0)
    : Number(selected?.total_planned_budget || 0);

  const totalSpent = isAllPeriods
    ? budgets.reduce((sum, b) => sum + Number(b.total_spent || 0), 0)
    : Number(selected?.total_spent || 0);

  const totalPlanned = isAllPeriods
    ? budgets.reduce((sum, b) => sum + Number(b.total_planned_expenses || 0), 0)
    : Number(selected?.total_planned_expenses || 0);

  const remainingBudget = isAllPeriods
    ? budgets.reduce((sum, b) => sum + Number(b.remaining_budget || 0), 0)
    : Number(selected?.remaining_budget || 0);

  const progress = totalBudget
    ? Math.min(100, (totalSpent / totalBudget) * 100)
    : 0;

  
  const load = async () => {
    setLoading(true); setError('');
    try {
      const data = await getFamilyBudgets();
      setBudgets(Array.isArray(data) ? data : []);
      setSelectedId(current =>
        current === 'all' || data.some(b => String(b.id) === String(current))
          ? current
          : String(data[0]?.id || '')
      );
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const submitBudget = async e => {
    e.preventDefault(); setBusy(true); setError('');
    try {
      const payload = {
        total_planned_budget: Number(budgetForm.total_planned_budget),
        currency: budgetForm.currency,
        start_date: `${budgetForm.start_date}T00:00:00`,
        end_date: `${budgetForm.end_date}T23:59:59`,
      };
      if (editingBudget) await updateBudget(editingBudget.id, payload);
      else await saveBudget(payload);
      setBudgetForm({ total_planned_budget: '', start_date: '', end_date: '', currency: 'UAH' });
      setEditingBudget(null);
      await load();
    } catch (e) { setError(e.message); }
    finally { setBusy(false); }
  };

    const startEdit = budget => {
      setEditingBudget(budget);

      setBudgetForm({
        total_planned_budget: String(budget.total_planned_budget),
        start_date: dateInput(budget.start_date),
        end_date: dateInput(budget.end_date),
        currency: budget.currency || 'UAH',
      });

      window.scrollTo({ top: 0, behavior: 'smooth' });
    };
    const startEditExpense = item => {
    setEditingExpense(item);

    setExpenseForm({
      title: item.title || '',
      amount: String(item.amount || ''),
      category: item.category || 'Продукти',
      date: dateInput(item.date),
    });

    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const submitExpense = async e => {
    e.preventDefault();

    setBusy(true);
    setError('');

    try {
      const payload = {
        title: expenseForm.title.trim(),
        amount: Number(expenseForm.amount),
        category: expenseForm.category || 'Загальні',
        date: `${expenseForm.date}T12:00:00`,
        is_planned: editingExpense
          ? Number(editingExpense.is_planned)
          : 1,
      };

      if (editingExpense) {
        await updateExpenseOrPlan(editingExpense.id, payload);
      } else {
        await addExpenseOrPlan(payload);
      }

      setExpenseForm({
        title: '',
        amount: '',
        category: 'Продукти',
        date: getLocalDate(),
      });

      setEditingExpense(null);

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
      <div className="page-heading">
        <div><span className="eyebrow">ФІНАНСИ РОДИНИ</span><h1>Сімейний бюджет</h1><p>Плануйте витрати та контролюйте залишок коштів.</p></div>
        <span className="heading-icon">₴</span>
      </div>
      {error && <div className="alert alert-error">{error}</div>}

      {budgets.length > 0 && (
        <div className="budget-switcher">
          <label>Бюджетний період
            <select
              value={isAllPeriods ? 'all' : selected?.id || ''}
              onChange={e => setSelectedId(e.target.value)}
            >
              <option value="all">Усі періоди</option>

              {budgets.map(b => (
                <option key={b.id} value={b.id}>
                  {dateInput(b.start_date)} — {dateInput(b.end_date)}
                </option>
              ))}
            </select>
          </label>
          {selected && <div className="budget-switcher-actions">
          {isHead && (
            <button
              className="button button-secondary button-small"
              onClick={() => startEdit(selected)}
            >
              Редагувати період
            </button>
          )}

          {isHead && (
            <button
              className="button button-danger button-small"
              onClick={async () => {
                if (window.confirm('Видалити бюджет разом з усіма його витратами?')) {
                  try {
                    await deleteBudget(selected.id);
                    await load();
                  } catch (e) {
                    setError(e.message);
                  }
                }
              }}
            >
              Видалити
            </button>
          )}
          </div>}
        </div>
      )}

      {selected || isAllPeriods ?  (
        <>
          <div className="stats-grid">
            <article className="stat-card">
              <span>Запланований бюджет</span>
              <strong>{money(totalBudget)}</strong>
              <small>{isAllPeriods ? 'За всі періоди' : 'На обраний період'}</small>
            </article>

            <article className="stat-card">
              <span>Фактичні витрати</span>
              <strong>{money(totalSpent)}</strong>
              <small>Уже витрачено</small>
            </article>

            <article className="stat-card">
              <span>Заплановані витрати</span>
              <strong>{money(totalPlanned)}</strong>
              <small>Ще не здійснені</small>
            </article>

            <article className="stat-card accent-stat">
              <span>Залишок</span>
              <strong>{money(remainingBudget)}</strong>
              <small>Після фактичних витрат</small>
            </article>
          </div>
          <div className="panel budget-progress-panel">
            <div className="panel-title-row">
              <div>
                <h2>Використання бюджету</h2>
                <p>{progress.toFixed(1)}% від запланованої суми</p>
              </div>
              <strong>
                {money(totalSpent)} / {money(totalBudget)}
              </strong>
            </div>
            <div className="progress-track"><span style={{ width: `${progress}%` }} /></div>
          </div>
        </>
      ) : (
        <div className="panel empty-panel"><div className="empty-illustration">₴</div><h2>Бюджет ще не створено</h2><p>Створіть період, щоб додавати витрати та відстежувати залишок.</p></div>
      )}

      <div className="content-grid">
        {isHead && <section className="panel">
          <div className="panel-heading"><div><h2>{editingBudget ? 'Редагування бюджету' : 'Новий бюджет'}</h2><p>Визначте суму та період планування.</p></div><span className="panel-icon">＋</span></div>
          <form className="form-stack" onSubmit={submitBudget}>
            <label>Сума бюджету<input type="number" min="0.01" step="0.01" value={budgetForm.total_planned_budget} onChange={e => setBudgetForm(v => ({ ...v, total_planned_budget: e.target.value }))} required /></label>
            <div className="form-two-columns">
              <label>Початок<input type="date" value={budgetForm.start_date} onChange={e => setBudgetForm(v => ({ ...v, start_date: e.target.value }))} required /></label>
              <label>Завершення<input type="date" value={budgetForm.end_date} min={budgetForm.start_date} onChange={e => setBudgetForm(v => ({ ...v, end_date: e.target.value }))} required /></label>
            </div>
            <label>Валюта<select value={budgetForm.currency} onChange={e => setBudgetForm(v => ({ ...v, currency: e.target.value }))}><option value="UAH">UAH — гривня</option><option value="USD">USD — долар</option><option value="EUR">EUR — євро</option></select></label>
            <div className="form-actions"><button className="button button-primary" disabled={busy}>{busy ? 'Збереження…' : editingBudget ? 'Зберегти зміни' : 'Створити бюджет'}</button>{editingBudget && <button type="button" className="button button-secondary" onClick={() => { setEditingBudget(null); setBudgetForm({ total_planned_budget: '', start_date: '', end_date: '', currency: 'UAH' }); }}>Скасувати</button>}</div>
          </form>
        </section>}

        <section className="panel">
          <div className="panel-heading"><div><h2>
              {editingExpense ? 'Редагувати заплановану витрату' : 'Запланувати витрату'}
            </h2>
            <p>
              Витрата автоматично прив’яжеться до бюджетного періоду за датою.
            </p>
          </div><span className="panel-icon">↗</span></div>
          <form className="form-stack" onSubmit={submitExpense}>
            <label>Назва витрати<input value={expenseForm.title} onChange={e => setExpenseForm(v => ({ ...v, title: e.target.value }))} placeholder="Наприклад, продукти" required /></label>
            <div className="form-two-columns">
              <label>Сума<input type="number" min="0.01" step="0.01" value={expenseForm.amount} onChange={e => setExpenseForm(v => ({ ...v, amount: e.target.value }))} required /></label>
              <label>Дата<input type="date" value={expenseForm.date} onChange={e => setExpenseForm(v => ({ ...v, date: e.target.value }))} required /></label>
            </div>
            <label>Категорія<select value={expenseForm.category} onChange={e => setExpenseForm(v => ({ ...v, category: e.target.value }))}>{['Продукти','Комунальні послуги','Транспорт','Здоров’я','Освіта','Розваги','Одяг','Інше'].map(x => <option key={x}>{x}</option>)}</select></label>
            <button className="button button-primary" disabled={busy || !budgets.length}>
              {busy
                ? 'Збереження…'
                : editingExpense
                  ? 'Зберегти зміни'
                  : 'Додати витрату'}
            </button>
            {editingExpense && (
            <button
              type="button"
              className="button button-secondary"
              disabled={busy}
              onClick={() => {
                setEditingExpense(null);
                setExpenseForm({
                  title: '',
                  amount: '',
                  category: 'Продукти',
                  date: new Date().toISOString().slice(0, 10),
                });
              }}
            >
              Скасувати редагування
            </button>
          )}
            {!budgets.length && <small className="field-hint">Спочатку потрібно створити бюджетний період.</small>}
          </form>
        </section>
      </div>

      {(selected || isAllPeriods) && (
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h2>Витрати та плани</h2>
              <p>
                {isAllPeriods
                  ? 'Записи за всі бюджетні періоди.'
                  : 'Записи обраного бюджетного періоду.'}
              </p>
            </div>
            <span className="count-pill">{displayedExpenses.length}</span>
          </div>

          {!displayedExpenses.length ? (
            <p className="empty-state">
              У цьому періоді поки немає витрат.
            </p>
          ) : (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Назва</th>
                    <th>Категорія</th>
                    <th>Дата</th>
                    {isAllPeriods && <th>Бюджетний період</th>}
                    <th>Тип</th>
                    <th>Сума</th>
                    <th />
                  </tr>
                </thead>

                <tbody>
                  {displayedExpenses.map(item => (
                    <tr key={item.id}>
                      <td>
                        <strong>{item.title}</strong>

                        <small className="table-subtitle">
                          {item.username || 'Учасник родини'}
                        </small>

                        {item.source_purchase_id != null && (
                          <small className="table-subtitle">
                            Автоматично зі списку покупок
                          </small>
                        )}
                      </td>

                      <td>{item.category || 'Загальні'}</td>

                      <td>
                        {item.date
                          ? new Date(item.date).toLocaleDateString('uk-UA')
                          : '—'}
                      </td>

                      {isAllPeriods && (
                        <td>
                          {dateInput(item.budgetStartDate)} —{' '}
                          {dateInput(item.budgetEndDate)}
                        </td>
                      )}

                      <td>
                        <span
                          className={`status-pill ${
                            item.is_planned ? 'planned' : 'done'
                          }`}
                        >
                          {item.is_planned ? 'Заплановано' : 'Фактична'}
                        </span>
                      </td>

                      <td className="amount-cell">
                        {money(item.amount)}
                      </td>

                      <td>
                        {Boolean(item.is_planned) && item.source_purchase_id == null && (
                          <button
                            className="icon-button"
                            title="Редагувати витрату"
                            onClick={() => startEditExpense(item)}
                          >
                            ✎
                          </button>
                        )}

                        {item.source_purchase_id == null && (
                          <button
                            className="icon-button danger-text"
                            title="Видалити"
                            onClick={async () => {
                              if (window.confirm('Видалити цей запис?')) {
                                try {
                                  await deleteExpenseOrPlan(item.id);
                                  await load();
                                } catch (e) {
                                  setError(e.message);
                                }
                              }
                            }}
                          >
                            ×
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}
    </section>
  );
}