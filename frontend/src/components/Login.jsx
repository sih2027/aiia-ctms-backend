import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { BrandLogo } from './BrandLogo';
import { Lock, Mail, ArrowRight, Shield, Globe } from 'lucide-react';

export function Login() {
  const { login } = useAuth();
  const { language, setLanguage, t } = useLanguage();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await login(email, password);
    } catch (err) {
      if (err.response?.status === 401) {
        setError(t('invalidCredentialsError', 'Invalid email or password. Please verify your credentials.'));
      } else {
        setError(
          err.response?.data?.detail ||
          t('connectionError', 'Unable to connect to the authentication service. Please ensure system services are active.')
        );
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F7F8F5] flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8">
      
      {/* Top Language Bar */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md flex justify-end mb-3">
        <div className="inline-flex items-center space-x-1.5 bg-white border border-[#D9E2DC] rounded-full px-3 py-1 shadow-2xs text-xs text-[#52616B]">
          <Globe className="w-3.5 h-3.5 text-[#17324D]" />
          <span className="text-[11px] font-medium mr-1">{t('languageSelectLabel', 'Language')}:</span>
          <button
            type="button"
            onClick={() => setLanguage('en')}
            className={`px-2 py-0.5 rounded-full text-xs font-semibold transition-colors cursor-pointer ${
              language === 'en'
                ? 'bg-[#166534] text-white shadow-2xs'
                : 'text-[#52616B] hover:text-[#172026]'
            }`}
          >
            English
          </button>
          <span className="text-[#D9E2DC]">|</span>
          <button
            type="button"
            onClick={() => setLanguage('hi')}
            className={`px-2 py-0.5 rounded-full text-xs font-semibold transition-colors cursor-pointer ${
              language === 'hi'
                ? 'bg-[#166534] text-white shadow-2xs'
                : 'text-[#52616B] hover:text-[#172026]'
            }`}
          >
            हिन्दी
          </button>
        </div>
      </div>

      {/* Main Container */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        
        {/* Brand Header with subtle Saffron accent */}
        <div className="bg-white py-6 px-6 sm:px-8 rounded-t-2xl shadow-xs border-t-4 border-t-[#E68A00] border-x border-[#D9E2DC]">
          <BrandLogo variant="login" />
        </div>

        {/* Form Card */}
        <div className="bg-white py-8 px-6 sm:px-8 shadow-xs rounded-b-2xl border border-[#D9E2DC] border-t-0">
          <div className="mb-6 pb-4 border-b border-[#D9E2DC]">
            <h2 className="text-base font-bold text-[#17324D]">
              {t('signInTitle', 'Official Portal Sign In')}
            </h2>
            <p className="text-xs text-[#52616B] mt-0.5">
              {t('signInSubtitle', 'Secure access for authorized clinical researchers, ethics committees, and regulators.')}
            </p>
          </div>

          {error && (
            <div className="mb-5 p-3.5 bg-[#FEE2E2] border border-[#FCA5A5] text-[#C62828] text-xs rounded-xl flex items-start space-x-2">
              <span className="font-bold">•</span>
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-[#172026] mb-1">
                {t('officialEmailLabel', 'Official Email ID')}
              </label>
              <div className="relative rounded-lg shadow-2xs">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#52616B]">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  type="email"
                  required
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder={t('emailPlaceholder', 'officer@ayush.gov.in')}
                  className="block w-full pl-9 pr-3 py-2.5 rounded-lg border border-[#D9E2DC] text-sm bg-white text-[#172026] placeholder-[#7E8E98] focus:border-[#166534] focus:outline-hidden focus:ring-1 focus:ring-[#166534]"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-[#172026] mb-1">
                {t('passwordLabel', 'Password')}
              </label>
              <div className="relative rounded-lg shadow-2xs">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-[#52616B]">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type="password"
                  required
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={t('passwordPlaceholder', 'Enter your password')}
                  className="block w-full pl-9 pr-3 py-2.5 rounded-lg border border-[#D9E2DC] text-sm bg-white text-[#172026] placeholder-[#7E8E98] focus:border-[#166534] focus:outline-hidden focus:ring-1 focus:ring-[#166534]"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full mt-2 flex items-center justify-center space-x-2 bg-[#166534] hover:bg-[#14532D] text-white font-bold py-2.5 px-4 rounded-xl transition-all text-sm shadow-xs disabled:opacity-50 cursor-pointer"
            >
              <span>{submitting ? t('authenticatingButton', 'Authenticating...') : t('signInButton', 'Sign In')}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Institutional Compliance Notice */}
          <div className="mt-6 pt-4 border-t border-[#D9E2DC] text-center">
            <div className="flex items-center justify-center space-x-1.5 text-[11px] text-[#52616B]">
              <Shield className="w-3.5 h-3.5 text-[#166534] shrink-0" />
              <span>{t('securityNotice', 'Authorized government and institutional personnel only.')}</span>
            </div>
            <p className="text-[10px] text-[#7E8E98] mt-1">
              Ministry of Ayush, Government of India • Official Clinical Trial Portal
            </p>
          </div>
        </div>

      </div>
    </div>
  );
}
