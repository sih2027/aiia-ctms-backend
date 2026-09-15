import React, { createContext, useContext, useState, useEffect } from 'react';
import { translations } from '../i18n';

const LanguageContext = createContext();

const STORAGE_KEY = 'aayur_sathi_lang';

export function LanguageProvider({ children }) {
  const [language, setLanguageState] = useState(() => {
    return localStorage.getItem(STORAGE_KEY) || 'en';
  });

  const setLanguage = (lang) => {
    if (translations[lang]) {
      setLanguageState(lang);
      localStorage.setItem(STORAGE_KEY, lang);
    }
  };

  useEffect(() => {
    if (language === 'hi') {
      document.title = 'आयुर साथी — नैदानिक परीक्षण प्रबंधन एवं भेषजगुण निगरानी पोर्टल';
    } else {
      document.title = 'AAYUR SATHI — Clinical Trial Management & Pharmacovigilance Portal';
    }
  }, [language]);

  const t = (key, fallback) => {
    const dict = translations[language] || translations.en;
    if (dict && dict[key] !== undefined) {
      return dict[key];
    }
    return fallback !== undefined ? fallback : key;
  };

  const formatStatus = (statusStr) => {
    if (!statusStr) return '';
    const key = 'status_' + statusStr.toLowerCase();
    const fallback = statusStr.replace(/_/g, ' ').toUpperCase();
    return t(key, fallback);
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t, formatStatus }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}
