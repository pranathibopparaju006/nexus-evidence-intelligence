import React from 'react';
import { useQuery } from 'react-query';
import { Brain, Users, CalendarDays, MapPin, ChevronDown } from 'lucide-react';
import api from '../services/api';

const formatError = (error) => {
  const d = error?.response?.data?.detail;
  if (Array.isArray(d)) return d.map(x => x?.msg || JSON.stringify(x)).join('; ');
  if (d && typeof d === 'object') return d.msg || d.message || JSON.stringify(d);
  return d || error?.message || 'Unknown error';
};

const NarrativePanel = ({ projectId }) => {
  const { data: narratives = [], isLoading, isError, error } = useQuery(['narratives', projectId], () => api.get(`/projects/${projectId}/narratives`).then(r => r.data), { refetchInterval: 5000 });
  if (isLoading) return <div className="loading">Preparing narrative summary...</div>;
  if (isError) return <div className="friendly-error">Could not load the narrative summary: {formatError(error)}</div>;
  if (!narratives.length) return <div className="empty-friendly">No narrative summary is available yet. Upload a document and run Analysis.</div>;
  const dna = narratives[0].narrative_dna || {};
  const list = (v, limit=20) => Array.isArray(v) ? v.slice(0, limit) : [];
  const label = (value) => typeof value === 'object'
    ? (value?.name || value?.label || '')
    : String(value || '');
  return <div className="narrative-panel clean-panel">
    <div className="page-title"><div><span className="eyebrow"><Brain size={15}/> UNDERSTANDING THE DOCUMENT</span><h2>Narrative Summary</h2><p>Here is the story NEXUS extracted from the source material, in plain language.</p></div></div>
    <div className="main-claim"><h3>Main narrative</h3><p>{dna.core_claim || 'No main narrative was extracted.'}</p></div>
    <div className="clean-info-grid">
      <div className="info-block"><h4><Users size={16}/> Key entities</h4><div className="chips">{list(dna.entities).map((x,i)=><span className="chip" key={i}>{label(x)}</span>)}</div></div>
      <div className="info-block"><h4><CalendarDays size={16}/> Key events</h4><ul className="plain-list">{list(dna.events,8).map((x,i)=><li key={i}>{label(x)}</li>)}</ul></div>
      <div className="info-block"><h4><MapPin size={16}/> Locations</h4><div className="chips">{list(dna.locations,10).map((x,i)=><span className="chip location" key={i}>{label(x)}</span>)}</div></div>
    </div>
    <details className="technical-details"><summary><ChevronDown size={15}/> Technical extraction details</summary><div className="technical-grid"><div><b>Framing</b><span>{dna.emotional_framing || 'neutral'}</span></div><div><b>Extraction method</b><span>{dna.extraction_method || 'standard'}</span></div><div><b>Key phrases</b><span>{list(dna.key_phrases,8).join(', ') || 'None'}</span></div></div></details>
  </div>;
};
export default NarrativePanel;
