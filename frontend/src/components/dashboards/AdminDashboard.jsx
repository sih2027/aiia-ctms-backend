import React, { useState, useEffect } from 'react';
import { studiesApi, auditApi, authApi } from '../../api';
import { useLanguage } from '../../context/LanguageContext';
import { Shield, PlusCircle, Users, Settings, Database, Activity, CheckCircle, BarChart3 } from 'lucide-react';

export function AdminDashboard() {
  const { t, formatStatus } = useLanguage();
  const [studies, setStudies] = useState([]);
  const [auditRows, setAuditRows] = useState([]);
  const [investigators, setInvestigators] = useState([]);
  const [selectedPiId, setSelectedPiId] = useState('');
  const [activeNav, setActiveNav] = useState('portfolio'); // portfolio, create, settings, audit
  const [loading, setLoading] = useState(true);

  // Study Creation State
  const [title, setTitle] = useState('');
  const [phase, setPhase] = useState('Phase 2');
  const [sponsor, setSponsor] = useState('All India Institute of Ayurveda (AIIA)');
  const [target, setTarget] = useState(100);
  const [siteId, setSiteId] = useState('AIIA-DELHI-01');
  const [msg, setMsg] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [sRes, aRes, piRes] = await Promise.all([
        studiesApi.list(),
        auditApi.trail({ limit: 40 }),
        authApi.investigators(),
      ]);
      setStudies(sRes.data);
      setAuditRows(aRes.data);
      const pis = piRes.data || [];
      setInvestigators(pis);
      if (pis.length > 0) {
        setSelectedPiId((prev) => prev || pis[0].id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateStudy = async (e) => {
    e.preventDefault();
    setMsg('');
    try {
      await studiesApi.create({
        title,
        phase,
        sponsor,
        enrollment_target: parseInt(target, 10),
        site_id: siteId,
        principal_investigator_id: selectedPiId || undefined,
      });
      setMsg(t('admin_study_created_success', 'Study created successfully! Initial status set to pending_iec.'));
      setTitle('');
      loadData();
    } catch (err) {
      setMsg(err.response?.data?.detail || 'Failed to create study.');
    }
  };

  const handleRegisterCtri = async (studyId) => {
    try {
      await studiesApi.ctriRegister(studyId, {});
      loadData();
    } catch (err) {
      alert(err.response?.data?.detail || 'CTRI registration failed.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Admin Header */}
      <div className="bg-[#17324D] border-t-2 border-t-[#E68A00] rounded-2xl p-6 text-white shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-[#93C5FD] text-xs font-semibold uppercase tracking-wider">
              <Shield className="w-4 h-4 text-[#34D399]" />
              <span>{t('admin_portal_badge')}</span>
            </div>
            <h1 className="text-2xl font-bold mt-1 text-white">{t('admin_title')}</h1>
            <p className="text-xs text-slate-300 mt-1">
              {t('admin_subtitle')}
            </p>
          </div>

          <button
            onClick={() => setActiveNav('create')}
            className="flex items-center space-x-2 bg-[#166534] hover:bg-[#14532D] text-white font-bold px-4 py-2.5 rounded-xl text-xs transition-all shadow-xs cursor-pointer"
          >
            <PlusCircle className="w-4 h-4" />
            <span>{t('admin_btn_configure')}</span>
          </button>
        </div>

        {/* 4 Nav Destinations */}
        <div className="flex flex-wrap gap-2 mt-6 pt-4 border-t border-white/15 text-xs font-medium">
          <button
            onClick={() => setActiveNav('portfolio')}
            className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
              activeNav === 'portfolio' ? 'bg-white text-[#17324D] font-bold shadow-xs' : 'text-slate-200 hover:text-white hover:bg-white/10'
            }`}
          >
            {t('admin_tab_portfolio')} ({studies.length})
          </button>
          <button
            onClick={() => setActiveNav('create')}
            className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
              activeNav === 'create' ? 'bg-white text-[#17324D] font-bold shadow-xs' : 'text-slate-200 hover:text-white hover:bg-white/10'
            }`}
          >
            {t('admin_tab_create')}
          </button>
          <button
            onClick={() => setActiveNav('settings')}
            className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
              activeNav === 'settings' ? 'bg-white text-[#17324D] font-bold shadow-xs' : 'text-slate-200 hover:text-white hover:bg-white/10'
            }`}
          >
            {t('admin_tab_settings')}
          </button>
          <button
            onClick={() => setActiveNav('audit')}
            className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
              activeNav === 'audit' ? 'bg-white text-[#17324D] font-bold shadow-xs' : 'text-slate-200 hover:text-white hover:bg-white/10'
            }`}
          >
            {t('admin_tab_audit')}
          </button>
        </div>
      </div>

      {/* Portfolio Overview */}
      {activeNav === 'portfolio' && (
        <div className="space-y-6">
          {/* Top KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-[#D9E2DC] shadow-xs">
              <span className="text-xs text-[#52616B] font-semibold block mb-1">{t('admin_total_studies')}</span>
              <span className="text-2xl font-bold text-[#172026]">{studies.length}</span>
              <span className="text-[11px] text-[#166534] font-medium block mt-1">{t('admin_kpi_facilities')}</span>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-[#D9E2DC] shadow-xs">
              <span className="text-xs text-[#52616B] font-semibold block mb-1">{t('admin_total_enrolled')}</span>
              <span className="text-2xl font-bold text-[#172026]">
                {studies.reduce((acc, s) => acc + (s.enrolled_count || 0), 0)}
              </span>
              <span className="text-[11px] text-[#52616B] block mt-1">
                {t('admin_kpi_target')}: {studies.reduce((acc, s) => acc + (s.enrollment_target || 0), 0)} {t('pi_subjects', 'subjects')}
              </span>
            </div>
            <div className="bg-white p-5 rounded-2xl border border-[#D9E2DC] shadow-xs">
              <span className="text-xs text-[#52616B] font-semibold block mb-1">{t('admin_compliance_rate')}</span>
              <span className="text-2xl font-bold text-[#166534]">100%</span>
              <span className="text-[11px] text-[#52616B] block mt-1">{t('admin_kpi_gates')}</span>
            </div>
          </div>

          {/* Studies Grid */}
          <div className="bg-white rounded-2xl border border-[#D9E2DC] shadow-xs overflow-hidden">
            <div className="p-4 bg-[#F7F8F5] border-b border-[#D9E2DC] font-bold text-xs text-[#17324D]">
              {t('admin_table_title')}
            </div>
            <div className="divide-y divide-[#D9E2DC]">
              {studies.map((s) => (
                <div key={s.id} className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs hover:bg-[#F7F8F5]">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-mono text-[10px] bg-[#F0F4F8] text-[#17324D] border border-[#D9E2DC] px-2 py-0.5 rounded font-bold">
                        {s.ctri_registration_number || 'CTRI: PENDING'}
                      </span>
                      <span className="font-bold text-[#172026]">{s.title}</span>
                    </div>
                    <div className="text-[11px] text-[#52616B] mt-0.5">
                      {t('admin_form_sponsor')}: {s.sponsor} | {t('admin_trial_phase')}: {s.phase} | {t('admin_form_site')}: {s.site_id || 'AIIA-01'}
                      {s.principal_investigator_id && (
                        <span> | {t('admin_form_pi')}: {investigators.find((pi) => pi.id === s.principal_investigator_id)?.name || s.principal_investigator_id.slice(0, 8)}</span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center space-x-3 shrink-0">
                    <div className="text-right">
                      <span className="font-bold text-[#172026]">{s.enrolled_count} / {s.enrollment_target} ({s.enrollment_percent}%)</span>
                      <div className="w-24 bg-[#E5EAE7] rounded-full h-1.5 mt-1 overflow-hidden">
                        <div className="bg-[#166534] h-1.5 rounded-full" style={{ width: `${s.enrollment_percent}%` }}></div>
                      </div>
                    </div>
                    {(s.status === 'iec_approved' || (s.iec_approval_status === 'approved' && s.ctri_status !== 'registered')) && (
                      <button
                        onClick={() => handleRegisterCtri(s.id)}
                        className="flex items-center space-x-1 bg-[#E68A00] hover:bg-[#D97706] text-white px-2.5 py-1 rounded-lg text-[10px] font-bold transition-all shadow-xs cursor-pointer"
                        title={t('admin_btn_register_ctri_tooltip', 'Register study on CTRI to unlock patient enrollment legal hard gate')}
                      >
                        <span>{t('admin_btn_register_ctri', 'Register CTRI')}</span>
                      </button>
                    )}
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${
                      s.status === 'iec_approved'
                        ? 'bg-[#EBF3ED] text-[#166534] border-[#C6DCCE]'
                        : s.status === 'actively_enrolling'
                        ? 'bg-[#EFF6FF] text-[#1D4ED8] border-[#BFDBFE]'
                        : s.status === 'completed'
                        ? 'bg-[#F3E8FF] text-[#7E22CE] border-[#E9D5FF]'
                        : s.status === 'pending_iec'
                        ? 'bg-[#FEF3C7] text-[#D97706] border-[#FDE68A]'
                        : s.status === 'iec_rejected'
                        ? 'bg-[#FEE2E2] text-[#C62828] border-[#FECACA]'
                        : 'bg-[#F0F4F8] text-[#17324D] border-[#D9E2DC]'
                    }`}>
                      {formatStatus(s.status)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Study Creation Form */}
      {activeNav === 'create' && (
        <div className="bg-white rounded-2xl border border-[#D9E2DC] p-6 shadow-xs max-w-xl mx-auto space-y-4">
          <div className="flex items-center space-x-2 text-[#17324D] font-bold mb-1">
            <PlusCircle className="w-5 h-5 text-[#166534]" />
            <h3 className="text-base">{t('admin_create_title')}</h3>
          </div>

          {msg && (
            <div className={`p-3 rounded-lg text-xs ${msg.includes('success') ? 'bg-[#EBF3ED] text-[#166534] border border-[#C6DCCE]' : 'bg-[#FEE2E2] text-[#C62828] border border-[#FECACA]'}`}>
              {msg}
            </div>
          )}

          <form onSubmit={handleCreateStudy} className="space-y-4 text-xs">
            <div>
              <label className="block font-semibold text-[#172026] mb-1">{t('admin_form_title')}</label>
              <textarea
                required
                rows={3}
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Enter complete investigation protocol title..."
                className="w-full rounded-lg border border-[#D9E2DC] p-2 text-xs shadow-xs focus:ring-1 focus:ring-[#166534] focus:border-[#166534] outline-none"
              />
            </div>

            <div>
              <label className="block font-semibold text-[#172026] mb-1">
                {t('admin_form_pi')} <span className="text-[#C62828]">*</span>
              </label>
              <select
                required
                value={selectedPiId}
                onChange={(e) => setSelectedPiId(e.target.value)}
                className="w-full rounded-lg border border-[#D9E2DC] p-2 text-xs shadow-xs focus:ring-1 focus:ring-[#166534] focus:border-[#166534] outline-none bg-white text-[#172026]"
              >
                {investigators.length === 0 ? (
                  <option value="">{t('admin_no_pi_available')}</option>
                ) : (
                  investigators.map((pi) => (
                    <option key={pi.id} value={pi.id}>
                      {pi.name} ({pi.email})
                    </option>
                  ))
                )}
              </select>
              <p className="text-[11px] text-[#52616B] mt-1">
                {t('admin_pi_helper')}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block font-semibold text-[#172026] mb-1">{t('admin_trial_phase')}</label>
                <select
                  value={phase}
                  onChange={(e) => setPhase(e.target.value)}
                  className="w-full rounded-lg border border-[#D9E2DC] p-2 text-xs shadow-xs focus:ring-1 focus:ring-[#166534] focus:border-[#166534] outline-none"
                >
                  <option value="Phase 1">Phase 1</option>
                  <option value="Phase 2">Phase 2</option>
                  <option value="Phase 3">Phase 3</option>
                  <option value="Phase 4">Phase 4</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-[#172026] mb-1">{t('admin_form_target')}</label>
                <input
                  type="number"
                  min={10}
                  value={target}
                  onChange={(e) => setTarget(e.target.value)}
                  className="w-full rounded-lg border border-[#D9E2DC] p-2 text-xs shadow-xs focus:ring-1 focus:ring-[#166534] focus:border-[#166534] outline-none"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block font-semibold text-[#172026] mb-1">{t('admin_form_sponsor')}</label>
                <input
                  type="text"
                  value={sponsor}
                  onChange={(e) => setSponsor(e.target.value)}
                  className="w-full rounded-lg border border-[#D9E2DC] p-2 text-xs shadow-xs focus:ring-1 focus:ring-[#166534] focus:border-[#166534] outline-none"
                />
              </div>
              <div>
                <label className="block font-semibold text-[#172026] mb-1">{t('admin_form_site')}</label>
                <input
                  type="text"
                  value={siteId}
                  onChange={(e) => setSiteId(e.target.value)}
                  className="w-full rounded-lg border border-[#D9E2DC] p-2 text-xs shadow-xs focus:ring-1 focus:ring-[#166534] focus:border-[#166534] outline-none"
                />
              </div>
            </div>

            <button
              type="submit"
              className="w-full bg-[#166534] hover:bg-[#14532D] text-white font-semibold py-2.5 rounded-xl transition-colors shadow-xs cursor-pointer"
            >
              {t('admin_btn_create')}
            </button>
          </form>
        </div>
      )}

      {/* Audit Trail Viewer */}
      {activeNav === 'audit' && (
        <div className="bg-white rounded-2xl border border-[#D9E2DC] shadow-xs overflow-hidden">
          <div className="p-4 bg-[#F7F8F5] border-b border-[#D9E2DC] font-bold text-xs text-[#17324D] flex justify-between items-center">
            <span>{t('admin_audit_title')}</span>
            <span className="text-[#52616B] font-normal">Most recent 40 events</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#F0F4F8] text-[#17324D] font-bold border-b border-[#D9E2DC]">
                <tr>
                  <th className="py-2.5 px-4">{t('reg_col_action')}</th>
                  <th className="py-2.5 px-4">{t('reg_col_entity')}</th>
                  <th className="py-2.5 px-4">{t('reg_col_timestamp')}</th>
                  <th className="py-2.5 px-4">{t('reg_col_curr_hash')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#D9E2DC] font-mono text-[11px]">
                {auditRows.map((r) => (
                  <tr key={r.id} className="hover:bg-[#F7F8F5]">
                    <td className="py-2.5 px-4 font-sans font-bold text-[#172026]">{r.action}</td>
                    <td className="py-2.5 px-4 font-sans capitalize text-[#172026]">{r.entity_type}</td>
                    <td className="py-2.5 px-4 text-[#52616B] font-sans">{r.timestamp?.slice(0, 19).replace('T', ' ')}</td>
                    <td className="py-2.5 px-4 text-[#166534]">{r.row_hash?.slice(0, 24)}...</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Settings */}
      {activeNav === 'settings' && (
        <div className="bg-white rounded-2xl border border-[#D9E2DC] p-6 shadow-xs space-y-4 text-xs">
          <h3 className="text-base font-bold text-[#172026]">{t('admin_governance_title')}</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-[#F7F8F5] border border-[#D9E2DC] rounded-xl space-y-2">
              <h4 className="font-bold text-[#17324D]">{t('admin_rbac_title')}</h4>
              <p className="text-[#52616B] text-[11px]">
                {t('admin_rbac_desc')}
              </p>
            </div>
            <div className="p-4 bg-[#F7F8F5] border border-[#D9E2DC] rounded-xl space-y-2">
              <h4 className="font-bold text-[#17324D]">{t('admin_anchor_engine_title')}</h4>
              <p className="text-[#52616B] text-[11px]">
                {t('admin_anchor_engine_desc')}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
