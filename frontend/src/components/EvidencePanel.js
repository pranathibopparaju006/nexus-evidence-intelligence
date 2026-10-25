import React from 'react';
import { useQuery } from 'react-query';
import { AlertTriangle, CheckCircle2, HelpCircle, XCircle, Lightbulb, ChevronDown } from 'lucide-react';
import api from '../services/api';

const statusLabel = s => ({SUPPORTED:'Supported',PARTIALLY_SUPPORTED:'Needs Review',INSUFFICIENT:'More Evidence Needed',CONTRADICTED:'Conflicting Evidence'}[s] || 'Needs Review');
const icon = s => s==='SUPPORTED' ? <CheckCircle2/> : s==='CONTRADICTED' ? <XCircle/> : s==='INSUFFICIENT' ? <HelpCircle/> : <AlertTriangle/>;
const title = (f) => f.evidence?.title || String(f.finding_type || 'Finding').replaceAll('_',' ');

const EvidencePanel = ({ projectId }) => {
 const {data=[],isLoading,isError} = useQuery(['findings',projectId],()=>api.get(`/projects/${projectId}/findings`).then(r=>r.data),{refetchInterval:5000});
 if(isLoading)return <div className="loading">Reviewing evidence...</div>;
 if(isError)return <div className="friendly-error">Could not load findings.</div>;
 const findings=Array.isArray(data)?data:[];
 const seen=new Set(); const unique=findings.filter(f=>{const e=f.evidence||{};const k=`${e.category||f.finding_type}|${e.title||''}|${JSON.stringify(e.entity_pair||'')}`;if(seen.has(k))return false;seen.add(k);return true;});
 const counts={SUPPORTED:0,PARTIALLY_SUPPORTED:0,INSUFFICIENT:0,CONTRADICTED:0};unique.forEach(f=>counts[f.claim_status]=(counts[f.claim_status]||0)+1);
 return <div className="evidence-panel clean-panel">
   <div className="page-title"><div><span className="eyebrow"><AlertTriangle size={15}/> EVIDENCE REVIEW</span><h2>Findings & Recommended Changes</h2><p>Each item below explains what NEXUS noticed, why it matters and what should be checked next.</p></div></div>
   <div className="finding-summary"><div><strong>{unique.length}</strong><span>review signals</span></div><div><strong>{counts.PARTIALLY_SUPPORTED||0}</strong><span>needs review</span></div><div><strong>{counts.INSUFFICIENT||0}</strong><span>needs evidence</span></div><div><strong>{counts.SUPPORTED||0}</strong><span>supported</span></div></div>
   <div className="findings-list">
   {unique.length ? unique.map(f=>{const e=f.evidence||{}; return <article className="human-finding large" key={f.id}>
      <div className={`finding-icon status-${String(f.claim_status).toLowerCase()}`}>{icon(f.claim_status)}</div>
      <div className="human-finding-main"><div className="finding-title-row"><div><span className="finding-category">{e.category || 'Analysis signal'}</span><h3>{title(f)}</h3></div><span className={`status-pill ${String(f.claim_status).toLowerCase()}`}>{statusLabel(f.claim_status)} · {((f.confidence_score||0)*100).toFixed(0)}%</span></div>
      <p className="finding-explanation">{e.explanation || f.abstain_reason || 'NEXUS identified a signal that should be checked against the source.'}</p>
      {e.evidence_summary && <div className="evidence-quote"><b>Source evidence</b><p>{e.evidence_summary}</p></div>}
      {e.recommendation && <div className="recommendation"><Lightbulb size={16}/><div><b>Recommended change</b><span>{e.recommendation}</span></div></div>}
      <details className="technical-details"><summary><ChevronDown size={14}/> Technical evidence</summary><pre>{JSON.stringify(e,null,2)}</pre></details>
      </div>
   </article>}) : <div className="empty-friendly"><CheckCircle2 size={20}/> No issues requiring review were detected.</div>}
   </div>
 </div>;
};
export default EvidencePanel;
