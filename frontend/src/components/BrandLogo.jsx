import React from 'react';
import ayushLogo from '../assets/ayush_logo.png';
import { useLanguage } from '../context/LanguageContext';

export function BrandLogo({ variant = 'header', className = '' }) {
  const { t } = useLanguage();

  if (variant === 'login') {
    return (
      <div className={`flex flex-col items-center text-center ${className}`}>
        {/* Official Ministry of Ayush Emblem Banner */}
        <div className="bg-white p-3 rounded-2xl border border-[#D9E2DC] shadow-xs max-w-sm sm:max-w-md w-full flex items-center justify-center">
          <img
            src={ayushLogo}
            alt="Ministry of Ayush, Government of India"
            className="h-14 sm:h-16 w-auto object-contain"
            style={{ maxWidth: '100%' }}
          />
        </div>

        {/* Brand Name & Subtitle */}
        <h1 className="mt-5 text-2xl sm:text-3xl font-extrabold text-[#17324D] tracking-tight">
          {t('brandName', 'AAYUR SATHI')}
        </h1>
        <p className="mt-1 text-sm sm:text-base font-semibold text-[#166534]">
          {t('brandTagline', 'Clinical Trial Management & Pharmacovigilance Portal')}
        </p>
        <p className="mt-0.5 text-xs font-medium text-[#52616B] tracking-wide uppercase">
          {t('institutionalSubtitle', 'All India Institute of Ayurveda')}
        </p>
      </div>
    );
  }

  // Header variant
  return (
    <div className={`flex items-center space-x-3.5 ${className}`}>
      <div className="bg-white p-1 rounded-lg border border-[#D9E2DC] shadow-xs flex items-center justify-center shrink-0">
        <img
          src={ayushLogo}
          alt="Ministry of Ayush, Government of India"
          className="h-9 w-auto object-contain"
        />
      </div>
      <div className="border-l border-[#D9E2DC] pl-3">
        <div className="flex items-center space-x-2">
          <span className="font-bold text-base sm:text-lg text-[#17324D] tracking-tight leading-none">
            {t('brandName', 'AAYUR SATHI')}
          </span>
          <span className="hidden md:inline-block text-[10px] bg-[#EBF5EE] text-[#166534] font-semibold px-2 py-0.5 rounded-full border border-[#BBDFC5]">
            {t('npvccBadge', 'NPvCC Safety Node Active')}
          </span>
        </div>
        <p className="text-[11px] font-medium text-[#52616B] hidden sm:block mt-0.5 leading-tight">
          {t('brandTagline', 'Clinical Trial Management & Pharmacovigilance Portal')} • {t('institutionalSubtitle', 'All India Institute of Ayurveda')}
        </p>
      </div>
    </div>
  );
}
