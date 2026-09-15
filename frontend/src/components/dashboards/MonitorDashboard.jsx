import React, { useState, useEffect } from 'react';
import { studiesApi, patientsApi, queriesApi, monitoringApi } from '../../api';
import { useLanguage } from '../../context/LanguageContext';
import { FileSearch, CheckCircle, AlertTriangle, ClipboardCheck, MessageSquare, Send, PlusCircle, CheckCircle2 } from 'lucide-react';

export function MonitorDashboard() {
  const { t, formatStatus } = useLanguage();
  const [studies, setStudies] = useState([]);
  const [selectedStudyId, setSelectedStudyId] = useState('');
  const [deviations, setDeviations] = useState([]);
  const [queries, setQueries] = useState([]);
  const [monitoringVisits, setMonitoringVisits] = useState([]);
  const [activeNav, setActiveNav] = useState('compliance'); // compliance, queries, monitoring_reports

  // New Query Form State
  const [queryField, setQueryField] = useState('visit_log.actual_date');
  const [queryText, setQueryText] = useState('');
  const [queryStatusMsg, setQueryStatusMsg] = useState('');

  // Monitoring Visit Form State
  const [visitType, setVisitType] = useState('routine');
  const [visitDate, setVisitDate] = useState(new Date().toISOString().split('T')[0]);
  const [findings, setFindings] = useState('');
  const [issuesIdentified, setIssuesIdentified] = useState('');
  const [followUpRequired, setFollowUpRequired] = useState(false);
  const [reportMsg, setReportMsg] = useState('');

  useEffect(() => {
    loadStudies();
  }, []);

  useEffect(() => {
    if (selectedStudyId) {
      loadDeviations(selectedStudyId);
      loadQueries(selectedStudyId);
      loadMonitoringVisits(selectedStudyId);
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

  const loadDeviations = async (studyId) => {
    try {
      const res = await patientsApi.getDeviations(studyId);
      setDeviations(res.data);
    } catch (err) {
      console.error(err);
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

  const loadMonitoringVisits = async (studyId) => {
    try {
      const res = await monitoringApi.list({ study_id: studyId });
      setMonitoringVisits(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleRaiseQuery = async (e) => {
    e.preventDefault();
    if (!queryText.trim()) return;
    setQueryStatusMsg('');
    try {
      await queriesApi.create({
        study_id: selectedStudyId,
        field_name: queryField,
        query_text: queryText,
      });
      setQueryStatusMsg('Electronic data query raised and dispatched to Study Coordinator.');
      setQueryText('');
      loadQueries(selectedStudyId);
    } catch (err) {
      setQueryStatusMsg(err.response?.data?.detail || 'Failed to raise query.');
    }
  };

  const handleCloseQuery = async (queryId) => {
    try {
      await queriesApi.close(queryId, {});
      setQueryStatusMsg('Query verified and closed.');
      loadQueries(selectedStudyId);
    } catch (err) {
      setQueryStatusMsg(err.response?.data?.detail || 'Failed to close query.');
    }
  };

  const handleSubmitMonitoringVisit = async (e) => {
    e.preventDefault();
    setReportMsg('');
    try {
      await monitoringApi.create({
        study_id: selectedStudyId,
        visit_date: visitDate,
        visit_type: visitType,
        findings: findings,
        issues_identified: issuesIdentified,
        follow_up_required: followUpRequired,
      });
      setReportMsg('ALCOA+ Site Monitoring Report successfully submitted and committed.');
      setFindings('');
      setIssuesIdentified('');
      loadMonitoringVisits(selectedStudyId);
    } catch (err) {
      setReportMsg(err.response?.data?.detail || 'Failed to submit report.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-[#17324D] border-t-2 border-t-[#E68A00] rounded-2xl p-6 text-white shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-[#93C5FD] text-xs font-semibold uppercase tracking-wider">
              <FileSearch className="w-4 h-4 text-[#34D399]" />
              <span>{t('mon_portal_badge')}</span>
            </div>
            <h1 className="text-2xl font-bold mt-1 text-white">{t('mon_title')}</h1>
            <p className="text-xs text-slate-300 mt-1">
              {t('mon_subtitle')}
            </p>
          </div>

          <div className="bg-white/10 p-2.5 rounded-xl border border-white/20">
            <select
              value={selectedStudyId}
              onChange={(e) => setSelectedStudyId(e.target.value)}
              className="bg-[#13283E] border border-white/20 rounded-lg text-white text-xs p-1.5 focus:outline-none w-64"
            >
              {studies.map((s) => (
                <option key={s.id} value={s.id}>{s.title.slice(0, 38)}...</option>
              ))}
            </select>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex gap-2 mt-6 pt-4 border-t border-white/15 text-xs font-medium">
          <button
            onClick={() => setActiveNav('compliance')}
            className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
              activeNav === 'compliance' ? 'bg-white text-[#17324D] font-bold shadow-xs' : 'text-slate-200 hover:text-white hover:bg-white/10'
            }`}
          >
            {t('mon_tab_deviations')} ({deviations.length})
          </button>
          <button
            onClick={() => setActiveNav('queries')}
            className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
              activeNav === 'queries' ? 'bg-white text-[#17324D] font-bold shadow-xs' : 'text-slate-200 hover:text-white hover:bg-white/10'
            }`}
          >
            {t('mon_tab_queries')} ({queries.length})
          </button>
          <button
            onClick={() => setActiveNav('monitoring_reports')}
            className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
              activeNav === 'monitoring_reports' ? 'bg-white text-[#17324D] font-bold shadow-xs' : 'text-slate-200 hover:text-white hover:bg-white/10'
            }`}
          >
            ALCOA+ Monitoring Visits ({monitoringVisits.length})
          </button>
        </div>
      </div>

      {/* Deviations Tab */}
      {activeNav === 'compliance' && (
        <div className="bg-white rounded-2xl border border-[#D9E2DC] shadow-xs p-6 space-y-4">
          <h3 className="text-xs font-bold text-[#17324D]">{t('mon_deviations_title')}</h3>
          {deviations.length === 0 ? (
            <p className="text-xs text-[#52616B] py-6 text-center">{t('mon_no_deviations')}</p>
          ) : (
            <div className="divide-y divide-[#D9E2DC] border border-[#D9E2DC] rounded-xl overflow-hidden text-xs">
              {deviations.map((d) => (
                <div key={d.id} className="p-4 flex items-start justify-between gap-4 hover:bg-[#F7F8F5]">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        d.severity === 'critical' ? 'bg-[#FEE2E2] text-[#C62828] border border-[#FECACA]' :
                        d.severity === 'major' ? 'bg-[#FEF3C7] text-[#D97706] border border-[#FDE68A]' :
                        'bg-[#F0F4F8] text-[#17324D] border border-[#D9E2DC]'
                      }`}>
                        {t('coord_severity_' + d.severity, d.severity)} {t('mon_table_severity')}
                      </span>
                      <span className="text-[11px] text-[#52616B] font-mono">{t('mon_patient')}: {d.patient_id?.slice(0, 8)}</span>
                    </div>
                    <p className="text-[#172026] font-medium">{d.description}</p>
                  </div>
                  <button
                    onClick={() => {
                      setActiveNav('queries');
                      setQueryField('protocol_deviation.severity');
                      setQueryText(`CRA Query regarding deviation: ${d.description}. Please provide PI justification and corrective action.`);
                    }}
                    className="bg-[#166534] hover:bg-[#14532D] text-white px-3 py-1 rounded-lg text-[11px] font-semibold shrink-0 cursor-pointer shadow-xs transition-colors"
                  >
                    Raise Data Query
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* GCP Data Query Engine Tab */}
      {activeNav === 'queries' && (
        <div className="space-y-6">
          {queryStatusMsg && (
            <div className="p-3 bg-[#EBF3ED] text-[#166534] border border-[#C6DCCE] rounded-xl text-xs font-semibold">
              {queryStatusMsg}
            </div>
          )}

          {/* Raise Query Form */}
          <div className="bg-white rounded-2xl border border-[#D9E2DC] shadow-xs p-6 space-y-4">
            <div className="flex items-center space-x-2 text-[#17324D] font-bold">
              <PlusCircle className="w-5 h-5 text-[#166534]" />
              <h3 className="text-sm">{t('mon_btn_raise_query', 'Raise New Clinical Data Query')}</h3>
            </div>
            <form onSubmit={handleRaiseQuery} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-[#172026] mb-1">{t('mon_query_field', 'CRF Field / Data Element')}</label>
                <input
                  type="text"
                  required
                  value={queryField}
                  onChange={(e) => setQueryField(e.target.value)}
                  placeholder="e.g. visit_log.actual_date, adverse_event.causality"
                  className="w-full rounded-lg border border-[#D9E2DC] p-2 text-xs focus:outline-none focus:border-[#166534]"
                />
              </div>

              <div>
                <label className="block font-semibold text-[#172026] mb-1">{t('mon_query_text', 'Query Description / Discrepancy')}</label>
                <textarea
                  required
                  rows={3}
                  value={queryText}
                  onChange={(e) => setQueryText(e.target.value)}
                  placeholder="Explain the data discrepancy or source document verification requirement..."
                  className="w-full rounded-lg border border-[#D9E2DC] p-2 text-xs focus:outline-none focus:border-[#166534]"
                />
              </div>

              <button
                type="submit"
                className="bg-[#166534] hover:bg-[#14532D] text-white px-4 py-2 rounded-xl text-xs font-bold transition-colors shadow-xs cursor-pointer"
              >
                Dispatch Query to Coordinator
              </button>
            </form>
          </div>

          {/* Queries List */}
          <div className="bg-white rounded-2xl border border-[#D9E2DC] shadow-xs p-6 space-y-4">
            <h3 className="text-sm font-bold text-[#172026]">Study Query Ledger</h3>
            <div className="space-y-3">
              {queries.map((q) => (
                <div key={q.id} className="p-4 rounded-xl border border-[#D9E2DC] bg-[#F7F8F5] space-y-2 text-xs">
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="font-mono text-[10px] bg-[#F0F4F8] text-[#17324D] border border-[#D9E2DC] px-2 py-0.5 rounded font-bold">
                        {q.field_name}
                      </span>
                      <p className="mt-1 font-semibold text-[#172026]">{q.query_text}</p>
                    </div>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                      q.status === 'open' ? 'bg-[#FEF3C7] text-[#D97706]' :
                      q.status === 'answered' ? 'bg-[#EFF6FF] text-[#1D4ED8]' :
                      'bg-[#EBF3ED] text-[#166534]'
                    }`}>
                      {q.status}
                    </span>
                  </div>

                  {q.resolution_text && (
                    <div className="p-2.5 bg-white rounded-lg border border-[#D9E2DC] text-xs">
                      <span className="text-[10px] text-[#52616B] font-semibold block">Coordinator Response:</span>
                      <p className="text-[#172026] mt-0.5">{q.resolution_text}</p>
                    </div>
                  )}

                  {q.status === 'answered' && (
                    <button
                      type="button"
                      onClick={() => handleCloseQuery(q.id)}
                      className="bg-[#166534] hover:bg-[#14532D] text-white px-3 py-1.5 rounded-lg text-xs font-bold transition-all shadow-xs cursor-pointer flex items-center space-x-1.5"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>{t('mon_btn_close_query', 'Verify & Close Query')}</span>
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ALCOA+ Monitoring Visits Tab */}
      {activeNav === 'monitoring_reports' && (
        <div className="space-y-6">
          {reportMsg && (
            <div className="p-3 bg-[#EBF3ED] text-[#166534] border border-[#C6DCCE] rounded-xl text-xs font-semibold">
              {reportMsg}
            </div>
          )}

          {/* File New Visit Report Form */}
          <div className="bg-white rounded-2xl border border-[#D9E2DC] shadow-xs p-6 space-y-4">
            <div className="flex items-center space-x-2 text-[#17324D] font-bold">
              <ClipboardCheck className="w-5 h-5 text-[#166534]" />
              <h3 className="text-sm">Submit ALCOA+ Site Monitoring Report</h3>
            </div>
            <form onSubmit={handleSubmitMonitoringVisit} className="space-y-4 text-xs">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block font-semibold text-[#172026] mb-1">Visit Type</label>
                  <select
                    value={visitType}
                    onChange={(e) => setVisitType(e.target.value)}
                    className="w-full rounded-lg border border-[#D9E2DC] p-2 text-xs bg-white focus:outline-none focus:border-[#166534]"
                  >
                    <option value="initiation">Site Initiation Visit (SIV)</option>
                    <option value="routine">Routine Periodic Monitoring</option>
                    <option value="for_cause">For-Cause Audit / Inspection</option>
                    <option value="close_out">Site Close-Out Visit (COV)</option>
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-[#172026] mb-1">Visit Date</label>
                  <input
                    type="date"
                    required
                    value={visitDate}
                    onChange={(e) => setVisitDate(e.target.value)}
                    className="w-full rounded-lg border border-[#D9E2DC] p-2 text-xs bg-white focus:outline-none focus:border-[#166534]"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-[#172026] mb-1">Site Findings (ALCOA+ Conformance)</label>
                <textarea
                  required
                  rows={3}
                  value={findings}
                  onChange={(e) => setFindings(e.target.value)}
                  placeholder="Summarize ICF physical verification, SDV progress, drug storage temperatures, and dispensing logs..."
                  className="w-full rounded-lg border border-[#D9E2DC] p-2 text-xs focus:outline-none focus:border-[#166534]"
                />
              </div>

              <div>
                <label className="block font-semibold text-[#172026] mb-1">Action Items / Deficiencies Identified</label>
                <textarea
                  rows={2}
                  value={issuesIdentified}
                  onChange={(e) => setIssuesIdentified(e.target.value)}
                  placeholder="Note unresolved data queries, protocol deviations, or required staff retraining..."
                  className="w-full rounded-lg border border-[#D9E2DC] p-2 text-xs focus:outline-none focus:border-[#166534]"
                />
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="followUp"
                  checked={followUpRequired}
                  onChange={(e) => setFollowUpRequired(e.target.checked)}
                  className="rounded border-[#D9E2DC] text-[#166534] focus:ring-[#166534]"
                />
                <label htmlFor="followUp" className="font-semibold text-[#172026]">Formal Follow-Up Required from Principal Investigator</label>
              </div>

              <button
                type="submit"
                className="w-full bg-[#166534] hover:bg-[#14532D] text-white font-bold py-2.5 rounded-xl text-xs transition-colors shadow-xs cursor-pointer"
              >
                Sign & File Monitoring Report
              </button>
            </form>
          </div>

          {/* Historical Monitoring Reports */}
          <div className="bg-white rounded-2xl border border-[#D9E2DC] shadow-xs p-6 space-y-4">
            <h3 className="text-sm font-bold text-[#172026]">Archived Monitoring Inspection Reports</h3>
            <div className="divide-y divide-[#D9E2DC] border border-[#D9E2DC] rounded-xl overflow-hidden text-xs">
              {monitoringVisits.map((mv) => (
                <div key={mv.id} className="p-4 space-y-2 hover:bg-[#F7F8F5]">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-[#172026] uppercase">{mv.visit_type.replace('_', ' ')} VISIT</span>
                    <span className="text-[#52616B] font-mono">{mv.visit_date}</span>
                  </div>
                  <p className="text-[#172026]">{mv.findings}</p>
                  {mv.issues_identified && (
                    <p className="text-[#C62828] text-[11px]"><strong>Deficiencies:</strong> {mv.issues_identified}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
