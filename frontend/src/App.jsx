import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import HomePage from './pages/HomePage';
import Layout from './components/Layout';
import DashboardPage from './pages/DashboardPage';
import TasksPage from './pages/TasksPage';
import SubjectsPage from './pages/SubjectsPage';
import ProfilePage from './pages/ProfilePage';

function AppContent() {
  const { token, loading } = useAuth();
  const [activePage, setActivePage] = useState('dashboard');

  if (loading) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'var(--bg-app)',
        color: 'var(--text-muted)',
        fontFamily: 'var(--font-body)',
        fontSize: '15px'
      }}>
        Initializing Meticul...
      </div>
    );
  }

  if (!token) {
    return <HomePage />;
  }

  return (
    <Layout activePage={activePage} setActivePage={setActivePage}>
      {activePage === 'dashboard' && <DashboardPage />}
      {activePage === 'tasks' && (
        <TasksPage onNavigateToSubjects={() => setActivePage('subjects')} />
      )}
      {activePage === 'subjects' && <SubjectsPage />}
      {activePage === 'profile' && <ProfilePage />}
    </Layout>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
