import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { LanguageProvider, useLanguage } from './context/LanguageContext';
import { Header } from './components/Header';
import { Login } from './components/Login';
import { NotificationCenter } from './components/NotificationCenter';
import { PIDashboard } from './components/dashboards/PIDashboard';
import { CoordinatorDashboard } from './components/dashboards/CoordinatorDashboard';
import { PVDashboard } from './components/dashboards/PVDashboard';
import { RegulatorDashboard } from './components/dashboards/RegulatorDashboard';
import { AdminDashboard } from './components/dashboards/AdminDashboard';
import { MonitorDashboard } from './components/dashboards/MonitorDashboard';
import { EthicsDashboard } from './components/dashboards/EthicsDashboard';

function MainApp() {
  const { user, loading } = useAuth();
  const { t } = useLanguage();
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F7F8F5] flex items-center justify-center text-[#17324D] text-sm font-semibold">
        {t('loadingPortal', 'Loading AAYUR SATHI Portal...')}
      </div>
    );
  }

  if (!user) {
    return <Login />;
  }

  const renderDashboard = () => {
    switch (user.role) {
      case 'pi':
        return <PIDashboard />;
      case 'coordinator':
        return <CoordinatorDashboard />;
      case 'pharmacovigilance':
        return <PVDashboard />;
      case 'regulator':
        return <RegulatorDashboard />;
      case 'admin':
        return <AdminDashboard />;
      case 'monitor':
        return <MonitorDashboard />;
      case 'ethics_committee':
        return <EthicsDashboard />;
      default:
        return (
          <div className="p-8 text-center text-slate-500">
            Unknown role: {user.role}
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen bg-[#F7F8F5] text-[#172026] flex flex-col">
      {/* Official Header */}
      <Header
        onOpenNotifications={() => setNotificationsOpen(true)}
        unreadCount={unreadCount}
      />

      {/* Main Role Dashboard Outlet */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {renderDashboard()}
      </main>

      {/* Notification Center Slide-Over */}
      <NotificationCenter
        isOpen={notificationsOpen}
        onClose={() => setNotificationsOpen(false)}
        onCountUpdate={setUnreadCount}
      />
    </div>
  );
}

export default function App() {
  return (
    <LanguageProvider>
      <AuthProvider>
        <MainApp />
      </AuthProvider>
    </LanguageProvider>
  );
}
