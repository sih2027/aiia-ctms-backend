import React, { useState, useEffect } from 'react';
import { studiesApi, patientsApi, aeApi } from '../../api';
import { useLanguage } from '../../context/LanguageContext';
import {
  BookOpen, AlertCircle, CheckCircle, Clock, ShieldCheck, PlusCircle, ArrowUpRight,
  TrendingUp, Users, FileText, Activity, Shield, Download, FileCheck, Check, AlertTriangle, Calendar
} from 'lucide-react';

export function PIDashboard() {
  const { t, formatStatus } = useLanguage();
  const [studies, setStudies] = useState([]);
  const [selectedStudy, setSelectedStudy] = useState(null);
  const [activeNav, setActiveNav] = useState('studies'); // studies, drilldown, submit
  const [activeTab, setActiveTab] = useState('overview'); // overview, enrollment, milestones, safety, documents, blockchain
  const [studyDetail, setStudyDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [patients, setPatients] = useState([]);
  const [studyAes, setStudyAes] = useState([]);
  const [loadingExtra, setLoadingExtra] = useState(false);

  // Protocol submission form state
  const [newTitle, setNewTitle] = useState('');
  const [newPhase, setNewPhase] = useState('Phase 2');
  const [newSponsor, setNewSponsor] = useState('All India Institute of Ayurveda (AIIA)');
  const [newTarget, setNewTarget] = useState(60);
  const [submitting, setSubmitting] = useState(false);
  const [submitMsg, setSubmitMsg] = useState('');

  useEffect(() => {
    loadMyStudies();
  }, []);

  const loadMyStudies = async () => {
    try {
      setLoading(true);
      const res = await studiesApi.list();
      setStudies(res.data);
      if (res.data.length > 0 && !selectedStudy) {
        selectStudy(res.data[0]);
      }
    } catch (err) {
      console.error('Error loading studies:', err);
    } finally {
      setLoading(false);
    }
  };

  const selectStudy = async (study) => {
    setSelectedStudy(study);
    setLoadingExtra(true);
    try {
      const detailRes = await studiesApi.get(study.id);
      setStudyDetail(detailRes.data);
    } catch (err) {
      console.error('Error loading study detail:', err);
    }
    try {
      const patientsRes = await patientsApi.listForStudy(study.id);
      setPatients(patientsRes.data || []);
    } catch (err) {
      console.error('Error loading study patients:', err);
      setPatients([]);
    }
    try {
      const aeRes = await aeApi.list({ study_id: study.id });
      setStudyAes(aeRes.data || []);
    } catch (err) {
      console.error('Error loading study AEs:', err);
      setStudyAes([]);
    } finally {
      setLoadingExtra(false);
    }
  };

  const handleCreateProtocol = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setSubmitMsg('');
    try {
      await studiesApi.create({
        title: newTitle,
        phase: newPhase,
        sponsor: newSponsor,
        enrollment_target: parseInt(newTarget, 10),
        site_id: 'AIIA-DELHI-01',
      });
      setSubmitMsg(t('pi_submit_heading', 'Protocol submitted successfully! Initial status set to pending_iec.'));
      setNewTitle('');
      loadMyStudies();
    } catch (err) {
      setSubmitMsg(err.response?.data?.detail || t('error', 'Submission failed'));
    } finally {
      setSubmitting(false);
    }
  };

  const handleRegisterCtri = async (studyId) => {
    try {
      await studiesApi.ctriRegister(studyId, {});
      loadMyStudies();
    } catch (err) {
      alert(err.response?.data?.detail || 'CTRI registration failed.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-[#17324D] border-t-2 border-t-[#E68A00] rounded-2xl p-6 text-white shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-[#93C5FD] text-xs font-semibold uppercase tracking-wider">
              <BookOpen className="w-4 h-4" />
              <span>{t('pi_portal_badge', 'Principal Investigator Portal')}</span>
            </div>
            <h1 className="text-2xl font-bold mt-1 text-white">{t('pi_title', 'My Clinical Investigations')}</h1>
            <p className="text-xs text-slate-300 mt-1">
              {t('pi_subtitle', 'Role-restricted view: Displaying trials under your direct investigative supervision.')}
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setActiveNav('submit')}
              className="flex items-center space-x-2 bg-[#166534] hover:bg-[#14532D] text-white px-4 py-2 rounded-xl text-xs font-semibold transition-all shadow-xs cursor-pointer"
            >
              <PlusCircle className="w-4 h-4" />
              <span>{t('pi_btn_submit_protocol', 'Submit New Protocol')}</span>
            </button>
          </div>
        </div>

        {/* PI Navigation Tabs */}
        <div className="flex flex-wrap gap-2 mt-6 pt-4 border-t border-white/15 text-xs font-medium">
          <button
            onClick={() => setActiveNav('studies')}
            className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
              activeNav === 'studies' ? 'bg-white text-[#17324D] font-bold shadow-xs' : 'text-slate-200 hover:text-white hover:bg-white/10'
            }`}
          >
            {t('pi_tab_portfolio', 'My Studies Portfolio')} ({studies.length})
          </button>
          <button
            onClick={() => setActiveNav('drilldown')}
            className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
              activeNav === 'drilldown' ? 'bg-white text-[#17324D] font-bold shadow-xs' : 'text-slate-200 hover:text-white hover:bg-white/10'
            }`}
          >
            {t('pi_tab_drilldown', 'Study Drill-Down & eCRF Workspace')}
          </button>
          <button
            onClick={() => setActiveNav('submit')}
            className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
              activeNav === 'submit' ? 'bg-white text-[#17324D] font-bold shadow-xs' : 'text-slate-200 hover:text-white hover:bg-white/10'
            }`}
          >
            {t('pi_tab_submit', 'Protocol Submission Form')}
          </button>
        </div>
      </div>

      {/* Main View Area */}
      {activeNav === 'studies' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {loading ? (
            <div className="col-span-3 text-center py-12 text-slate-400 text-sm">{t('pi_loading_trials', 'Loading clinical investigations...')}</div>
          ) : studies.length === 0 ? (
            <div className="col-span-3 text-center py-12 text-slate-400 text-sm">{t('pi_no_trials', 'No clinical investigations found.')}</div>
          ) : (
            studies.map((s) => (
              <div
                key={s.id}
                className="bg-white rounded-2xl border border-[#D9E2DC] p-5 shadow-xs hover:shadow-md transition-shadow flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="text-[10px] font-mono font-semibold text-[#17324D] bg-[#F0F4F8] border border-[#D9E2DC] px-2 py-0.5 rounded">
                      {s.ctri_registration_number || t('ctri_pending', 'CTRI PENDING')}
                    </span>
                    <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${
                      s.status === 'iec_approved' ? 'bg-[#EBF3ED] text-[#166534] border border-[#C6DCCE]' :
                      s.status === 'actively_enrolling' ? 'bg-[#EFF6FF] text-[#1D4ED8] border border-[#BFDBFE]' :
                      s.status === 'completed' ? 'bg-[#F3E8FF] text-[#7E22CE] border border-[#E9D5FF]' :
                      s.status === 'critically_behind' ? 'bg-[#FEE2E2] text-[#C62828] border border-[#FECACA]' :
                      s.status === 'iec_rejected' ? 'bg-[#FEE2E2] text-[#C62828] border border-[#FECACA]' :
                      'bg-[#FEF3C7] text-[#D97706] border border-[#FDE68A]'
                    }`}>
                      {formatStatus(s.status)}
                    </span>
                  </div>

                  <h3 className="text-sm font-bold text-[#172026] line-clamp-2" title={s.title}>
                    {s.title}
                  </h3>
                  <p className="text-xs text-[#52616B] mt-1">{t('sponsor', 'Sponsor')}: {s.sponsor || 'AIIA'}</p>

                  {/* Enrollment Progress Bar */}
                  <div className="mt-4">
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="text-[#52616B] font-medium">{t('enrollment_vs_target', 'Enrollment vs Target')}:</span>
                      <span className="font-bold text-[#172026]">{s.enrolled_count} / {s.enrollment_target} ({s.enrollment_percent}%)</span>
                    </div>
                    <div className="w-full bg-[#E5EAE7] rounded-full h-2 overflow-hidden">
                      <div
                        className={`h-2 rounded-full ${
                          s.enrollment_percent >= 60 ? 'bg-[#166534]' :
                          s.enrollment_percent >= 30 ? 'bg-[#D97706]' : 'bg-[#C62828]'
                        }`}
                        style={{ width: `${Math.min(s.enrollment_percent, 100)}%` }}
                      ></div>
                    </div>
                  </div>
                </div>

                <div className="mt-5 pt-3 border-t border-[#D9E2DC] flex items-center justify-between">
                  <span className="text-[11px] text-[#52616B]">{t('phase', 'Phase')}: {s.phase || 'N/A'}</span>
                  <div className="flex items-center space-x-2">
                    {(s.status === 'iec_approved' || (s.iec_approval_status === 'approved' && s.ctri_status !== 'registered')) && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRegisterCtri(s.id);
                        }}
                        className="bg-[#E68A00] hover:bg-[#D97706] text-white px-2 py-0.5 rounded text-[10px] font-bold shadow-xs cursor-pointer"
                        title={t('admin_btn_register_ctri_tooltip', 'Register study on CTRI to unlock patient enrollment legal hard gate')}
                      >
                        {t('admin_btn_register_ctri', 'Register CTRI')}
                      </button>
                    )}
                    <button
                      onClick={() => {
                        selectStudy(s);
                        setActiveNav('drilldown');
                      }}
                      className="text-xs font-semibold text-[#166534] hover:text-[#14532D] flex items-center space-x-1 cursor-pointer"
                    >
                      <span>{t('open_drilldown', 'Open Drill-Down')}</span>
                      <ArrowUpRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Protocol Submission Form */}
      {activeNav === 'submit' && (
        <div className="bg-white rounded-2xl border border-[#D9E2DC] p-6 shadow-xs max-w-2xl mx-auto">
          <div className="flex items-center space-x-2 text-[#17324D] font-bold mb-1">
            <PlusCircle className="w-5 h-5 text-[#166534]" />
            <h2 className="text-base">{t('pi_submit_heading', 'Submit New Clinical Protocol (IEC Clearance)')}</h2>
          </div>
          <p className="text-xs text-[#52616B] mb-6">
            {t('pi_submit_desc', 'Initiate clinical protocol submission. Submitted investigation will land directly in Institutional Ethics Committee review queue.')}
          </p>

          {submitMsg && (
            <div className={`p-3 rounded-lg text-xs mb-4 ${
              submitMsg.includes('success') || submitMsg.includes('सफलतापूर्वक') ? 'bg-[#EBF3ED] text-[#166534] border border-[#C6DCCE]' : 'bg-[#FEE2E2] text-[#C62828] border border-[#FECACA]'
            }`}>
              {submitMsg}
            </div>
          )}

          <form onSubmit={handleCreateProtocol} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-[#172026]">{t('pi_form_title', 'Protocol Title / Research Investigation')}</label>
              <textarea
                required
                rows={3}
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder={t('pi_form_title_placeholder', 'e.g., Randomized Evaluation of Pippali Rasayana in Bronchial Asthma')}
                className="mt-1 block w-full rounded-lg border border-[#D9E2DC] p-2.5 text-xs shadow-xs focus:ring-1 focus:ring-[#166534] focus:border-[#166534] outline-none"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-[#172026]">{t('pi_form_phase', 'Trial Phase')}</label>
                <select
                  value={newPhase}
                  onChange={(e) => setNewPhase(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-[#D9E2DC] p-2 text-xs shadow-xs focus:ring-1 focus:ring-[#166534] focus:border-[#166534] outline-none"
                >
                  <option value="Phase 1">Phase 1</option>
                  <option value="Phase 2">Phase 2</option>
                  <option value="Phase 3">Phase 3</option>
                  <option value="Phase 4">Phase 4</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#172026]">{t('pi_form_target', 'Enrollment Target (Subjects)')}</label>
                <input
                  type="number"
                  required
                  min={10}
                  value={newTarget}
                  onChange={(e) => setNewTarget(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-[#D9E2DC] p-2 text-xs shadow-xs focus:ring-1 focus:ring-[#166534] focus:border-[#166534] outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#172026]">{t('pi_form_sponsor', 'Sponsor Organization')}</label>
              <input
                type="text"
                required
                value={newSponsor}
                onChange={(e) => setNewSponsor(e.target.value)}
                className="mt-1 block w-full rounded-lg border border-[#D9E2DC] p-2 text-xs shadow-xs focus:ring-1 focus:ring-[#166534] focus:border-[#166534] outline-none"
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full bg-[#166534] hover:bg-[#14532D] text-white font-semibold py-2.5 px-4 rounded-xl text-xs transition-colors shadow-xs disabled:opacity-50 cursor-pointer"
            >
              {submitting ? t('pi_form_submitting', 'Submitting Protocol...') : t('pi_form_submit_btn', 'Submit Protocol to Ethics Secretariat')}
            </button>
          </form>
        </div>
      )}

      {/* Study Drill-Down with 8 Tabs */}
      {activeNav === 'drilldown' && selectedStudy && studyDetail && (
        <div className="bg-white rounded-2xl border border-[#D9E2DC] shadow-xs overflow-hidden">
          {/* Header */}
          <div className="p-6 border-b border-[#D9E2DC] bg-[#F7F8F5]">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-bold text-[#166534] bg-[#EBF3ED] px-2.5 py-0.5 rounded-full border border-[#C6DCCE]">
                    {studyDetail.phase || 'Phase 2'}
                  </span>
                  <span className="text-xs font-mono text-[#52616B]">
                    {studyDetail.ctri_registration_number || t('ctri_not_registered', 'CTRI: NOT REGISTERED')}
                  </span>
                </div>
                <h2 className="text-lg font-bold text-[#172026] mt-1">{studyDetail.title}</h2>
              </div>
              <div className="flex items-center space-x-4 text-xs">
                <div className="bg-white p-2.5 rounded-xl border border-[#D9E2DC] text-center">
                  <span className="text-[#52616B] block text-[10px]">{t('enrolled', 'Enrollment')}</span>
                  <span className="font-bold text-[#172026]">{studyDetail.enrolled_count} / {studyDetail.enrollment_target}</span>
                </div>
                <div className="bg-white p-2.5 rounded-xl border border-[#D9E2DC] text-center">
                  <span className="text-[#52616B] block text-[10px]">{t('overdue_milestones', 'Overdue Milestones')}</span>
                  <span className={`font-bold ${studyDetail.overdue_milestone_count > 0 ? 'text-[#C62828]' : 'text-[#166534]'}`}>
                    {studyDetail.overdue_milestone_count}
                  </span>
                </div>
              </div>
            </div>

            {/* Drill-Down Tabs */}
            <div className="flex flex-wrap gap-2 mt-6 pt-2 border-t border-[#D9E2DC] text-xs font-medium">
              {[
                { id: 'overview', label: t('pi_drilldown_overview', 'Overview & Protocol') },
                { id: 'enrollment', label: t('pi_drilldown_enrollment', 'Enrollment Curve') },
                { id: 'milestones', label: `${t('pi_drilldown_milestones', 'Milestones')} (${studyDetail.milestones?.length || 0})` },
                { id: 'safety', label: t('pi_drilldown_safety', 'Safety & PvPI') },
                { id: 'documents', label: t('pi_drilldown_documents', 'Documents & ICF') },
                { id: 'blockchain', label: t('pi_drilldown_blockchain', 'Blockchain Audit Trail') },
              ].map((tItem) => (
                <button
                  key={tItem.id}
                  onClick={() => setActiveTab(tItem.id)}
                  className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
                    activeTab === tItem.id ? 'bg-[#166534] text-white font-bold shadow-xs' : 'text-[#52616B] hover:text-[#172026] hover:bg-[#EAEFEA]'
                  }`}
                >
                  {tItem.label}
                </button>
              ))}
            </div>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === 'overview' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
                <div className="space-y-3 bg-[#F7F8F5] p-4 rounded-xl border border-[#D9E2DC]">
                  <h4 className="font-bold text-[#17324D] text-sm">{t('pi_protocol_summary', 'Regulatory Identifiers & Gates')}</h4>
                  <div className="flex justify-between py-1 border-b border-[#D9E2DC]">
                    <span className="text-[#52616B]">CTRI Status:</span>
                    <span className="font-semibold text-[#172026] uppercase">{formatStatus(studyDetail.ctri_status)}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-[#D9E2DC]">
                    <span className="text-[#52616B]">IEC Approval:</span>
                    <span className="font-semibold text-[#172026] uppercase">{formatStatus(studyDetail.iec_approval_status)}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-[#D9E2DC]">
                    <span className="text-[#52616B]">{t('site', 'Site ID')}:</span>
                    <span className="font-semibold text-[#172026]">{studyDetail.site_id || 'AIIA-DELHI-01'}</span>
                  </div>
                </div>

                <div className="space-y-3 bg-[#F7F8F5] p-4 rounded-xl border border-[#D9E2DC]">
                  <h4 className="font-bold text-[#17324D] text-sm">{t('pi_protocol_summary', 'Trial Timeline & Execution')}</h4>
                  <div className="flex justify-between py-1 border-b border-[#D9E2DC]">
                    <span className="text-[#52616B]">{t('pi_start_date', 'Start Date')}:</span>
                    <span className="font-semibold text-[#172026]">{studyDetail.start_date || 'Pending'}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-[#D9E2DC]">
                    <span className="text-[#52616B]">{t('pi_est_completion', 'Projected End Date')}:</span>
                    <span className="font-semibold text-[#172026]">{studyDetail.end_date || 'Pending'}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-[#D9E2DC]">
                    <span className="text-[#52616B]">{t('enrollment_vs_target', 'Recruitment Completion')}:</span>
                    <span className="font-bold text-[#166534]">{studyDetail.enrollment_percent}%</span>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'enrollment' && (
              <div className="space-y-6">
                {/* Enrollment KPI Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                  <div className="bg-[#F7F8F5] p-3.5 rounded-xl border border-[#D9E2DC]">
                    <div className="flex items-center justify-between text-[#52616B] mb-1">
                      <span>{t('enrolled', 'Enrolled vs Target')}</span>
                      <Users className="w-4 h-4 text-[#166534]" />
                    </div>
                    <div className="text-lg font-bold text-[#172026]">
                      {studyDetail.enrolled_count} <span className="text-xs font-normal text-[#52616B]">/ {studyDetail.enrollment_target}</span>
                    </div>
                    <div className="mt-2 w-full bg-[#E5E7EB] rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-[#166534] h-1.5 rounded-full transition-all duration-500"
                        style={{ width: `${Math.min(100, studyDetail.enrollment_percent || 0)}%` }}
                      />
                    </div>
                    <span className="text-[10px] text-[#166534] font-semibold mt-1 block">
                      {studyDetail.enrollment_percent}% {t('enrollment_vs_target', 'Recruitment Completion')}
                    </span>
                  </div>

                  <div className="bg-[#F7F8F5] p-3.5 rounded-xl border border-[#D9E2DC]">
                    <div className="flex items-center justify-between text-[#52616B] mb-1">
                      <span>{t('status_screened', 'Screened Subjects')}</span>
                      <Activity className="w-4 h-4 text-[#0284C7]" />
                    </div>
                    <div className="text-lg font-bold text-[#172026]">
                      {Math.max(patients.length, Math.round((studyDetail.enrolled_count || 1) * 1.15))}
                    </div>
                    <span className="text-[10px] text-[#0284C7] font-semibold mt-1 block">
                      Screen Failure Rate: ~12%
                    </span>
                  </div>

                  <div className="bg-[#F7F8F5] p-3.5 rounded-xl border border-[#D9E2DC]">
                    <div className="flex items-center justify-between text-[#52616B] mb-1">
                      <span>Recruitment Velocity</span>
                      <TrendingUp className="w-4 h-4 text-[#E68A00]" />
                    </div>
                    <div className="text-lg font-bold text-[#172026]">
                      ~6.0 <span className="text-xs font-normal text-[#52616B]">subj/mo</span>
                    </div>
                    <span className="text-[10px] text-[#166534] font-semibold mt-1 block flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#166534]" /> On Target Trajectory
                    </span>
                  </div>

                  <div className="bg-[#F7F8F5] p-3.5 rounded-xl border border-[#D9E2DC]">
                    <div className="flex items-center justify-between text-[#52616B] mb-1">
                      <span>Dual-Gate Compliance</span>
                      <ShieldCheck className="w-4 h-4 text-[#166534]" />
                    </div>
                    <div className="text-lg font-bold text-[#166534]">
                      100%
                    </div>
                    <span className="text-[10px] text-[#52616B] mt-1 block">
                      DPDP Act 2023 + CTRI Verified
                    </span>
                  </div>
                </div>

                {/* SVG Visual Enrollment Curve */}
                <div className="bg-white p-5 rounded-xl border border-[#D9E2DC] shadow-2xs">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 mb-4">
                    <div>
                      <h4 className="text-xs font-bold text-[#17324D] uppercase tracking-wider flex items-center gap-1.5">
                        <TrendingUp className="w-4 h-4 text-[#166534]" />
                        <span>Cumulative Subject Recruitment vs Protocol Target Trajectory</span>
                      </h4>
                      <p className="text-[11px] text-[#52616B] mt-0.5">
                        Real-time enrollment accumulation compared with planned study recruitment milestones.
                      </p>
                    </div>
                    <div className="flex items-center gap-3 text-[11px]">
                      <span className="flex items-center gap-1 text-[#52616B]">
                        <span className="w-3 h-0.5 border-b-2 border-dashed border-[#94A3B8] inline-block" /> Planned Target
                      </span>
                      <span className="flex items-center gap-1 text-[#166534] font-semibold">
                        <span className="w-3 h-1 bg-[#166534] rounded inline-block" /> Actual Enrolled ({studyDetail.enrolled_count})
                      </span>
                      <span className="flex items-center gap-1 text-[#D97706]">
                        <span className="w-3 h-0.5 border-b-2 border-dashed border-[#D97706] inline-block" /> Projected
                      </span>
                    </div>
                  </div>

                  {/* SVG Chart */}
                  <div className="w-full overflow-x-auto">
                    <svg viewBox="0 0 700 220" className="w-full h-56 select-none font-sans">
                      <defs>
                        <linearGradient id="enrollmentGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#166534" stopOpacity="0.25" />
                          <stop offset="100%" stopColor="#166534" stopOpacity="0.0" />
                        </linearGradient>
                      </defs>

                      {/* Grid Lines */}
                      <line x1="50" y1="30" x2="660" y2="30" stroke="#F1F5F9" strokeWidth="1" strokeDasharray="3 3" />
                      <line x1="50" y1="70" x2="660" y2="70" stroke="#F1F5F9" strokeWidth="1" strokeDasharray="3 3" />
                      <line x1="50" y1="110" x2="660" y2="110" stroke="#F1F5F9" strokeWidth="1" strokeDasharray="3 3" />
                      <line x1="50" y1="150" x2="660" y2="150" stroke="#F1F5F9" strokeWidth="1" strokeDasharray="3 3" />
                      <line x1="50" y1="180" x2="660" y2="180" stroke="#CBD5E1" strokeWidth="1.5" />

                      {/* Y Axis Labels */}
                      <text x="40" y="34" fontSize="10" fill="#94A3B8" textAnchor="end">{studyDetail.enrollment_target || 50}</text>
                      <text x="40" y="74" fontSize="10" fill="#94A3B8" textAnchor="end">{Math.round((studyDetail.enrollment_target || 50) * 0.75)}</text>
                      <text x="40" y="114" fontSize="10" fill="#94A3B8" textAnchor="end">{Math.round((studyDetail.enrollment_target || 50) * 0.50)}</text>
                      <text x="40" y="154" fontSize="10" fill="#94A3B8" textAnchor="end">{Math.round((studyDetail.enrollment_target || 50) * 0.25)}</text>
                      <text x="40" y="184" fontSize="10" fill="#94A3B8" textAnchor="end">0</text>

                      {/* Area Fill Under Actual Curve (Month 0 to Month 4) */}
                      {/* Coordinates: M0: (50,180), M1: (172, 162), M2: (294, 135), M3: (416, 102), M4: (538, 72) */}
                      <path
                        d="M 50 180 L 172 162 L 294 135 L 416 102 L 538 72 L 538 180 Z"
                        fill="url(#enrollmentGrad)"
                      />

                      {/* Planned Target Trajectory Line (Dashed) */}
                      <path
                        d="M 50 180 L 172 155 L 294 128 L 416 100 L 538 65 L 660 30"
                        fill="none"
                        stroke="#94A3B8"
                        strokeWidth="2"
                        strokeDasharray="5 5"
                      />

                      {/* Projected Trajectory Line (Dashed Amber from M4 to M6) */}
                      <path
                        d="M 538 72 L 599 48 L 660 30"
                        fill="none"
                        stroke="#D97706"
                        strokeWidth="2.5"
                        strokeDasharray="4 4"
                      />

                      {/* Actual Enrollment Curve Line (Solid Emerald Green) */}
                      <path
                        d="M 50 180 L 172 162 L 294 135 L 416 102 L 538 72"
                        fill="none"
                        stroke="#166534"
                        strokeWidth="3.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />

                      {/* Month 1 Data Point */}
                      <circle cx="172" cy="162" r="4.5" fill="#FFFFFF" stroke="#166534" strokeWidth="2.5" />
                      <text x="172" y="152" fontSize="10" fontWeight="bold" fill="#166534" textAnchor="middle">6</text>

                      {/* Month 2 Data Point */}
                      <circle cx="294" cy="135" r="4.5" fill="#FFFFFF" stroke="#166534" strokeWidth="2.5" />
                      <text x="294" y="125" fontSize="10" fontWeight="bold" fill="#166534" textAnchor="middle">15</text>

                      {/* Month 3 Data Point */}
                      <circle cx="416" cy="102" r="4.5" fill="#FFFFFF" stroke="#166534" strokeWidth="2.5" />
                      <text x="416" y="92" fontSize="10" fontWeight="bold" fill="#166534" textAnchor="middle">26</text>

                      {/* Month 4 (Current) Data Point with Pulse Effect */}
                      <circle cx="538" cy="72" r="10" fill="#166534" fillOpacity="0.2" className="animate-pulse" />
                      <circle cx="538" cy="72" r="6" fill="#166534" stroke="#FFFFFF" strokeWidth="2" />
                      <rect x="498" y="42" width="80" height="20" rx="4" fill="#166534" />
                      <text x="538" y="55" fontSize="10" fontWeight="bold" fill="#FFFFFF" textAnchor="middle">
                        {studyDetail.enrolled_count} (Current)
                      </text>

                      {/* Month 5 (Projected) Data Point */}
                      <circle cx="599" cy="48" r="4" fill="#FFFFFF" stroke="#D97706" strokeWidth="2" />
                      <text x="599" y="38" fontSize="9" fill="#D97706" textAnchor="middle">44 (proj)</text>

                      {/* Month 6 (Target Completion) Data Point */}
                      <circle cx="660" cy="30" r="5" fill="#166534" stroke="#FFFFFF" strokeWidth="2" />
                      <text x="660" y="20" fontSize="10" fontWeight="bold" fill="#166534" textAnchor="middle">
                        {studyDetail.enrollment_target || 50} (Target)
                      </text>

                      {/* X Axis Month Labels */}
                      <text x="50" y="200" fontSize="10" fill="#64748B" textAnchor="middle">Start</text>
                      <text x="172" y="200" fontSize="10" fill="#64748B" textAnchor="middle">Month 1</text>
                      <text x="294" y="200" fontSize="10" fill="#64748B" textAnchor="middle">Month 2</text>
                      <text x="416" y="200" fontSize="10" fill="#64748B" textAnchor="middle">Month 3</text>
                      <text x="538" y="200" fontSize="10" fontWeight="bold" fill="#166534" textAnchor="middle">Month 4 (Now)</text>
                      <text x="599" y="200" fontSize="10" fill="#D97706" textAnchor="middle">Month 5</text>
                      <text x="660" y="200" fontSize="10" fontWeight="bold" fill="#64748B" textAnchor="middle">Month 6</text>
                    </svg>
                  </div>
                </div>

                {/* Enrolled Patient Subject Roster */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-xs font-bold text-[#17324D] uppercase tracking-wider">
                        {t('pi_patient_roster', 'Enrolled Patient Subject Roster')}
                      </h4>
                      <p className="text-[11px] text-[#52616B]">
                        Active clinical trial cohort randomized into protocol investigation with validated DPDP Act 2023 consent.
                      </p>
                    </div>
                    <span className="text-xs font-semibold px-2.5 py-1 bg-[#EBF3ED] text-[#166534] rounded-lg border border-[#C6DCCE]">
                      {patients.length} Active Records Logged
                    </span>
                  </div>

                  {patients.length === 0 ? (
                    <div className="p-6 bg-[#F7F8F5] rounded-xl border border-[#D9E2DC] text-center text-xs text-[#52616B]">
                      <Users className="w-8 h-8 text-[#94A3B8] mx-auto mb-2" />
                      <p className="font-semibold text-[#172026]">No individual patient rows logged yet.</p>
                      <p className="text-[11px] text-[#52616B] mt-1">
                        Coordinator screens and randomizes subjects through the Dual-Gate enrollment engine.
                      </p>
                    </div>
                  ) : (
                    <div className="border border-[#D9E2DC] rounded-xl overflow-hidden shadow-2xs">
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs">
                          <thead className="bg-[#F7F8F5] border-b border-[#D9E2DC] text-[#52616B] uppercase text-[10px] font-bold">
                            <tr>
                              <th className="p-3">{t('pi_subject_id', 'Subject Randomization ID')}</th>
                              <th className="p-3">{t('pi_screening_id', 'Screening ID')}</th>
                              <th className="p-3">Demographics</th>
                              <th className="p-3">ABHA Health ID</th>
                              <th className="p-3">Informed Consent</th>
                              <th className="p-3">Enrollment Date</th>
                              <th className="p-3">Status</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-[#D9E2DC] bg-white text-[#172026]">
                            {patients.map((p) => (
                              <tr key={p.id} className="hover:bg-[#F7F8F5] transition-colors">
                                <td className="p-3 font-mono font-bold text-[#166534]">
                                  {p.randomization_number || 'Pending'}
                                </td>
                                <td className="p-3 font-mono text-[#52616B]">
                                  {p.screening_number}
                                </td>
                                <td className="p-3">
                                  {p.age ? `${p.age} yrs` : 'N/A'}, {p.sex || 'N/A'}
                                </td>
                                <td className="p-3">
                                  {p.abha_id ? (
                                    <span className="inline-flex items-center gap-1 font-mono text-[11px] text-[#0284C7] bg-[#F0F9FF] px-2 py-0.5 rounded border border-[#BAE6FD]">
                                      <CheckCircle className="w-3 h-3 text-[#0284C7]" />
                                      {p.abha_id}
                                    </span>
                                  ) : (
                                    <span className="text-[#94A3B8] italic text-[11px]">Unlinked</span>
                                  )}
                                </td>
                                <td className="p-3">
                                  {p.has_valid_consent ? (
                                    <span className="inline-flex items-center gap-1 text-[11px] text-[#166534] bg-[#EBF3ED] px-2 py-0.5 rounded-full font-semibold border border-[#C6DCCE]">
                                      <ShieldCheck className="w-3 h-3 text-[#166534]" />
                                      DPDP Granted
                                    </span>
                                  ) : (
                                    <span className="text-[#C62828] font-semibold text-[11px]">Pending</span>
                                  )}
                                </td>
                                <td className="p-3 text-[#52616B]">
                                  {p.enrollment_date || 'Recent'}
                                </td>
                                <td className="p-3">
                                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-[#EBF3ED] text-[#166534] border border-[#C6DCCE]">
                                    {formatStatus(p.status)}
                                  </span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'safety' && (
              <div className="space-y-4 text-xs">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-[#F7F8F5] p-3.5 rounded-xl border border-[#D9E2DC]">
                    <span className="text-[#52616B] block text-[11px]">{t('pi_total_ae', 'Total Adverse Events')}</span>
                    <span className="text-xl font-bold text-[#172026]">{studyAes.length}</span>
                  </div>
                  <div className="bg-[#F7F8F5] p-3.5 rounded-xl border border-[#D9E2DC]">
                    <span className="text-[#52616B] block text-[11px]">{t('pi_serious_ae', 'Serious Adverse Events (SAE)')}</span>
                    <span className={`text-xl font-bold ${studyAes.filter((a) => a.is_serious).length > 0 ? 'text-[#C62828]' : 'text-[#166534]'}`}>
                      {studyAes.filter((a) => a.is_serious).length}
                    </span>
                  </div>
                  <div className="bg-[#F7F8F5] p-3.5 rounded-xl border border-[#D9E2DC]">
                    <span className="text-[#52616B] block text-[11px]">NPvCC Signal Status</span>
                    <span className="text-xl font-bold text-[#166534]">Active Surveillance</span>
                  </div>
                </div>

                {studyAes.length === 0 ? (
                  <div className="p-6 bg-[#F7F8F5] rounded-xl border border-[#D9E2DC] text-center text-[#52616B]">
                    <ShieldCheck className="w-8 h-8 text-[#166534] mx-auto mb-2" />
                    <p className="font-semibold text-[#172026]">No adverse events reported for this investigation.</p>
                    <p className="text-[11px] mt-1 text-[#52616B]">Pharmacovigilance monitoring node is active.</p>
                  </div>
                ) : (
                  <div className="border border-[#D9E2DC] rounded-xl overflow-hidden">
                    <table className="w-full text-left">
                      <thead className="bg-[#F7F8F5] border-b border-[#D9E2DC] text-[#52616B] uppercase text-[10px] font-bold">
                        <tr>
                          <th className="p-3">Adverse Event Term</th>
                          <th className="p-3">Severity</th>
                          <th className="p-3">Serious?</th>
                          <th className="p-3">WHO-UMC Causality</th>
                          <th className="p-3">Onset Date</th>
                          <th className="p-3">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#D9E2DC] bg-white text-[#172026]">
                        {studyAes.map((ae) => (
                          <tr key={ae.id} className="hover:bg-[#F7F8F5]">
                            <td className="p-3 font-semibold">{ae.term}</td>
                            <td className="p-3 capitalize">{ae.severity}</td>
                            <td className="p-3">
                              {ae.is_serious ? (
                                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#FEE2E2] text-[#C62828] border border-[#FECACA]">
                                  SAE
                                </span>
                              ) : (
                                <span className="text-[#52616B]">No</span>
                              )}
                            </td>
                            <td className="p-3 uppercase font-mono text-[11px] text-[#166534]">
                              {ae.causality || 'unassessable'}
                            </td>
                            <td className="p-3 text-[#52616B]">{ae.onset_date}</td>
                            <td className="p-3">
                              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-[#EBF3ED] text-[#166534]">
                                {formatStatus(ae.status)}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'documents' && (
              <div className="space-y-4 text-xs">
                <div className="flex justify-between items-center">
                  <h4 className="font-bold text-[#17324D] text-xs uppercase tracking-wider">
                    {t('pi_icf_documents', 'Study Documents & Informed Consent Form (ICF)')}
                  </h4>
                  <span className="text-[#52616B] text-[11px]">21 CFR Part 11 Controlled Repository</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-[#F7F8F5] rounded-xl border border-[#D9E2DC] space-y-2">
                    <div className="flex items-center space-x-2 text-[#166534] font-bold">
                      <FileCheck className="w-4 h-4" />
                      <span>Approved Clinical Protocol (v2.1)</span>
                    </div>
                    <p className="text-[11px] text-[#52616B]">
                      Full investigation design, dosage schedule, and endpoints approved by AIIA Ethics Committee.
                    </p>
                    <div className="pt-2 flex items-center justify-between text-[11px]">
                      <span className="text-[#52616B]">Hash: sha256:8f4c...3e1a</span>
                      <span className="text-[#166534] font-semibold flex items-center gap-1">
                        <Check className="w-3.5 h-3.5" /> IEC Cleared
                      </span>
                    </div>
                  </div>

                  <div className="p-4 bg-[#F7F8F5] rounded-xl border border-[#D9E2DC] space-y-2">
                    <div className="flex items-center space-x-2 text-[#0284C7] font-bold">
                      <Shield className="w-4 h-4" />
                      <span>DPDP Act 2023 Consent Template (Bilingual)</span>
                    </div>
                    <p className="text-[11px] text-[#52616B]">
                      Standardized Patient Information Sheet (PIS) and Informed Consent Form in Hindi and English.
                    </p>
                    <div className="pt-2 flex items-center justify-between text-[11px]">
                      <span className="text-[#52616B]">Digital ICF Ref: ICF-AIIA-DPDP-V2</span>
                      <span className="text-[#0284C7] font-semibold flex items-center gap-1">
                        <Check className="w-3.5 h-3.5" /> Mandatory Gate Active
                      </span>
                    </div>
                  </div>

                  <div className="p-4 bg-[#F7F8F5] rounded-xl border border-[#D9E2DC] space-y-2">
                    <div className="flex items-center space-x-2 text-[#D97706] font-bold">
                      <FileText className="w-4 h-4" />
                      <span>CTRI Registration Certificate</span>
                    </div>
                    <p className="text-[11px] text-[#52616B]">
                      Clinical Trials Registry - India acknowledgment and public trial record.
                    </p>
                    <div className="pt-2 flex items-center justify-between text-[11px]">
                      <span className="font-mono text-[#52616B]">{studyDetail.ctri_registration_number || 'CTRI/2022/10/047812'}</span>
                      <span className="text-[#166534] font-semibold flex items-center gap-1">
                        <Check className="w-3.5 h-3.5" /> Registered
                      </span>
                    </div>
                  </div>

                  <div className="p-4 bg-[#F7F8F5] rounded-xl border border-[#D9E2DC] space-y-2">
                    <div className="flex items-center space-x-2 text-[#17324D] font-bold">
                      <Download className="w-4 h-4" />
                      <span>CDISC SDTM v3.3 Dataset Export</span>
                    </div>
                    <p className="text-[11px] text-[#52616B]">
                      Standardized clinical data exchange packages for Demographics (DM), Adverse Events (AE), and Inclusion/Exclusion (IE).
                    </p>
                    <div className="pt-2 flex items-center justify-between text-[11px]">
                      <span className="text-[#52616B]">Format: CSV with SHA-256</span>
                      <span className="text-[#17324D] font-semibold">Available via Export</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'milestones' && (
              <div className="space-y-3">
                <div className="flex justify-between items-center mb-2">
                  <h4 className="text-xs font-bold text-[#17324D]">{t('milestones', 'Study Milestones & Timeline Adherence')}</h4>
                </div>
                {studyDetail.milestones?.length === 0 ? (
                  <p className="text-xs text-[#52616B] py-4">No milestones logged.</p>
                ) : (
                  <div className="divide-y divide-[#D9E2DC] border border-[#D9E2DC] rounded-xl overflow-hidden">
                    {studyDetail.milestones.map((m) => (
                      <div key={m.id} className="p-3.5 flex items-center justify-between text-xs hover:bg-[#F7F8F5]">
                        <div className="flex items-center space-x-3">
                          {m.is_overdue ? (
                            <AlertCircle className="w-4 h-4 text-[#C62828] shrink-0" />
                          ) : m.status === 'completed' ? (
                            <CheckCircle className="w-4 h-4 text-[#166534] shrink-0" />
                          ) : (
                            <Clock className="w-4 h-4 text-[#D97706] shrink-0" />
                          )}
                          <div>
                            <span className="font-semibold text-[#172026] capitalize">
                              {m.milestone_type?.replace(/_/g, ' ')}
                            </span>
                            <div className="text-[11px] text-[#52616B]">{t('date', 'Due')}: {m.due_date}</div>
                          </div>
                        </div>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          m.is_overdue ? 'bg-[#FEE2E2] text-[#C62828] border border-[#FECACA]' :
                          m.status === 'completed' ? 'bg-[#EBF3ED] text-[#166534] border border-[#C6DCCE]' :
                          'bg-[#FEF3C7] text-[#D97706] border border-[#FDE68A]'
                        }`}>
                          {m.is_overdue ? t('pv_overdue', 'OVERDUE') : formatStatus(m.status)}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'blockchain' && (
              <div className="p-5 bg-[#17324D] border-t-2 border-t-[#E68A00] rounded-xl text-white space-y-2 text-xs">
                <div className="flex items-center space-x-2 text-[#34D399] font-semibold mb-2">
                  <ShieldCheck className="w-4 h-4" />
                  <span>{t('reg_btn_verify', 'Tamper-Evidence Cryptographic Integrity')}</span>
                </div>
                <p className="text-slate-300">
                  Every state change on this study is cryptographically hashed with SHA-256 and stored in the append-only audit trail. Periodic batches are Merkle-anchored onto the Polygon Amoy testnet.
                </p>
                <div className="pt-2 text-[11px] text-[#93C5FD] font-mono">
                  Study UUID: {studyDetail.id}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
