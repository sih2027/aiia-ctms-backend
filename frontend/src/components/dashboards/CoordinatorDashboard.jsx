import React, { useState, useEffect } from 'react';
import { studiesApi, patientsApi, aeApi, queriesApi } from '../../api';
import { useLanguage } from '../../context/LanguageContext';
import { UserCheck, ShieldAlert, CheckCircle2, UserPlus, ClipboardList, Activity, AlertTriangle, FileText, Send } from 'lucide-react';

export function CoordinatorDashboard() {
  const { t, formatStatus } = useLanguage();
  const [studies, setStudies] = useState([]);
  const [selectedStudyId, setSelectedStudyId] = useState('');
  const [patients, setPatients] = useState([]);
  const [activeNav, setActiveNav] = useState('workspace'); // dashboard, workspace, queries
  const [activeTab, setActiveTab] = useState('enrollment'); // screening, enrollment, visits, deviations, ae
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState({ type: '', text: '' });

  // Patient Screening Form
  const [screeningNumber, setScreeningNumber] = useState('');
  const [patientAge, setPatientAge] = useState(35);
  const [patientSex, setPatientSex] = useState('M');
  const [abhaId, setAbhaId] = useState('');

  // Patient Enrollment Form
  const [selectedPatientId, setSelectedPatientId] = useState('');

  // AE Report Form
  const [aePatientId, setAePatientId] = useState('');
  const [aeDescription, setAeDescription] = useState('');
  const [aeSeriousness, setAeSeriousness] = useState('non_serious');
  const [aeTerm, setAeTerm] = useState('nausea');

  // Deviation Form
  const [devPatientId, setDevPatientId] = useState('');
  const [devDescription, setDevDescription] = useState('');
  const [devSeverity, setDevSeverity] = useState('minor');

  // Queries State
  const [queries, setQueries] = useState([]);
  const [queryResolution, setQueryResolution] = useState({});

  useEffect(() => {
    loadStudies();
  }, []);

  useEffect(() => {
    if (selectedStudyId) {
      loadPatients(selectedStudyId);
      loadQueries(selectedStudyId);
    }
  }, [selectedStudyId]);

  const loadStudies = async () => {
    try {
      const res = await studiesApi.list();
      setStudies(res.data);
      if (res.data.length > 0) {
        setSelectedStudyId(res.data[0].id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const loadPatients = async (studyId) => {
    try {
      setLoading(true);
      const res = await patientsApi.listForStudy(studyId);
      setPatients(res.data);
      if (res.data.length > 0) {
        setSelectedPatientId(res.data[0].id);
        setAePatientId(res.data[0].id);
        setDevPatientId(res.data[0].id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadQueries = async (studyId) => {
    try {
      const res = await queriesApi.list({ study_id: studyId });
      setQueries(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const currentStudy = studies.find((s) => s.id === selectedStudyId);
  const selectedPatient = patients.find((p) => p.id === selectedPatientId);

  // Handle Screen Patient
  const handleScreen = async (e) => {
    e.preventDefault();
    setStatusMsg({ type: '', text: '' });
    try {
      await patientsApi.screen({
        study_id: selectedStudyId,
        screening_number: screeningNumber || `SCR-${Date.now().toString().slice(-4)}`,
        age: parseInt(patientAge, 10),
        sex: patientSex,
        abha_id: abhaId || undefined,
      });
      setStatusMsg({ type: 'success', text: t('status_screened', 'Patient screened successfully!') });
      setScreeningNumber('');
      setAbhaId('');
      loadPatients(selectedStudyId);
    } catch (err) {
      setStatusMsg({ type: 'error', text: err.response?.data?.detail || t('error', 'Screening failed') });
    }
  };

  // Handle Recording Consent (Gate 2)
  const handleRecordConsent = async (patientId) => {
    setStatusMsg({ type: '', text: '' });
    try {
      await patientsApi.recordConsent(patientId, {
        consent_version: 'v1.0',
      });
      setStatusMsg({ type: 'success', text: t('coord_consent_verified', 'Informed consent signed and registered under DPDP Act 2023!') });
      loadPatients(selectedStudyId);
    } catch (err) {
      setStatusMsg({ type: 'error', text: err.response?.data?.detail || 'Failed to record consent.' });
    }
  };

  // Handle Enroll Patient (Demonstrates Dual Gates: CTRI + Consent)
  const handleEnroll = async (e) => {
    e.preventDefault();
    setStatusMsg({ type: '', text: '' });
    try {
      const res = await patientsApi.enroll({ patient_id: selectedPatientId });
      setStatusMsg({
        type: 'success',
        text: `${t('status_actively_enrolling', 'Patient enrolled successfully!')} Assigned: ${res.data.randomization_number}`,
      });
      loadPatients(selectedStudyId);
      loadStudies();
    } catch (err) {
      setStatusMsg({
        type: 'error',
        text: err.response?.data?.detail || t('coord_enrollment_prohibited', 'Enrollment rejected by system.'),
      });
    }
  };

  // Handle AE Report
  const handleReportAE = async (e) => {
    e.preventDefault();
    setStatusMsg({ type: '', text: '' });
    try {
      const res = await aeApi.create({
        study_id: selectedStudyId,
        patient_id: aePatientId,
        description: aeDescription,
        seriousness: aeSeriousness,
        ae_term: aeTerm,
      });
      setStatusMsg({
        type: 'success',
        text: `${t('pv_action_update', 'Safety report created!')} Regulatory deadline: ${res.data.regulatory_deadline}`,
      });
      setAeDescription('');
    } catch (err) {
      setStatusMsg({ type: 'error', text: err.response?.data?.detail || t('error', 'AE logging failed.') });
    }
  };

  // Handle Deviation
  const handleReportDeviation = async (e) => {
    e.preventDefault();
    setStatusMsg({ type: '', text: '' });
    try {
      await patientsApi.createDeviation({
        study_id: selectedStudyId,
        patient_id: devPatientId,
        description: devDescription,
        severity: devSeverity,
      });
      setStatusMsg({ type: 'success', text: t('mon_tab_deviations', 'Protocol deviation logged into compliance audit trail.') });
      setDevDescription('');
    } catch (err) {
      setStatusMsg({ type: 'error', text: err.response?.data?.detail || t('error', 'Failed to log deviation.') });
    }
  };

  // Handle Answer Query
  const handleAnswerQuery = async (queryId) => {
    const text = queryResolution[queryId];
    if (!text) return;
    try {
      await queriesApi.answer(queryId, { resolution_text: text });
      setStatusMsg({ type: 'success', text: t('coord_btn_answer_query', 'Resolution submitted to CRA for verification.') });
      loadQueries(selectedStudyId);
    } catch (err) {
      setStatusMsg({ type: 'error', text: err.response?.data?.detail || 'Failed to submit resolution.' });
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-[#17324D] border-t-2 border-t-[#E68A00] rounded-2xl p-6 text-white shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-[#93C5FD] text-xs font-semibold uppercase tracking-wider">
              <UserCheck className="w-4 h-4" />
              <span>{t('coord_portal_badge', 'Study Coordinator Clinical Workspace')}</span>
            </div>
            <h1 className="text-2xl font-bold mt-1 text-white">{t('coord_title', 'Patient Screening & CTRI-Gated Enrollment')}</h1>
            <p className="text-xs text-slate-300 mt-1">
              {t('coord_subtitle', 'Operational clinic portal: Screen subjects, verify CTRI gate status, record visits, and report safety events.')}
            </p>
          </div>

          {/* Study Selector */}
          <div className="bg-white/10 p-2.5 rounded-xl border border-white/20">
            <label className="block text-[10px] uppercase font-bold text-[#93C5FD] mb-1">
              {t('coord_select_study', 'Active Investigation')}
            </label>
            <select
              value={selectedStudyId}
              onChange={(e) => setSelectedStudyId(e.target.value)}
              className="bg-[#13283E] border border-white/20 rounded-lg text-white text-xs p-1.5 focus:outline-none w-64"
            >
              {studies.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.title.slice(0, 38)}... ({formatStatus(s.ctri_status)})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Nav Destinations */}
        <div className="flex flex-wrap gap-2 mt-6 pt-4 border-t border-white/15 text-xs font-medium">
          <button
            onClick={() => setActiveNav('workspace')}
            className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
              activeNav === 'workspace' ? 'bg-white text-[#17324D] font-bold shadow-xs' : 'text-slate-200 hover:text-white hover:bg-white/10'
            }`}
          >
            {t('coord_tab_assigned', 'Assigned Study Workspace')}
          </button>
          <button
            onClick={() => setActiveNav('queries')}
            className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
              activeNav === 'queries' ? 'bg-white text-[#17324D] font-bold shadow-xs' : 'text-slate-200 hover:text-white hover:bg-white/10'
            }`}
          >
            {t('coord_queries_title', 'Data Query Inbox')} ({queries.filter((q) => q.status === 'open').length})
          </button>
        </div>
      </div>

      {/* Dual Gates Status Banner */}
      {currentStudy && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Gate 1: CTRI Status */}
          <div className={`p-4 rounded-xl border flex items-center justify-between text-xs ${
            currentStudy.ctri_status === 'registered'
              ? 'bg-[#EBF3ED] border-[#C6DCCE] text-[#166534]'
              : 'bg-[#FEF3C7] border-[#FDE68A] text-[#D97706]'
          }`}>
            <div className="flex items-center space-x-3">
              {currentStudy.ctri_status === 'registered' ? (
                <CheckCircle2 className="w-5 h-5 text-[#166534] shrink-0" />
              ) : (
                <ShieldAlert className="w-5 h-5 text-[#D97706] shrink-0" />
              )}
              <div>
                <span className="font-bold">
                  {t('coord_ctri_gate_status', 'Gate 1: CTRI Legal Status')}: {currentStudy.ctri_status.toUpperCase()}
                </span>
                <p className="text-[11px] opacity-80">
                  {currentStudy.ctri_status === 'registered'
                    ? `${t('coord_enrollment_allowed', 'Enrolled under CTRI')}: ${currentStudy.ctri_registration_number}`
                    : t('coord_enrollment_prohibited', 'Enrollment prohibited until CTRI registration is confirmed.')}
                </p>
              </div>
            </div>
            <span className="text-[10px] font-mono bg-white px-2 py-1 rounded border border-[#D9E2DC] font-semibold text-[#17324D]">
              {currentStudy.enrolled_count} / {currentStudy.enrollment_target}
            </span>
          </div>

          {/* Gate 2: DPDP Act 2023 Consent Gate Overview */}
          <div className="p-4 rounded-xl border bg-white border-[#D9E2DC] flex items-center justify-between text-xs text-[#17324D]">
            <div className="flex items-center space-x-3">
              <FileText className="w-5 h-5 text-[#166534] shrink-0" />
              <div>
                <span className="font-bold">{t('coord_gate2_consent_title', 'Gate 2: DPDP Act 2023 Consent Gate')}</span>
                <p className="text-[11px] text-[#52616B]">
                  {t('coord_consent_verified', 'Individual informed consent strictly enforced before subject randomization.')}
                </p>
              </div>
            </div>
            <span className="text-[10px] bg-[#EBF3ED] text-[#166534] font-bold px-2 py-1 rounded border border-[#C6DCCE]">
              Active Gate
            </span>
          </div>
        </div>
      )}

      {/* Status Message Alert */}
      {statusMsg.text && (
        <div className={`p-3 rounded-xl text-xs font-semibold ${
          statusMsg.type === 'success' ? 'bg-[#EBF3ED] text-[#166534] border border-[#C6DCCE]' : 'bg-[#FEE2E2] text-[#C62828] border border-[#FECACA]'
        }`}>
          {statusMsg.text}
        </div>
      )}

      {/* Patient Workspace (Tabbed) */}
      {activeNav === 'workspace' && (
        <div className="bg-white rounded-2xl border border-[#D9E2DC] shadow-xs overflow-hidden">
          <div className="p-4 bg-[#F7F8F5] border-b border-[#D9E2DC] flex flex-wrap gap-2 text-xs font-medium">
            {[
              { id: 'enrollment', label: t('coord_tab_enrollment', '1. Dual-Gate Enrollment') },
              { id: 'screening', label: t('coord_tab_screening', '2. Patient Screening') },
              { id: 'deviations', label: t('coord_tab_deviations', '3. Protocol Deviation Log') },
              { id: 'ae', label: t('coord_tab_report_ae', '4. Adverse Event (AE) Submission') },
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

          <div className="p-6">
            {/* Enrollment Form with Dual Gate Feedback */}
            {activeTab === 'enrollment' && (
              <div className="max-w-xl mx-auto space-y-4">
                <div className="flex items-center space-x-2 text-[#17324D] font-bold mb-1">
                  <UserPlus className="w-5 h-5 text-[#166534]" />
                  <h3 className="text-sm">{t('coord_enroll_title', 'Enroll Screened Patient')}</h3>
                </div>
                <p className="text-xs text-[#52616B] mb-4">
                  {t('coord_enroll_desc', 'Select a screened patient to enroll and generate randomisation ID. Validated against official CTRI gate.')}
                </p>

                <form onSubmit={handleEnroll} className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-[#172026] mb-1">{t('coord_select_screened_patient', 'Select Screened Patient')}</label>
                    {patients.length === 0 ? (
                      <div className="p-3.5 bg-[#FEF3C7] border border-[#FDE68A] rounded-xl text-xs space-y-2">
                        <p className="text-[#92400E] font-bold">
                          {t('coord_no_screened_subjects', 'No subjects have been screened for this trial yet.')}
                        </p>
                        <button
                          type="button"
                          onClick={() => setActiveTab('screening')}
                          className="mt-1 bg-[#166534] hover:bg-[#14532D] text-white px-3 py-1.5 rounded-lg text-xs font-bold transition-all shadow-xs cursor-pointer flex items-center space-x-1.5"
                        >
                          <ClipboardList className="w-3.5 h-3.5" />
                          <span>{t('coord_btn_go_to_screening', 'Go to Screening Form')}</span>
                        </button>
                      </div>
                    ) : (
                      <select
                        value={selectedPatientId}
                        onChange={(e) => setSelectedPatientId(e.target.value)}
                        className="mt-1 block w-full rounded-lg border border-[#D9E2DC] p-2.5 text-xs shadow-xs focus:ring-1 focus:ring-[#166534] focus:border-[#166534] outline-none bg-white text-[#172026]"
                      >
                        {patients.map((p) => (
                          <option key={p.id} value={p.id}>
                            {p.screening_number} — {t('status', 'Status')}: {formatStatus(p.status)} ({p.age}y, {p.sex}) {p.has_valid_consent ? '✓ Consent Verified' : '⚠ Consent Missing'}
                          </option>
                        ))}
                      </select>
                    )}
                  </div>

                  {/* Selected Patient Dual-Gate Compliance Card */}
                  {selectedPatient && (
                    <div className="p-3.5 rounded-xl border border-[#D9E2DC] bg-[#F7F8F5] space-y-2.5 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-[#172026]">Gate 1: CTRI Registration</span>
                        {currentStudy?.ctri_status === 'registered' ? (
                          <span className="text-[#166534] font-bold flex items-center space-x-1">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Passed</span>
                          </span>
                        ) : (
                          <span className="text-[#C62828] font-bold flex items-center space-x-1">
                            <ShieldAlert className="w-3.5 h-3.5" />
                            <span>Blocked</span>
                          </span>
                        )}
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-[#172026]">Gate 2: DPDP Act 2023 Consent</span>
                        {selectedPatient.has_valid_consent ? (
                          <span className="text-[#166534] font-bold flex items-center space-x-1">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Verified (v1.0 Signed)</span>
                          </span>
                        ) : (
                          <div className="flex items-center space-x-2">
                            <span className="text-[#D97706] font-bold flex items-center space-x-1">
                              <ShieldAlert className="w-3.5 h-3.5" />
                              <span>Missing</span>
                            </span>
                            <button
                              type="button"
                              onClick={() => handleRecordConsent(selectedPatient.id)}
                              className="bg-[#166534] hover:bg-[#14532D] text-white px-2.5 py-1 rounded-md text-[10px] font-bold transition-all shadow-xs cursor-pointer"
                            >
                              {t('coord_btn_record_consent', 'Record Consent')}
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={!selectedPatientId || currentStudy?.ctri_status !== 'registered' || !selectedPatient?.has_valid_consent}
                    className="w-full bg-[#166534] hover:bg-[#14532D] text-white font-bold py-2.5 px-4 rounded-xl text-xs transition-colors shadow-xs cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    {t('coord_btn_enroll', 'Enroll Subject & Issue Randomisation ID')}
                  </button>
                </form>
              </div>
            )}

            {/* Screening Form */}
            {activeTab === 'screening' && (
              <form onSubmit={handleScreen} className="max-w-xl mx-auto space-y-4 text-xs">
                <div className="flex items-center space-x-2 text-[#17324D] font-bold mb-1">
                  <ClipboardList className="w-5 h-5 text-[#166534]" />
                  <h3 className="text-sm">{t('coord_tab_screening', 'Screen New Subject')}</h3>
                </div>

                <div>
                  <label className="block font-semibold text-[#172026] mb-1">{t('coord_screening_num', 'Screening Identifier')}</label>
                  <input
                    type="text"
                    value={screeningNumber}
                    onChange={(e) => setScreeningNumber(e.target.value)}
                    placeholder="e.g. SCR-DELHI-042"
                    className="w-full rounded-lg border border-[#D9E2DC] p-2.5 text-xs shadow-xs focus:ring-1 focus:ring-[#166534] focus:border-[#166534] outline-none"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-[#172026] mb-1">ABHA ID (Ayushman Bharat Health ID)</label>
                  <input
                    type="text"
                    value={abhaId}
                    onChange={(e) => setAbhaId(e.target.value)}
                    placeholder="e.g. 91-4921-3829-1092"
                    className="w-full rounded-lg border border-[#D9E2DC] p-2.5 text-xs shadow-xs focus:ring-1 focus:ring-[#166534] focus:border-[#166534] outline-none"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block font-semibold text-[#172026] mb-1">{t('coord_age', 'Age')}</label>
                    <input
                      type="number"
                      required
                      min={18}
                      max={100}
                      value={patientAge}
                      onChange={(e) => setPatientAge(e.target.value)}
                      className="w-full rounded-lg border border-[#D9E2DC] p-2.5 text-xs shadow-xs focus:ring-1 focus:ring-[#166534] focus:border-[#166534] outline-none"
                    />
                  </div>
                  <div>
                    <label className="block font-semibold text-[#172026] mb-1">{t('coord_sex', 'Sex')}</label>
                    <select
                      value={patientSex}
                      onChange={(e) => setPatientSex(e.target.value)}
                      className="w-full rounded-lg border border-[#D9E2DC] p-2.5 text-xs shadow-xs focus:ring-1 focus:ring-[#166534] focus:border-[#166534] outline-none bg-white text-[#172026]"
                    >
                      <option value="M">Male (पुरुष)</option>
                      <option value="F">Female (महिला)</option>
                      <option value="O">Other (अन्य)</option>
                    </select>
                  </div>
                </div>

                <button
                  type="submit"
                  className="w-full bg-[#166534] hover:bg-[#14532D] text-white font-semibold py-2.5 rounded-xl transition-colors shadow-xs cursor-pointer"
                >
                  {t('coord_btn_screen', 'Save Screening Assessment')}
                </button>
              </form>
            )}

            {/* Protocol Deviation Form */}
            {activeTab === 'deviations' && (
              <form onSubmit={handleReportDeviation} className="max-w-xl mx-auto space-y-4 text-xs">
                <div className="flex items-center space-x-2 text-[#17324D] font-bold mb-1">
                  <AlertTriangle className="w-5 h-5 text-[#D97706]" />
                  <h3 className="text-sm">{t('coord_tab_deviations', 'Log Protocol Deviation')}</h3>
                </div>

                <div>
                  <label className="block font-semibold text-[#172026] mb-1">{t('coord_dev_patient', 'Associated Patient')}</label>
                  <select
                    value={devPatientId}
                    onChange={(e) => setDevPatientId(e.target.value)}
                    className="w-full rounded-lg border border-[#D9E2DC] p-2.5 text-xs shadow-xs focus:ring-1 focus:ring-[#166534] focus:border-[#166534] outline-none bg-white text-[#172026]"
                  >
                    {patients.map((p) => (
                      <option key={p.id} value={p.id}>{p.screening_number} ({p.status})</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-[#172026] mb-1">{t('coord_dev_desc', 'Description of Deviation')}</label>
                  <textarea
                    required
                    rows={3}
                    value={devDescription}
                    onChange={(e) => setDevDescription(e.target.value)}
                    placeholder="e.g. Visit window exceeded by 3 days due to patient travel."
                    className="w-full rounded-lg border border-[#D9E2DC] p-2.5 text-xs shadow-xs focus:ring-1 focus:ring-[#166534] focus:border-[#166534] outline-none"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-[#172026] mb-1">{t('coord_dev_severity', 'Severity Level')}</label>
                  <select
                    value={devSeverity}
                    onChange={(e) => setDevSeverity(e.target.value)}
                    className="w-full rounded-lg border border-[#D9E2DC] p-2.5 text-xs shadow-xs focus:ring-1 focus:ring-[#166534] focus:border-[#166534] outline-none bg-white text-[#172026]"
                  >
                    <option value="minor">Minor (प्रोटोकॉल मामूली विचलन)</option>
                    <option value="major">Major (प्रमुख विचलन)</option>
                    <option value="critical">Critical (गंभीर विचलन)</option>
                  </select>
                </div>

                <button
                  type="submit"
                  className="w-full bg-[#D97706] hover:bg-[#B45309] text-white font-semibold py-2.5 rounded-xl transition-colors shadow-xs cursor-pointer"
                >
                  {t('coord_btn_log_dev', 'Log Protocol Deviation')}
                </button>
              </form>
            )}

            {/* AE Submission Form */}
            {activeTab === 'ae' && (
              <form onSubmit={handleReportAE} className="max-w-xl mx-auto space-y-4 text-xs">
                <div className="flex items-center space-x-2 text-[#17324D] font-bold mb-1">
                  <Activity className="w-5 h-5 text-[#C62828]" />
                  <h3 className="text-sm">{t('coord_tab_report_ae', 'Report Adverse Event')}</h3>
                </div>

                <div>
                  <label className="block font-semibold text-[#172026] mb-1">{t('coord_ae_patient', 'Associated Patient')}</label>
                  <select
                    value={aePatientId}
                    onChange={(e) => setAePatientId(e.target.value)}
                    className="w-full rounded-lg border border-[#D9E2DC] p-2.5 text-xs shadow-xs focus:ring-1 focus:ring-[#166534] focus:border-[#166534] outline-none bg-white text-[#172026]"
                  >
                    {patients.map((p) => (
                      <option key={p.id} value={p.id}>{p.screening_number} ({p.status})</option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block font-semibold text-[#172026] mb-1">{t('coord_ae_term', 'MedDRA Symptom Term')}</label>
                    <select
                      value={aeTerm}
                      onChange={(e) => setAeTerm(e.target.value)}
                      className="w-full rounded-lg border border-[#D9E2DC] p-2.5 text-xs shadow-xs focus:ring-1 focus:ring-[#166534] focus:border-[#166534] outline-none bg-white text-[#172026]"
                    >
                      <option value="nausea">Nausea (मतली)</option>
                      <option value="headache">Headache (सिरदर्द)</option>
                      <option value="rash">Skin Rash (त्वचा पर चकत्ते)</option>
                      <option value="vomiting">Vomiting (उल्टी)</option>
                      <option value="fatigue">Fatigue (थकान)</option>
                      <option value="pruritus">Pruritus (खुजली)</option>
                      <option value="dizziness">Dizziness (चक्कर आना)</option>
                      <option value="elevated_alt">Elevated ALT (यकृत एंजाइम वृद्धि)</option>
                      <option value="urticaria">Urticaria (पित्ती)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block font-semibold text-[#172026] mb-1">{t('coord_ae_seriousness', 'Seriousness Classification')}</label>
                    <select
                      value={aeSeriousness}
                      onChange={(e) => setAeSeriousness(e.target.value)}
                      className="w-full rounded-lg border border-[#D9E2DC] p-2.5 text-xs shadow-xs focus:ring-1 focus:ring-[#166534] focus:border-[#166534] outline-none bg-white text-[#172026]"
                    >
                      <option value="non_serious">Non-Serious (30-Day CDSCO Deadline)</option>
                      <option value="serious">Serious (15-Day Expedited Deadline)</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block font-semibold text-[#172026] mb-1">{t('coord_ae_desc', 'Clinical Description')}</label>
                  <textarea
                    required
                    rows={3}
                    value={aeDescription}
                    onChange={(e) => setAeDescription(e.target.value)}
                    placeholder="Provide clinical observations, onset time, and management details."
                    className="w-full rounded-lg border border-[#D9E2DC] p-2.5 text-xs shadow-xs focus:ring-1 focus:ring-[#166534] focus:border-[#166534] outline-none"
                  />
                </div>

                <button
                  type="submit"
                  className="w-full bg-[#C62828] hover:bg-[#B71C1C] text-white font-semibold py-2.5 rounded-xl transition-colors shadow-xs cursor-pointer"
                >
                  {t('coord_btn_submit_ae', 'Transmit Safety Event to Pharmacovigilance')}
                </button>
              </form>
            )}
          </div>
        </div>
      )}

      {/* Data Query Inbox (ActiveNav === 'queries') */}
      {activeNav === 'queries' && (
        <div className="bg-white rounded-2xl border border-[#D9E2DC] shadow-xs p-6 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[#D9E2DC]">
            <div className="flex items-center space-x-2">
              <ClipboardList className="w-5 h-5 text-[#166534]" />
              <h3 className="text-sm font-bold text-[#172026]">{t('coord_queries_title', 'Clinical Data Query Management')}</h3>
            </div>
            <span className="text-xs text-[#52616B]">Total: {queries.length} Queries</span>
          </div>

          {queries.length === 0 ? (
            <p className="text-xs text-[#52616B] py-8 text-center">{t('coord_no_queries', 'No data queries raised for this study.')}</p>
          ) : (
            <div className="space-y-4">
              {queries.map((q) => (
                <div key={q.id} className="p-4 rounded-xl border border-[#D9E2DC] bg-[#F7F8F5] space-y-3 text-xs">
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="font-mono text-[10px] bg-[#F0F4F8] text-[#17324D] border border-[#D9E2DC] px-2 py-0.5 rounded font-bold">
                        {q.field_name}
                      </span>
                      <p className="mt-1 font-semibold text-[#172026]">{q.query_text}</p>
                      <p className="text-[10px] text-[#52616B] mt-0.5">Raised by: {q.raiser_name || 'CRA / Monitor'}</p>
                    </div>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                      q.status === 'open' ? 'bg-[#FEF3C7] text-[#D97706] border border-[#FDE68A]' :
                      q.status === 'answered' ? 'bg-[#EFF6FF] text-[#1D4ED8] border border-[#BFDBFE]' :
                      'bg-[#EBF3ED] text-[#166534] border border-[#C6DCCE]'
                    }`}>
                      {q.status}
                    </span>
                  </div>

                  {q.resolution_text ? (
                    <div className="p-2.5 bg-white rounded-lg border border-[#D9E2DC]">
                      <span className="text-[10px] text-[#52616B] font-semibold block">Resolution Provided:</span>
                      <p className="text-[#172026] mt-0.5">{q.resolution_text}</p>
                    </div>
                  ) : (
                    <div className="space-y-2 pt-2 border-t border-[#D9E2DC]">
                      <label className="block text-[11px] font-semibold text-[#172026]">{t('coord_query_resolution', 'Provide Clarification / Rationale')}</label>
                      <div className="flex gap-2">
                        <input
                          type="text"
                          placeholder="Enter source verification evidence or justification..."
                          value={queryResolution[q.id] || ''}
                          onChange={(e) => setQueryResolution({ ...queryResolution, [q.id]: e.target.value })}
                          className="flex-1 rounded-lg border border-[#D9E2DC] px-3 py-1.5 text-xs bg-white focus:outline-none focus:border-[#166534]"
                        />
                        <button
                          type="button"
                          onClick={() => handleAnswerQuery(q.id)}
                          className="bg-[#166534] hover:bg-[#14532D] text-white px-3 py-1.5 rounded-lg text-xs font-bold transition-all shadow-xs cursor-pointer shrink-0 flex items-center space-x-1"
                        >
                          <Send className="w-3 h-3" />
                          <span>{t('coord_btn_answer_query', 'Submit')}</span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
