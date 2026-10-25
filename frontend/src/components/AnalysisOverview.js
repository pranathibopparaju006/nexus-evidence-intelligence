import React from 'react';
import { useQuery } from 'react-query';
import { AlertTriangle, CheckCircle2, FileSearch, Network, CalendarDays, Lightbulb, ChevronRight } from 'lucide-react';
import api from '../services/api';

const pct = (v) => `${((Number(v) || 0) * 100).toFixed(0)}%`;
const clean = (v) => String(v || '').replaceAll('_', ' ');

const statusText = (s) => ({
  SUPPORTED: 'Supported',
  PARTIALLY_SUPPORTED: 'Needs Review',
  INSUFFICIENT: 'More Evidence Needed',
  CONTRADICTED: 'Conflicting Evidence'
}[s] || 'Needs Review');

const AnalysisOverview = ({ projectId, onNavigate }) => {
  const { data: narratives = [], isLoading: loadingN } = useQuery(
    ['narratives', projectId], () => api.get(`/projects/${projectId}/narratives`).then(r => r.data), { refetchInterval: 5000 }
  );
  const { data: findings = [], isLoading: loadingF } = useQuery(
    ['findings', projectId], () => api.get(`/projects/${projectId}/findings`).then(r => r.data), { refetchInterval: 5000 }
  );
  if (loadingN || loadingF) return <div className="analysis-overview loading-panel">Preparing your analysis...</div>;

  const first = narratives[0] || {};
  const dna = first.narrative_dna || {};
  const uniqueFindings = [];
  const seen = new Set();
  (Array.isArray(findings) ? findings : []).forEach((f) => {
    const e = f.evidence || {};
    const key = `${e.category || f.finding_type}|${e.title || f.finding_type}|${e.entity_pair || ''}`;
    if (!seen.has(key)) { seen.add(key); uniqueFindings.push(f); }
  });
  const reviewFindings = uniqueFindings.slice(0, 5);
  const rawEntities = Array.isArray(dna.entities) ? dna.entities : [];
  const entityName = (entity) => typeof entity === 'object'
    ? (entity?.name || entity?.label || '')
    : String(entity || '');
  const entityType = (entity) => typeof entity === 'object'
    ? String(entity?.type || '').toLowerCase()
    : '';
  const groupedEntities = {
    Person: rawEntities.filter(e => entityType(e) === 'person').slice(0, 6),
    Organization: rawEntities.filter(e => entityType(e) === 'organization').slice(0, 6),
    Location: rawEntities.filter(e => entityType(e) === 'location').slice(0, 6),
    System: rawEntities.filter(e => entityType(e) === 'system').slice(0, 8),
  };
  const entities = rawEntities.slice(0, 10);
  const events = Array.isArray(dna.events) ? dna.events.slice(0, 6) : [];
  const locations = Array.isArray(dna.locations) ? dna.locations.slice(0, 8) : [];

  return (
    <div className="analysis-overview">
      <section className="hero-summary">
        <div className="hero-kicker"><FileSearch size={16}/> AI DOCUMENT ANALYSIS</div>
        <h2>What did NEXUS understand?</h2>
        <p className="hero-claim">{dna.core_claim || 'Upload a document and run analysis to generate a human-readable narrative summary.'}</p>
        <div className="hero-meta">
          <span><strong>{entities.length}</strong> key entities</span>
          <span><strong>{events.length}</strong> notable events</span>
          <span><strong>{uniqueFindings.length}</strong> review signals</span>
        </div>
      </section>

      <section className="analysis-steps">
        {['Read document', 'Extract meaning', 'Connect evidence', 'Review issues', 'Explain results'].map((label, i) => (
          <div className="analysis-step" key={label}><span>{i + 1}</span><div>{label}</div>{i < 4 && <ChevronRight size={16}/>}</div>
        ))}
      </section>

      <section className="overview-grid">
        <div className="overview-card context-card">
          <div className="section-heading"><span><Network size={18}/> Key information</span><button onClick={() => onNavigate('narratives')}>View details</button></div>
          <div className="chip-section">
            <label>People</label>
            <div className="chips">
              {groupedEntities.Person.length
                ? groupedEntities.Person.map((e,i)=><span className="chip" key={i}>{entityName(e)}</span>)
                : <span className="muted">None detected</span>}
            </div>
          </div>
          <div className="chip-section">
            <label>Organizations</label>
            <div className="chips">
              {groupedEntities.Organization.length
                ? groupedEntities.Organization.map((e,i)=><span className="chip" key={i}>{entityName(e)}</span>)
                : <span className="muted">None detected</span>}
            </div>
          </div>
          <div className="chip-section">
            <label>Systems</label>
            <div className="chips">
              {groupedEntities.System.length
                ? groupedEntities.System.map((e,i)=><span className="chip" key={i}>{entityName(e)}</span>)
                : <span className="muted">None detected</span>}
            </div>
          </div>
          <div className="chip-section">
            <label>Locations</label>
            <div className="chips">
              {locations.length
                ? locations.map((e,i)=><span className="chip location" key={i}>{entityName(e)}</span>)
                : <span className="muted">None detected</span>}
            </div>
          </div>
        </div>
        <div className="overview-card snapshot-card">
          <div className="section-heading"><span><CalendarDays size={18}/> Narrative flow</span><button onClick={() => onNavigate('timeline')}>Open timeline</button></div>
          {events.length ? events.map((e,i)=><div className="flow-item" key={i}><span>{i+1}</span><p>{String(e)}</p></div>) : <p className="muted">No dated or event-like statements detected.</p>}
        </div>
      </section>

      <section className="findings-hero">
        <div className="section-heading"><span><AlertTriangle size={19}/> What needs attention?</span><button onClick={() => onNavigate('findings')}>See all findings</button></div>
        {reviewFindings.length ? reviewFindings.map((f) => {
          const e = f.evidence || {};
          const status = statusText(f.claim_status);
          const title = e.title || clean(f.finding_type);
          const explanation = e.explanation || f.abstain_reason || 'The system identified a signal that should be reviewed against the source evidence.';
          return <div className="human-finding" key={f.id}>
            <div className="finding-icon"><AlertTriangle size={19}/></div>
            <div className="human-finding-main">
              <div className="finding-title-row"><h3>{title}</h3><span className={`status-pill ${String(f.claim_status).toLowerCase()}`}>{status} · {pct(f.confidence_score)}</span></div>
              <p>{explanation}</p>
              {e.recommendation && <div className="recommendation"><Lightbulb size={15}/><strong>Suggested action:</strong> {e.recommendation}</div>}
            </div>
          </div>;
        }) : <div className="empty-friendly"><CheckCircle2 size={20}/> No review signals were generated from the current source.</div>}
      </section>

      <section className="overview-footer">
        <div><strong>Important:</strong> NEXUS highlights evidence-based review signals. It does not treat a signal as proof by itself.</div>
        <button onClick={() => onNavigate('graph')}>Explore Evidence Graph →</button>
      </section>
    </div>
  );
};
export default AnalysisOverview;
