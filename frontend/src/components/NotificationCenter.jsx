import React, { useState, useEffect } from 'react';
import { aeApi, studiesApi } from '../api';
import { useLanguage } from '../context/LanguageContext';
import { X, AlertTriangle, Clock, Calendar, CheckCircle2, ShieldAlert } from 'lucide-react';

export function NotificationCenter({ isOpen, onClose, onCountUpdate }) {
  const { t } = useLanguage();
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isOpen) return;
    loadAlerts();
  }, [isOpen]);

  // Initial count check
  useEffect(() => {
    loadAlerts();
  }, []);

  const loadAlerts = async () => {
    try {
      setLoading(true);
      const [studiesRes, aeRes] = await Promise.all([
        studiesApi.list(),
        aeApi.list({}),
      ]);

      const items = [];

      // Check for overdue milestones across studies
      studiesRes.data.forEach((s) => {
        if (s.iec_approval_status === 'pending') {
          items.push({
            id: `iec-${s.id}`,
            type: 'warning',
            title: t('notif_iec_pending_title'),
            message: `Study "${s.title}" awaits Ethics Committee clearance.`,
            meta: `Phase: ${s.phase || 'N/A'}`,
          });
        }
        if (s.ctri_status === 'not_registered' && s.enrolled_count === 0) {
          items.push({
            id: `ctri-${s.id}`,
            type: 'info',
            title: t('notif_ctri_gate_title'),
            message: `Enrollment locked for "${s.title}" until CTRI registration is completed.`,
            meta: 'Regulatory Compliance Gate',
          });
        }
      });

      // Check urgent AE regulatory deadlines
      const today = new Date();
      aeRes.data.forEach((ae) => {
        const deadline = new Date(ae.regulatory_deadline);
        const diffDays = Math.ceil((deadline - today) / (1000 * 60 * 60 * 24));

        if (ae.status !== 'resolved' && ae.status !== 'reported') {
          if (diffDays <= 3 && diffDays >= 0) {
            items.push({
              id: `ae-${ae.id}`,
              type: 'critical',
              title: `${t('notif_ae_urgent_title')}: ${diffDays} ${t('pv_days_left')}`,
              message: `Regulatory reporting deadline imminent for ${ae.seriousness} event: "${ae.ae_term || ae.description}"`,
              meta: `Deadline: ${ae.regulatory_deadline} (NPvCC Escalation)`,
            });
          } else if (diffDays < 0) {
            items.push({
              id: `ae-overdue-${ae.id}`,
              type: 'critical',
              title: t('notif_ae_overdue_title'),
              message: `AE report deadline elapsed on ${ae.regulatory_deadline}. Immediate action required.`,
              meta: `Term: ${ae.ae_term || ae.description}`,
            });
          }
        }
      });

      setAlerts(items);
      if (onCountUpdate) {
        onCountUpdate(items.length);
      }
    } catch (err) {
      console.error('Error fetching alerts:', err);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-[#17324D]/40 backdrop-blur-xs flex justify-end">
      <div className="w-full max-w-md bg-white h-full shadow-2xl flex flex-col border-l border-[#D9E2DC] animate-in slide-in-from-right duration-200">
        
        {/* Header with subtle Saffron accent */}
        <div className="px-6 py-4 border-b border-[#D9E2DC] border-t-3 border-t-[#E68A00] flex items-center justify-between bg-white">
          <div className="flex items-center space-x-2">
            <ShieldAlert className="w-5 h-5 text-[#166534]" />
            <h3 className="font-bold text-[#17324D] text-sm">{t('notif_feed_title')}</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-[#52616B] hover:text-[#172026] hover:bg-[#F0F4F8] transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-[#F7F8F5]">
          {loading ? (
            <div className="text-center py-12 text-xs text-[#52616B]">{t('notif_loading')}</div>
          ) : alerts.length === 0 ? (
            <div className="text-center py-12 text-[#52616B]">
              <CheckCircle2 className="w-8 h-8 text-[#15803D] mx-auto mb-2" />
              <p className="text-xs">{t('notif_no_alerts')}</p>
            </div>
          ) : (
            alerts.map((a) => (
              <div
                key={a.id}
                className={`p-3.5 rounded-xl border text-left transition-all ${
                  a.type === 'critical'
                    ? 'bg-[#FEE2E2] border-[#FCA5A5] text-[#7F1D1D]'
                    : a.type === 'warning'
                    ? 'bg-[#FEF3C7] border-[#FCD39B] text-[#78350F]'
                    : 'bg-white border-[#D9E2DC] text-[#172026] shadow-2xs'
                }`}
              >
                <div className="flex items-start space-x-2.5">
                  {a.type === 'critical' ? (
                    <AlertTriangle className="w-4 h-4 text-[#C62828] mt-0.5 shrink-0" />
                  ) : a.type === 'warning' ? (
                    <Clock className="w-4 h-4 text-[#D97706] mt-0.5 shrink-0" />
                  ) : (
                    <Calendar className="w-4 h-4 text-[#17324D] mt-0.5 shrink-0" />
                  )}
                  <div className="flex-1">
                    <h4 className="text-xs font-bold">{a.title}</h4>
                    <p className="text-xs mt-0.5 opacity-90">{a.message}</p>
                    <span className="inline-block mt-1.5 text-[10px] font-medium opacity-75">
                      {a.meta}
                    </span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-[#D9E2DC] bg-white text-[11px] text-[#52616B] text-center">
          {t('notif_footer')}
        </div>
      </div>
    </div>
  );
}
