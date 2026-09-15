import React, { useState, useEffect } from 'react';
import { studiesApi, aeApi } from '../../api';
import { useLanguage } from '../../context/LanguageContext';
import { FileText, CheckCircle2, XCircle, AlertTriangle, ShieldCheck, Clock } from 'lucide-react';

export function EthicsDashboard() {
  const { t, formatStatus } = useLanguage();
  const [studies, setStudies] = useState([]);
  const [seriousEvents, setSeriousEvents] = useState([]);
  const [activeNav, setActiveNav] = useState('queue'); // queue, review, sae
  const [selectedStudy, setSelectedStudy] = useState(null);
  const [decisionMsg, setDecisionMsg] = useState('');
  const [loading, setLoading] = useState(true);
  const [submittingId, setSubmittingId] = useState(null);

  useEffect(() => {
    loadEthicsData();
  }, []);

  const loadEthicsData = async () => {
    try {
      setLoading(true);
      const [sRes, aeRes] = await Promise.all([
        studiesApi.list(),
        aeApi.list({ seriousness: 'serious' }),
      ]);
      setStudies(sRes.data);
      setSeriousEvents(aeRes.data);
      const pending = sRes.data.filter((s) => s.status === 'pending_iec');
      if (pending.length > 0) {
        setSelectedStudy(pending[0]);
      } else if (sRes.data.length > 0) {
        setSelectedStudy(sRes.data[0]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDecision = async (studyId, decision) => {
    try {
      setSubmittingId(studyId);
      setDecisionMsg('');
      await studiesApi.iecDecision(studyId, { decision });
      setDecisionMsg(
        decision === 'approved'
          ? t('ec_decision_approved_msg', "Protocol cleared by Institutional Ethics Committee! Study status updated to 'IEC Approved' and logged in immutable audit trail.")
          : t('ec_decision_rejected_msg', "Protocol rejected by Institutional Ethics Committee. Status updated to 'IEC Rejected' and logged in immutable audit trail.")
      );
      await loadEthicsData();
    } catch (err) {
      setDecisionMsg(err.response?.data?.detail || t('error', 'Decision recording failed.'));
    } finally {
      setSubmittingId(null);
    }
  };

  const pendingProtocols = studies.filter((s) => s.status === 'pending_iec');

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-[#17324D] border-t-2 border-t-[#E68A00] rounded-2xl p-6 text-white shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-[#93C5FD] text-xs font-semibold uppercase tracking-wider">
              <ShieldCheck className="w-4 h-4 text-[#E68A00]" />
              <span>{t('ec_portal_badge')}</span>
            </div>
            <h1 className="text-2xl font-bold mt-1 text-white">{t('ec_title')}</h1>
            <p className="text-xs text-slate-300 mt-1">
              {t('ec_subtitle')}
            </p>
          </div>

          <div className="flex items-center space-x-3 bg-white/10 p-3 rounded-xl border border-white/20">
            <div className="text-center px-2">
              <span className="text-[10px] uppercase text-[#93C5FD] block font-bold">{t('ec_pending_clearance')}</span>
              <span className="text-sm font-bold text-white">{pendingProtocols.length} {t('ec_protocols')}</span>
            </div>
          </div>
        </div>

        {/* Nav Tabs */}
        <div className="flex gap-2 mt-6 pt-4 border-t border-white/15 text-xs font-medium">
          <button
            onClick={() => setActiveNav('queue')}
            className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
              activeNav === 'queue' ? 'bg-white text-[#17324D] font-bold shadow-xs' : 'text-slate-200 hover:text-white hover:bg-white/10'
            }`}
          >
            {t('ec_tab_queue')} ({pendingProtocols.length})
          </button>
          <button
            onClick={() => setActiveNav('sae')}
            className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
              activeNav === 'sae' ? 'bg-white text-[#17324D] font-bold shadow-xs' : 'text-slate-200 hover:text-white hover:bg-white/10'
            }`}
          >
            {t('ec_tab_sae')} ({seriousEvents.length})
          </button>
        </div>
      </div>

      {decisionMsg && (
        <div className="p-3 bg-[#EBF3ED] text-[#166534] rounded-xl border border-[#C6DCCE] text-xs font-semibold">
          {decisionMsg}
        </div>
      )}

      {/* Review Queue */}
      {activeNav === 'queue' && (
        <div className="bg-white rounded-2xl border border-[#D9E2DC] shadow-xs p-6 space-y-6">
          <h3 className="text-sm font-bold text-[#172026]">{t('ec_review_title')}</h3>

          {pendingProtocols.length === 0 ? (
            <div className="text-center py-8 text-xs text-[#52616B]">
              {t('ec_no_pending')}
            </div>
          ) : (
            <div className="divide-y divide-[#D9E2DC] border border-[#D9E2DC] rounded-xl overflow-hidden text-xs">
              {pendingProtocols.map((s) => (
                <div key={s.id} className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-[#F7F8F5]">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="bg-[#FEF3C7] text-[#D97706] border border-[#FDE68A] font-bold px-2 py-0.5 rounded text-[10px] uppercase">
                        {formatStatus(s.status)}
                      </span>
                      <span className="text-[#52616B] font-mono text-[10px]">{t('ec_site')}: {s.site_id}</span>
                    </div>
                    <h4 className="font-bold text-[#172026] text-sm">{s.title}</h4>
                    <p className="text-[#52616B] text-[11px]">{t('ec_sponsor')}: {s.sponsor} | {t('ec_planned_cohort')}: {s.enrollment_target} {t('pi_subjects', 'subjects')}</p>
                  </div>

                  <div className="flex items-center space-x-2 shrink-0">
                    <button
                      disabled={submittingId === s.id}
                      onClick={() => handleDecision(s.id, 'approved')}
                      className="flex items-center space-x-1.5 bg-[#166534] hover:bg-[#14532D] text-white px-3.5 py-2 rounded-xl text-xs font-bold transition-colors shadow-xs cursor-pointer disabled:opacity-50"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>{submittingId === s.id ? t('loading', 'Processing...') : t('ec_decision_approve')}</span>
                    </button>
                    <button
                      disabled={submittingId === s.id}
                      onClick={() => handleDecision(s.id, 'rejected')}
                      className="flex items-center space-x-1.5 bg-[#C62828] hover:bg-[#B71C1C] text-white px-3.5 py-2 rounded-xl text-xs font-bold transition-colors shadow-xs cursor-pointer disabled:opacity-50"
                    >
                      <XCircle className="w-3.5 h-3.5" />
                      <span>{submittingId === s.id ? t('loading', 'Processing...') : t('ec_decision_reject')}</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Serious AE Escalation */}
      {activeNav === 'sae' && (
        <div className="bg-white rounded-2xl border border-[#D9E2DC] shadow-xs p-6 space-y-4">
          <div className="flex items-center space-x-2 text-[#172026] font-bold">
            <AlertTriangle className="w-5 h-5 text-[#C62828]" />
            <h3 className="text-base">{t('ec_sae_title')}</h3>
          </div>
          <p className="text-xs text-[#52616B]">
            {t('ec_sae_desc')}
          </p>

          <div className="divide-y divide-[#D9E2DC] border border-[#D9E2DC] rounded-xl overflow-hidden text-xs">
            {seriousEvents.map((ae) => (
              <div key={ae.id} className="p-4 flex items-center justify-between hover:bg-[#F7F8F5]">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="bg-[#FEE2E2] text-[#C62828] border border-[#FECACA] font-bold px-2 py-0.5 rounded text-[10px] uppercase">
                      {t('pv_filter_serious', 'Serious SAE')}
                    </span>
                    <span className="font-bold text-[#172026] capitalize">{ae.ae_term || ae.description}</span>
                  </div>
                  <p className="text-[#52616B] text-[11px]">{ae.description}</p>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-[#52616B] block">{t('ec_regulatory_deadline')}</span>
                  <span className="font-mono font-bold text-[#C62828]">{ae.regulatory_deadline}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
