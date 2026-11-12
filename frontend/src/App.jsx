import React, { useState } from 'react';
import useAuth from './hooks/useAuth';
import AuthPage from './components/Auth/AuthPage';
import Navbar from './components/Layout/Navbar';
import BudgetSection from './components/budget/BudgetSection';
import ShoppingList from './components/shopping/ShoppingList';
import AnalyticsDashboard from './components/analytics/AnalyticsDashboard';
import AdminDashboard from './components/Admin/AdminDashboard';

export default function App() {
  const {
    user, familyMembers, loading, login, register, logout,
    changeMemberRole, removeMember, addFamilyMember,
    updateUsername, renameFamily,   deleteMyAccount,
    removeFamily, googleRegistrationToken, oauthError,
    finishGoogleRegistration, linkGoogle,
  } = useAuth();
  const [activeTab, setActiveTab] = useState('shopping');

  if (loading) {
    return (
      <div className="app-loading">
        <span className="loading-spinner" />
        <strong>Завантажуємо FamilyPlan</strong>
        <span>Готуємо ваш сімейний простір…</span>
      </div>
    );
  }

  if (!user.token) {
    return (
      <AuthPage
        onLogin={login}
        onRegister={register}
        googleRegistrationToken={googleRegistrationToken}
        oauthError={oauthError}
        onGoogleRegister={finishGoogleRegistration}
      />
    );
  }

  return (
    <div className="app">
      <Navbar
        user={user}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        familyMembers={familyMembers}
        onLogout={logout}
        onProfileUpdated={updateUsername}
        onFamilyNameUpdated={renameFamily}
        onUserAdded={addFamilyMember}
        onUpdateRole={changeMemberRole}
        onDeleteMember={removeMember}
        onDeleteAccount={deleteMyAccount}
        onDeleteFamily={removeFamily}
        onLinkGoogle={linkGoogle}
      />
      <main className="app-content">
        {user.role === 'admin' ? (
          <AdminDashboard />
        ) : (
          <>
            {activeTab === 'budget' && <BudgetSection user={user} />}
            {activeTab === 'shopping' && <ShoppingList />}
            {activeTab === 'analytics' && <AnalyticsDashboard />}
          </>
        )}
      </main>
      <footer className="app-footer">FamilyPlan · Плануйте разом, витрачайте розумно</footer>
    </div>
  );
}