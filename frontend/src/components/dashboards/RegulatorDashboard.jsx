import React, { useState, useEffect } from 'react';
import { auditApi, studiesApi, exportApi, fhirApi } from '../../api';
import { useLanguage } from '../../context/LanguageContext';
import { ShieldCheck, Database, FileSpreadsheet, Download, RefreshCw, AlertCircle, CheckCircle2, Lock, Code, ExternalLink, ShieldAlert, Undo2 } from 'lucide-react';

export function RegulatorDashboard() {
  const { t, formatStatus } = useLanguage();
  const [activeNav, setActiveNav] = useState('anchor'); // anchor, portfolio, export
  const [studies, setStudies] = useState([]);
  const [selectedStudyId, setSelectedStudyId] = useState('');
  const [auditRows, setAuditRows] = useState([]);
  const [verifyResult, setVerifyResult] = useState(null);
  const [verifying, setVerifying] = useState(false);
  const [anchoring, setAnchoring] = useState(false);
  const [anchorMsg, setAnchorMsg] = useState('');
  const [fhirData, setFhirData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [studiesRes, trailRes] = await Promise.all([
        studiesApi.list(),
        auditApi.trail({ limit: 50 }),
      ]);
      setStudies(studiesRes.data);
      if (studiesRes.data.length > 0) {
        setSelectedStudyId(studiesRes.data[0].id);
      }
      setAuditRows(trailRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (simulate = false) => {
    setVerifying(true);
    try {
      const res = await auditApi.verify(simulate);
      setVerifyResult(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setVerifying(false);
    }
  };

  const handleSimulateTamper = async () => {
    setVerifying(true);
    try {
      await auditApi.simulateTamper();
      const res = await auditApi.verify(true);
      setVerifyResult(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setVerifying(false);
    }
  };

  const handleRestoreTamper = async () => {
    setVerifying(true);
    try {
      await auditApi.restoreTamper();
      const res = await auditApi.verify(false);
      setVerifyResult(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setVerifying(false);
    }
  };

  const handleManualAnchor = async () => {
    setAnchoring(true);
    setAnchorMsg('');
    try {
      const res = await auditApi.anchor();
      setAnchorMsg(res.data.anchored ? `Batch anchored! Tx Hash: ${res.data.tx_hash}` : res.data.reason);
      handleVerify(false);
    } catch (err) {
      setAnchorMsg(err.response?.data?.detail || 'Anchor commit skipped or RPC unconfigured.');
    } finally {
      setAnchoring(false);
    }
  };

  const handleViewFhir = async (studyId) => {
    try {
      const res = await fhirApi.study(studyId);
      setFhirData(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-[#17324D] border-t-2 border-t-[#E68A00] rounded-2xl p-6 text-white shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 text-[#93C5FD] text-xs font-semibold uppercase tracking-wider">
              <Lock className="w-4 h-4 text-[#34D399]" />
              <span>{t('reg_portal_badge')}</span>
            </div>
            <h1 className="text-2xl font-bold mt-1 text-white">{t('reg_title')}</h1>
            <p className="text-xs text-slate-300 mt-1">
              {t('reg_subtitle')}
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => handleVerify(false)}
              disabled={verifying}
              className="flex items-center space-x-2 bg-[#166534] hover:bg-[#14532D] text-white font-bold px-4 py-2.5 rounded-xl text-xs transition-all shadow-xs disabled:opacity-50 cursor-pointer"
            >
              <RefreshCw className={`w-4 h-4 ${verifying ? 'animate-spin' : ''}`} />
              <span>{verifying ? t('reg_btn_verifying') : t('reg_btn_verify')}</span>
            </button>
            <button
              onClick={handleSimulateTamper}
              disabled={verifying}
              className="flex items-center space-x-1.5 bg-white/10 hover:bg-[#C62828] text-white font-semibold px-3 py-2.5 rounded-xl text-xs transition-all border border-white/20 hover:border-transparent cursor-pointer"
              title={t('reg_btn_tamper_tooltip')}
            >
              <AlertCircle className="w-3.5 h-3.5" />
              <span>{t('reg_btn_simulate_tamper')}</span>
            </button>
            {verifyResult?.status === 'mismatched' && (
              <button
                onClick={handleRestoreTamper}
                disabled={verifying}
                className="flex items-center space-x-1.5 bg-[#166534] hover:bg-[#14532D] text-white font-bold px-3 py-2.5 rounded-xl text-xs transition-all shadow-xs cursor-pointer"
              >
                <Undo2 className="w-3.5 h-3.5" />
                <span>{t('reg_btn_restore_integrity', 'Restore Integrity')}</span>
              </button>
            )}
          </div>
        </div>

        {/* 3 Nav Destinations */}
        <div className="flex flex-wrap gap-2 mt-6 pt-4 border-t border-white/15 text-xs font-medium">
          <button
            onClick={() => setActiveNav('anchor')}
            className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
              activeNav === 'anchor' ? 'bg-white text-[#17324D] font-bold shadow-xs' : 'text-slate-200 hover:text-white hover:bg-white/10'
            }`}
          >
            {t('reg_tab_anchor')}
          </button>
          <button
            onClick={() => setActiveNav('export')}
            className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
              activeNav === 'export' ? 'bg-white text-[#17324D] font-bold shadow-xs' : 'text-slate-200 hover:text-white hover:bg-white/10'
            }`}
          >
            {t('reg_tab_export')}
          </button>
          <button
            onClick={() => setActiveNav('portfolio')}
            className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
              activeNav === 'portfolio' ? 'bg-white text-[#17324D] font-bold shadow-xs' : 'text-slate-200 hover:text-white hover:bg-white/10'
            }`}
          >
            {t('reg_tab_portfolio')}
          </button>
        </div>
      </div>

      {/* Audit Anchor Verification Panel (The Primary Demo Moment) */}
      {activeNav === 'anchor' && (
        <div className="space-y-6">
          {/* Integrity Status Card */}
          <div className="bg-white rounded-2xl border border-[#D9E2DC] p-6 shadow-xs">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[#D9E2DC]">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-xl bg-[#EBF3ED] flex items-center justify-center text-[#166534] font-bold">
                  <ShieldCheck className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-[#172026]">{t('reg_anchor_panel_title')}</h3>
                  <p className="text-xs text-[#52616B]">
                    {t('reg_anchor_panel_desc')}
                  </p>
                </div>
              </div>

              {/* Live Badge */}
              <div>
                {verifyResult?.status === 'matched' ? (
                  <span className="bg-[#EBF3ED] text-[#166534] border border-[#C6DCCE] text-xs font-bold px-3 py-1.5 rounded-xl flex items-center space-x-1.5 shadow-xs">
                    <CheckCircle2 className="w-4 h-4 text-[#166534]" />
                    <span>{t('reg_status_verified')}</span>
                  </span>
                ) : verifyResult?.status === 'mismatched' ? (
                  <span className="bg-[#FEE2E2] text-[#C62828] border border-[#FECACA] text-xs font-bold px-3 py-1.5 rounded-xl flex items-center space-x-1.5 animate-bounce">
                    <AlertCircle className="w-4 h-4 text-[#C62828]" />
                    <span>{t('reg_status_mismatch')}</span>
                  </span>
                ) : (
                  <span className="bg-[#F0F4F8] text-[#17324D] border border-[#D9E2DC] text-xs font-medium px-3 py-1.5 rounded-xl">
                    {t('reg_verification_status')}: {verifyResult?.status || t('reg_status_no_anchor')}
                  </span>
                )}
              </div>
            </div>

            {/* Verification Metadata Grid */}
            <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
              <div className="bg-[#F7F8F5] p-3.5 rounded-xl border border-[#D9E2DC]">
                <span className="text-[#52616B] block text-[10px] uppercase font-sans font-semibold mb-1">
                  {t('reg_merkle_root')}
                </span>
                <span className="text-[#172026] break-all">
                  {verifyResult?.recomputed_merkle_root || t('reg_btn_verify')}
                </span>
              </div>
              <div className="bg-[#F7F8F5] p-3.5 rounded-xl border border-[#D9E2DC]">
                <span className="text-[#52616B] block text-[10px] uppercase font-sans font-semibold mb-1">
                  {t('reg_onchain_root')}
                </span>
                <span className="text-[#172026] break-all">
                  {verifyResult?.onchain_merkle_root || verifyResult?.stored_merkle_root || t('reg_status_no_anchor')}
                </span>
              </div>
            </div>

            {/* Live Polygonscan Explorer Link */}
            {verifyResult?.explorer_url && (
              <div className="mt-4 pt-3 border-t border-[#D9E2DC] flex items-center justify-between">
                <span className="text-xs text-[#52616B]">Blockchain Contract Ledger: Polygon Amoy Testnet (Chain ID 80002)</span>
                <a
                  href={verifyResult.explorer_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="bg-[#17324D] hover:bg-[#13283E] text-white px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-colors shadow-xs"
                >
                  <span>{t('reg_view_polygonscan', 'View on Polygonscan Amoy')}</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
            )}

            {anchorMsg && (
              <div className="mt-3 p-2 bg-[#F7F8F5] border border-[#D9E2DC] rounded-lg text-xs font-mono text-[#52616B]">
                {anchorMsg}
              </div>
            )}
          </div>

          {/* Immutable Audit Log Table */}
          <div className="bg-white rounded-2xl border border-[#D9E2DC] shadow-xs overflow-hidden">
            <div className="p-4 bg-[#F7F8F5] border-b border-[#D9E2DC] flex justify-between items-center text-xs">
              <div className="flex items-center space-x-2 font-bold text-[#17324D]">
                <Database className="w-4 h-4 text-[#166534]" />
                <span>{t('reg_audit_table_title')}</span>
              </div>
              <span className="text-[#52616B] font-medium">{t('reg_alcoa_standard')}</span>
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
                <tbody className="divide-y divide-[#D9E2DC]">
                  {auditRows.map((row) => (
                    <tr key={row.id} className="hover:bg-[#F7F8F5] font-mono text-[11px]">
                      <td className="py-2.5 px-4 font-sans font-semibold">
                        <span className="bg-[#F0F4F8] text-[#17324D] border border-[#D9E2DC] px-2 py-0.5 rounded">
                          {row.action}
                        </span>
                      </td>
                      <td className="py-2.5 px-4 capitalize font-sans text-[#172026]">{row.entity_type}</td>
                      <td className="py-2.5 px-4 text-[#52616B]">{row.timestamp?.replace('T', ' ').slice(0, 19)}</td>
                      <td className="py-2.5 px-4 text-[#166534] break-all font-mono" title={row.row_hash}>
                        {row.row_hash.slice(0, 24)}...
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* CDISC SDTM & FHIR Inspection Screen */}
      {activeNav === 'export' && (
        <div className="space-y-6">
          <div className="bg-white rounded-2xl border border-[#D9E2DC] p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-[#172026]">{t('reg_sdtm_hub_title')}</h3>
                <p className="text-xs text-[#52616B]">
                  {t('reg_sdtm_hub_desc')}
                </p>
              </div>

              {/* Study Picker */}
              <select
                value={selectedStudyId}
                onChange={(e) => {
                  setSelectedStudyId(e.target.value);
                  setFhirData(null);
                }}
                className="bg-[#F7F8F5] border border-[#D9E2DC] rounded-lg p-2 text-xs font-semibold w-72 text-[#172026] outline-none focus:border-[#166534]"
              >
                {studies.map((s) => (
                  <option key={s.id} value={s.id}>{s.title.slice(0, 45)}...</option>
                ))}
              </select>
            </div>

            {/* Download Buttons Grid (4 CDISC domains) */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-2">
              <a
                href={exportApi.dmUrl(selectedStudyId)}
                download
                className="p-4 rounded-xl border border-[#D9E2DC] bg-[#F7F8F5] hover:bg-[#EBF3ED] hover:border-[#C6DCCE] flex items-center space-x-3 transition-colors group"
              >
                <FileSpreadsheet className="w-6 h-6 text-[#166534] group-hover:scale-110 transition-transform" />
                <div className="text-left">
                  <span className="text-xs font-bold text-[#172026] block">{t('reg_btn_download_dm')}</span>
                  <span className="text-[10px] text-[#52616B]">Demographics (DM)</span>
                </div>
              </a>

              <a
                href={exportApi.aeUrl(selectedStudyId)}
                download
                className="p-4 rounded-xl border border-[#D9E2DC] bg-[#F7F8F5] hover:bg-[#FFF5F5] hover:border-[#FECACA] flex items-center space-x-3 transition-colors group"
              >
                <FileSpreadsheet className="w-6 h-6 text-[#C62828] group-hover:scale-110 transition-transform" />
                <div className="text-left">
                  <span className="text-xs font-bold text-[#172026] block">{t('reg_btn_download_ae')}</span>
                  <span className="text-[10px] text-[#52616B]">Adverse Events (AE)</span>
                </div>
              </a>

              <a
                href={exportApi.ieUrl(selectedStudyId)}
                download
                className="p-4 rounded-xl border border-[#D9E2DC] bg-[#F7F8F5] hover:bg-[#EFF6FF] hover:border-[#BFDBFE] flex items-center space-x-3 transition-colors group"
              >
                <FileSpreadsheet className="w-6 h-6 text-[#1D4ED8] group-hover:scale-110 transition-transform" />
                <div className="text-left">
                  <span className="text-xs font-bold text-[#172026] block">{t('reg_btn_download_ie', 'Download SDTM IE CSV')}</span>
                  <span className="text-[10px] text-[#52616B]">Criteria (IE)</span>
                </div>
              </a>

              <a
                href={exportApi.defineUrl(selectedStudyId)}
                download
                className="p-4 rounded-xl border border-[#D9E2DC] bg-[#F7F8F5] hover:bg-[#F0F4F8] hover:border-[#D9E2DC] flex items-center space-x-3 transition-colors group"
              >
                <Download className="w-6 h-6 text-[#17324D] group-hover:scale-110 transition-transform" />
                <div className="text-left">
                  <span className="text-xs font-bold text-[#172026] block">{t('reg_btn_download_xml')}</span>
                  <span className="text-[10px] text-[#52616B]">Define-XML 2.0</span>
                </div>
              </a>
            </div>

            {/* FHIR R4 Inspector */}
            <div className="mt-6 pt-4 border-t border-[#D9E2DC]">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2 text-[#172026] font-bold text-xs">
                  <Code className="w-4 h-4 text-[#166534]" />
                  <span>{t('reg_fhir_hub_title')}</span>
                </div>
                <button
                  onClick={() => handleViewFhir(selectedStudyId)}
                  className="text-xs bg-[#17324D] hover:bg-[#13283E] text-white font-semibold px-3 py-1.5 rounded-lg transition-colors flex items-center space-x-1 cursor-pointer"
                >
                  <span>{t('reg_btn_fetch_fhir')}</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </button>
              </div>

              {fhirData && (
                <div className="bg-[#17324D] text-[#34D399] p-4 rounded-xl font-mono text-[11px] overflow-x-auto max-h-96 border border-white/10">
                  <pre>{JSON.stringify(fhirData, null, 2)}</pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Full Portfolio (Read Only) */}
      {activeNav === 'portfolio' && (
        <div className="bg-white rounded-2xl border border-[#D9E2DC] shadow-xs p-6 space-y-4">
          <h3 className="text-sm font-bold text-[#172026]">{t('reg_tab_portfolio')}</h3>
          <div className="divide-y divide-[#D9E2DC] border border-[#D9E2DC] rounded-xl overflow-hidden">
            {studies.map((s) => (
              <div key={s.id} className="p-4 flex items-center justify-between text-xs hover:bg-[#F7F8F5]">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-[10px] bg-[#F0F4F8] text-[#17324D] border border-[#D9E2DC] px-1.5 py-0.5 rounded font-bold">
                      {s.ctri_registration_number || 'CTRI: PENDING'}
                    </span>
                    <span className="font-bold text-[#172026]">{s.title}</span>
                  </div>
                  <div className="text-[11px] text-[#52616B] mt-1">
                    {t('reg_sponsor')}: {s.sponsor} | {t('reg_phase')}: {s.phase}
                  </div>
                </div>
                <div className="text-right">
                  <span className="font-bold text-[#166534]">
                    {s.enrolled_count} / {s.enrollment_target} {t('pi_enrolled')}
                  </span>
                  <div className="text-[10px] text-[#52616B] uppercase font-semibold">
                    {formatStatus(s.status)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
