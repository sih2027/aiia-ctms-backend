import React, { useState, useEffect } from 'react';
import { aeApi } from '../../api';
import { useLanguage } from '../../context/LanguageContext';
import { Activity, ShieldAlert, AlertTriangle, CheckCircle, Clock, Filter, Send, AlertOctagon } from 'lucide-react';

export function PVDashboard() {
  const { t, formatStatus } = useLanguage();
  const [activeNav, setActiveNav] = useState('inbox'); // inbox, workspace, dsmb, signals
  const [events, setEvents] = useState([]);
  const [dsmbFeed, setDsmbFeed] = useState([]);
  const [signals, setSignals] = useState([]);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filterSeriousness, setFilterSeriousness] = useState('');
  const [statusAction, setStatusAction] = useState('under_review');
  const [updateOutcome, setUpdateOutcome] = useState('recovered');
  const [causalityGrade, setCausalityGrade] = useState('possible');
  const [causalityAction, setCausalityAction] = useState('');
  const [statusMsg, setStatusMsg] = useState('');

  useEffect(() => {
    loadEvents();
    loadSignals();
  }, [filterSeriousness]);

  const loadEvents = async () => {
    try {
      setLoading(true);
      const params = {};
      if (filterSeriousness) params.seriousness = filterSeriousness;
      const res = await aeApi.list(params);
      setEvents(res.data);
      if (res.data.length > 0 && !selectedEvent) {
        setSelectedEvent(res.data[0]);
        setCausalityGrade(res.data[0].causality || 'possible');
        setCausalityAction(res.data[0].action_taken || '');
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadSignals = async () => {
    try {
      const res = await aeApi.signals();
      setSignals(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadDSMB = async () => {
    try {
      const res = await aeApi.dsmbFeed();
      setDsmbFeed(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    if (activeNav === 'dsmb') {
      loadDSMB();
    }
  }, [activeNav]);

  const handleUpdateStatus = async (e) => {
    e.preventDefault();
    if (!selectedEvent) return;
    setStatusMsg('');
    try {
      const res = await aeApi.updateStatus(selectedEvent.id, {
        status: statusAction,
        outcome: updateOutcome,
      });
      setStatusMsg(`${t('pv_action_update', 'Workflow status updated')} (${formatStatus(statusAction)})!`);
      setSelectedEvent(res.data);
      loadEvents();
    } catch (err) {
      setStatusMsg(err.response?.data?.detail || t('error', 'Status update failed.'));
    }
  };

  const handleAssessCausality = async (e) => {
    e.preventDefault();
    if (!selectedEvent) return;
    setStatusMsg('');
    try {
      const res = await aeApi.assessCausality(selectedEvent.id, {
        causality: causalityGrade,
        action_taken: causalityAction,
      });
      setStatusMsg(`WHO-UMC Causality assessed: ${causalityGrade.toUpperCase()}!`);
      setSelectedEvent(res.data);
      loadEvents();
    } catch (err) {
      setStatusMsg(err.response?.data?.detail || 'Causality update failed.');
    }
  };

  const getUrgencyBadge = (ae) => {
    const today = new Date();
    const deadline = new Date(ae.regulatory_deadline);
    const diffDays = Math.ceil((deadline - today) / (1000 * 60 * 60 * 24));

    if (ae.status === 'resolved' || ae.status === 'reported') {
      return (
        <span className="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center space-x-1">
          <CheckCircle className="w-3 h-3" />
          <span>{formatStatus(ae.status)}</span>
        </span>
      );
    }

    if (diffDays < 0) {
      return (
        <span className="bg-rose-600 text-white text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center space-x-1 animate-pulse">
          <AlertTriangle className="w-3 h-3" />
          <span>{t('pv_overdue', 'OVERDUE')} ({Math.abs(diffDays)} {t('pv_days_left', 'days')})</span>
        </span>
      );
    }

    if (diffDays <= 3) {
      return (
        <span className="bg-rose-100 text-rose-800 border border-rose-300 text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center space-x-1">
          <Clock className="w-3 h-3 text-rose-600" />
          <span>{t('critical', 'URGENT')}: {diffDays} {t('pv_days_left', 'Day(s) Left')}</span>
        </span>
      );
    }

    return (
      <span className="bg-amber-100 text-amber-800 border border-amber-300 text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center space-x-1">
        <Clock className="w-3 h-3 text-amber-600" />
        <span>{diffDays} {t('pv_days_left', 'days left')}</span>
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-[#17324D] border-t-2 border-t-[#E68A00] rounded-2xl p-6 text-white shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-[#93C5FD] text-xs font-semibold uppercase tracking-wider">
              <Activity className="w-4 h-4 text-[#C62828]" />
              <span>{t('pv_portal_badge')}</span>
            </div>
            <h1 className="text-2xl font-bold mt-1 text-white">{t('pv_title')}</h1>
            <p className="text-xs text-slate-300 mt-1">
              {t('pv_subtitle')}
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <span className="bg-rose-600 text-white font-mono text-xs px-3 py-1.5 rounded-xl font-bold shadow-xs">
              {events.filter((e) => e.seriousness === 'serious' && e.status === 'open').length} {t('pv_statutory_sae')}
            </span>
          </div>
        </div>

        {/* 3 Nav Destinations */}
        <div className="flex flex-wrap gap-2 mt-6 pt-4 border-t border-white/15 text-xs font-medium">
          <button
            onClick={() => setActiveNav('inbox')}
            className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
              activeNav === 'inbox' ? 'bg-white text-[#17324D] font-bold shadow-xs' : 'text-slate-200 hover:text-white hover:bg-white/10'
            }`}
          >
            {t('pv_tab_inbox')} ({events.length})
          </button>
          <button
            onClick={() => setActiveNav('dsmb')}
            className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
              activeNav === 'dsmb' ? 'bg-white text-[#17324D] font-bold shadow-xs' : 'text-slate-200 hover:text-white hover:bg-white/10'
            }`}
          >
            {t('pv_tab_dsmb')}
          </button>
          <button
            onClick={() => setActiveNav('signals')}
            className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
              activeNav === 'signals' ? 'bg-white text-[#17324D] font-bold shadow-xs' : 'text-slate-200 hover:text-white hover:bg-white/10'
            }`}
          >
            NPvCC Safety Signals ({signals.length})
          </button>
        </div>
      </div>

      {/* NPvCC 30-Day Signal Detection High-Priority Banner */}
      {signals.length > 0 && (
        <div className="space-y-3">
          {signals.map((sig, idx) => (
            <div
              key={idx}
              className="p-4 bg-[#FFF5F5] border-2 border-[#FECACA] rounded-2xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-sm"
            >
              <div className="flex items-start space-x-3.5">
                <div className="w-10 h-10 rounded-xl bg-[#FEE2E2] flex items-center justify-center text-[#C62828] shrink-0 mt-0.5">
                  <AlertOctagon className="w-6 h-6 animate-pulse" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="bg-[#C62828] text-white text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider">
                      {t('pv_signal_detected_title', 'NPvCC Safety Signal Detected')}
                    </span>
                    <span className="font-bold text-sm text-[#172026]">{sig.ae_term} ({sig.count_in_30_days} cases in 30 days)</span>
                  </div>
                  <p className="text-xs text-[#52616B] mt-1">
                    <strong className="text-[#172026]">{t('pv_suspected_formulation', 'Suspected Formulation')}:</strong> {sig.intervention} | <strong className="text-[#172026]">Study:</strong> {sig.study_title}
                  </p>
                  <p className="text-xs text-[#C62828] font-semibold mt-1">
                    {t('pv_signal_recommendation', 'Recommendation')}: {sig.recommendation}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setActiveNav('signals')}
                className="bg-[#C62828] hover:bg-[#B71C1C] text-white px-3.5 py-2 rounded-xl text-xs font-bold shrink-0 transition-all shadow-xs cursor-pointer"
              >
                Review Signal Dossier
              </button>
            </div>
          ))}
        </div>
      )}

      {statusMsg && (
        <div className="p-3 bg-[#EBF3ED] text-[#166534] border border-[#C6DCCE] rounded-xl text-xs font-semibold">
          {statusMsg}
        </div>
      )}

      {/* Main Workspace (Inbox / Detail) */}
      {activeNav === 'inbox' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* AE List (Left Column) */}
          <div className="lg:col-span-5 bg-white rounded-2xl border border-[#D9E2DC] shadow-xs overflow-hidden flex flex-col">
            <div className="p-4 bg-[#F7F8F5] border-b border-[#D9E2DC] flex justify-between items-center">
              <span className="text-xs font-bold text-[#17324D]">Triage Queue (By Regulatory Urgency)</span>
              <div className="flex items-center space-x-1">
                <Filter className="w-3.5 h-3.5 text-[#52616B]" />
                <select
                  value={filterSeriousness}
                  onChange={(e) => setFilterSeriousness(e.target.value)}
                  className="text-xs border border-[#D9E2DC] rounded p-1 bg-white"
                >
                  <option value="">{t('all')}</option>
                  <option value="serious">{t('serious')}</option>
                  <option value="non_serious">{t('non_serious')}</option>
                </select>
              </div>
            </div>

            <div className="divide-y divide-[#D9E2DC] overflow-y-auto max-h-[600px]">
              {events.map((ae) => (
                <div
                  key={ae.id}
                  onClick={() => {
                    setSelectedEvent(ae);
                    setCausalityGrade(ae.causality || 'possible');
                    setCausalityAction(ae.action_taken || '');
                  }}
                  className={`p-4 cursor-pointer transition-colors text-xs space-y-2 ${
                    selectedEvent?.id === ae.id ? 'bg-[#F0F4F8] border-l-4 border-l-[#166534]' : 'hover:bg-[#F7F8F5]'
                  }`}
                >
                  <div className="flex justify-between items-start gap-2">
                    <span className="font-bold text-[#172026] text-xs">
                      {ae.ae_term ? ae.ae_term.replace('_', ' ').toUpperCase() : 'ADVERSE EVENT'}
                    </span>
                    {getUrgencyBadge(ae)}
                  </div>
                  <p className="text-[#52616B] line-clamp-2 text-[11px]">{ae.description}</p>
                  <div className="flex justify-between items-center text-[10px] text-[#52616B] pt-1">
                    <span>{t('report_date')}: {ae.report_date}</span>
                    <span className="font-mono text-[#C62828] font-bold">
                      {t('pv_deadline')}: {ae.regulatory_deadline}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* AE Detail & Actions (Right Column) */}
          <div className="lg:col-span-7 space-y-6">
            {selectedEvent ? (
              <div className="bg-white rounded-2xl border border-[#D9E2DC] shadow-xs p-6 space-y-5">
                <div className="flex justify-between items-start pb-4 border-b border-[#D9E2DC]">
                  <div>
                    <span className="text-[10px] font-mono bg-[#F0F4F8] text-[#17324D] border border-[#D9E2DC] px-2 py-0.5 rounded font-bold">
                      EVENT ID: {selectedEvent.id.slice(0, 8)}
                    </span>
                    <h3 className="text-base font-bold text-[#172026] mt-1">
                      {selectedEvent.ae_term ? selectedEvent.ae_term.replace('_', ' ').toUpperCase() : 'Adverse Event Report'}
                    </h3>
                  </div>
                  {getUrgencyBadge(selectedEvent)}
                </div>

                <div className="grid grid-cols-2 gap-4 text-xs">
                  <div className="p-3 bg-[#F7F8F5] rounded-xl border border-[#D9E2DC]">
                    <span className="text-[10px] text-[#52616B] font-semibold block">{t('seriousness')}</span>
                    <span className="font-bold text-[#172026] capitalize">{selectedEvent.seriousness.replace('_', ' ')}</span>
                  </div>
                  <div className="p-3 bg-[#F7F8F5] rounded-xl border border-[#D9E2DC]">
                    <span className="text-[10px] text-[#52616B] font-semibold block">{t('pv_regulatory_deadline')}</span>
                    <span className="font-bold text-[#C62828] font-mono">{selectedEvent.regulatory_deadline}</span>
                  </div>
                </div>

                <div>
                  <h4 className="text-xs font-bold text-[#172026] mb-1">{t('description')}</h4>
                  <div className="p-3.5 bg-[#F7F8F5] rounded-xl border border-[#D9E2DC] text-xs text-[#172026] leading-relaxed">
                    {selectedEvent.description}
                  </div>
                </div>

                {/* WHO-UMC Causality Assessment Form */}
                <form onSubmit={handleAssessCausality} className="p-4 rounded-xl border border-[#D9E2DC] bg-[#F7F8F5] space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold text-[#17324D]">{t('pv_causality_assessment', 'WHO-UMC Causality Assessment')}</h4>
                    {selectedEvent.causality && (
                      <span className="bg-[#EBF3ED] text-[#166534] border border-[#C6DCCE] text-[10px] font-bold px-2 py-0.5 rounded uppercase">
                        {selectedEvent.causality}
                      </span>
                    )}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                    <div>
                      <label className="block text-[11px] font-semibold text-[#172026] mb-1">Causality Grade (WHO-UMC)</label>
                      <select
                        value={causalityGrade}
                        onChange={(e) => setCausalityGrade(e.target.value)}
                        className="w-full rounded-lg border border-[#D9E2DC] p-2 text-xs bg-white focus:outline-none focus:border-[#166534]"
                      >
                        <option value="certain">Certain (निश्चित)</option>
                        <option value="probable">Probable / Likely (संभाव्य)</option>
                        <option value="possible">Possible (संभव)</option>
                        <option value="unlikely">Unlikely (असंभाव्य)</option>
                        <option value="unclassified">Conditional / Unclassified (सशर्त)</option>
                        <option value="unclassifiable">Unassessable / Unclassifiable (अवर्गीकृत)</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-[11px] font-semibold text-[#172026] mb-1">{t('pv_action_taken', 'Action Taken')}</label>
                      <input
                        type="text"
                        value={causalityAction}
                        onChange={(e) => setCausalityAction(e.target.value)}
                        placeholder="e.g. Dose reduced, symptomatic relief given"
                        className="w-full rounded-lg border border-[#D9E2DC] p-2 text-xs bg-white focus:outline-none focus:border-[#166534]"
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    className="bg-[#166534] hover:bg-[#14532D] text-white px-3 py-1.5 rounded-lg text-xs font-bold transition-all shadow-xs cursor-pointer"
                  >
                    {t('pv_btn_assess_causality', 'Save Causality Classification')}
                  </button>
                </form>

                {/* Workflow Status Transition */}
                <form onSubmit={handleUpdateStatus} className="pt-4 border-t border-[#D9E2DC] space-y-3">
                  <h4 className="text-xs font-bold text-[#172026]">Regulatory Status Action</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <select
                      value={statusAction}
                      onChange={(e) => setStatusAction(e.target.value)}
                      className="rounded-lg border border-[#D9E2DC] p-2 text-xs bg-white"
                    >
                      <option value="under_review">Under Review (समीक्षाधीन)</option>
                      <option value="reported">Reported to CDSCO / NPvCC (प्रतिवेदित)</option>
                      <option value="resolved">Resolved & Closed (निस्तारित)</option>
                    </select>
                    <select
                      value={updateOutcome}
                      onChange={(e) => setUpdateOutcome(e.target.value)}
                      className="rounded-lg border border-[#D9E2DC] p-2 text-xs bg-white"
                    >
                      <option value="recovered">Recovered (स्वस्थ)</option>
                      <option value="recovering">Recovering (सुधार हो रहा है)</option>
                      <option value="not_recovered">Not Recovered (अपरिवर्तित)</option>
                      <option value="fatal">Fatal (घातक)</option>
                    </select>
                  </div>
                  <button
                    type="submit"
                    className="w-full bg-[#17324D] hover:bg-[#13283E] text-white font-bold py-2 rounded-xl text-xs transition-colors shadow-xs cursor-pointer"
                  >
                    Transmit Status Transition to Audit Ledger
                  </button>
                </form>
              </div>
            ) : (
              <div className="bg-white rounded-2xl border border-[#D9E2DC] p-12 text-center text-xs text-[#52616B]">
                Select an event from the queue to view full dossier and perform causality assessment.
              </div>
            )}
          </div>
        </div>
      )}

      {/* DSMB Feed View */}
      {activeNav === 'dsmb' && (
        <div className="bg-white rounded-2xl border border-[#D9E2DC] shadow-xs p-6 space-y-4">
          <div className="flex justify-between items-center pb-3 border-b border-[#D9E2DC]">
            <h3 className="text-sm font-bold text-[#172026]">{t('pv_tab_dsmb')}</h3>
            <span className="text-xs text-[#52616B]">Live Cross-Study DSMB Safety Stream</span>
          </div>

          <div className="divide-y divide-[#D9E2DC] border border-[#D9E2DC] rounded-xl overflow-hidden text-xs">
            {dsmbFeed.map((e) => (
              <div key={e.id} className="p-4 flex items-center justify-between hover:bg-[#F7F8F5]">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-[#172026]">{e.ae_term?.toUpperCase()}</span>
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                      e.seriousness === 'serious' ? 'bg-[#FEE2E2] text-[#C62828]' : 'bg-[#F0F4F8] text-[#17324D]'
                    }`}>
                      {e.seriousness}
                    </span>
                  </div>
                  <p className="text-[#52616B] text-[11px]">{e.description}</p>
                </div>
                <div className="text-right space-y-1">
                  <span className="text-rose-600 font-mono font-bold block">{e.regulatory_deadline}</span>
                  <span className="text-[10px] text-[#52616B] capitalize">{formatStatus(e.status)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Signals View */}
      {activeNav === 'signals' && (
        <div className="bg-white rounded-2xl border border-[#D9E2DC] shadow-xs p-6 space-y-4">
          <h3 className="text-sm font-bold text-[#172026]">NPvCC Rolling 30-Day Safety Signal Detection Logs</h3>
          <p className="text-xs text-[#52616B]">
            Automated pharmacovigilance surveillance algorithm scans rolling 30-day reporting windows. If 3 or more cases of identical symptom terms emerge, a high-level safety signal is raised for DSMB investigation.
          </p>

          <div className="space-y-4 pt-2">
            {signals.map((sig, idx) => (
              <div key={idx} className="p-5 rounded-xl border border-[#FECACA] bg-[#FFF5F5] space-y-3 text-xs">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="bg-[#C62828] text-white text-xs font-bold px-2.5 py-0.5 rounded-full">
                      LEVEL: {sig.signal_level}
                    </span>
                    <span className="text-sm font-bold text-[#172026]">{sig.ae_term}</span>
                  </div>
                  <span className="text-xs font-mono font-bold text-[#C62828]">
                    {sig.count_in_30_days} cases ({sig.earliest_date} to {sig.latest_date})
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-4 bg-white p-3 rounded-lg border border-[#D9E2DC]">
                  <div>
                    <span className="text-[10px] text-[#52616B] font-semibold block">Investigation Title</span>
                    <span className="font-semibold text-[#172026]">{sig.study_title}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-[#52616B] font-semibold block">Formulation Composition</span>
                    <span className="font-semibold text-[#172026]">{sig.intervention}</span>
                  </div>
                </div>
                <div className="p-3 bg-[#FEF3C7] rounded-lg border border-[#FDE68A] text-[#92400E]">
                  <strong>Action Required:</strong> {sig.recommendation}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
