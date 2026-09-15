import React from 'react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { BrandLogo } from './BrandLogo';
import { Bell, LogOut, Globe } from 'lucide-react';

export function Header({ onOpenNotifications, unreadCount = 0 }) {
  const { user, logout, getRoleLabel } = useAuth();
  const { language, setLanguage, t } = useLanguage();

  const localizedRole = t(`role_${user?.role}`, getRoleLabel(user?.role));

  return (
    <header className="bg-white border-b border-[#D9E2DC] border-t-3 border-t-[#E68A00] sticky top-0 z-30 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand with Official Ayush Logo */}
        <BrandLogo variant="header" />

        {/* Right Section: Role Status, Language Switcher, Notifications, User */}
        <div className="flex items-center space-x-3 sm:space-x-4">
          
          {/* Read-Only Role Designation Badge */}
          <div className="hidden sm:flex items-center space-x-2">
            <span className="text-[11px] text-[#52616B] font-medium">{t('activeRole', 'Active Role')}:</span>
            <span className="px-2.5 py-1 rounded-lg text-xs font-bold border border-[#D9E2DC] bg-[#F0F4F8] text-[#17324D] shadow-2xs flex items-center space-x-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#166534]"></span>
              <span>{localizedRole}</span>
            </span>
          </div>

          {/* Language Toggle */}
          <div className="inline-flex items-center bg-[#F0F4F8] border border-[#D9E2DC] rounded-lg p-0.5 text-xs">
            <Globe className="w-3.5 h-3.5 text-[#17324D] ml-1.5 mr-1" />
            <button
              onClick={() => setLanguage('en')}
              className={`px-2 py-0.5 rounded text-[11px] font-semibold transition-colors cursor-pointer ${
                language === 'en'
                  ? 'bg-[#166534] text-white shadow-2xs font-bold'
                  : 'text-[#52616B] hover:text-[#172026]'
              }`}
            >
              EN
            </button>
            <button
              onClick={() => setLanguage('hi')}
              className={`px-2 py-0.5 rounded text-[11px] font-semibold transition-colors cursor-pointer ${
                language === 'hi'
                  ? 'bg-[#166534] text-white shadow-2xs font-bold'
                  : 'text-[#52616B] hover:text-[#172026]'
              }`}
            >
              हिन्दी
            </button>
          </div>

          {/* Notifications Bell */}
          <button
            onClick={onOpenNotifications}
            className="relative p-2 text-[#17324D] hover:text-[#166534] hover:bg-[#F0F4F8] rounded-lg transition-colors cursor-pointer"
            title={t('notifications', 'Notification Centre')}
          >
            <Bell className="w-5 h-5" />
            {unreadCount > 0 && (
              <span className="absolute top-1.5 right-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-[#C62828] text-[10px] font-bold text-white ring-2 ring-white animate-pulse">
                {unreadCount}
              </span>
            )}
          </button>

          {/* User & Logout */}
          <div className="flex items-center space-x-2 pl-2 border-l border-[#D9E2DC]">
            <div className="hidden lg:block text-right">
              <div className="text-xs font-bold text-[#172026] leading-tight">{user?.name}</div>
              <div className="text-[10px] text-[#52616B] leading-tight font-mono">{user?.email}</div>
            </div>
            <button
              onClick={logout}
              className="p-1.5 text-[#52616B] hover:text-[#C62828] hover:bg-[#FEE2E2] rounded-lg transition-colors cursor-pointer"
              title={t('logout', 'Sign Out')}
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>

        </div>
      </div>
    </header>
  );
}
