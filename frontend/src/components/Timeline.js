import React from 'react';
import { useQuery } from 'react-query';
import { format, isValid } from 'date-fns';
import { CalendarDays } from 'lucide-react';
import api from '../services/api';

const Timeline = ({ projectId }) => {
  const { data, isLoading, isError, error } = useQuery(
    ['timeline', projectId],
    () => api.get(`/projects/${projectId}/timeline`).then((r) => r.data),
    {
      enabled: Number.isInteger(Number(projectId)) && Number(projectId) > 0,
      refetchInterval: 10000
    }
  );

  if (isLoading) return <div className="loading">Reconstructing the timeline...</div>;
  if (isError) return <div className="friendly-error">Could not load timeline: {error?.response?.data?.detail || error?.message || 'Unknown error'}</div>;

  // The API contract is a list, but accepting a single event object makes the
  // page resilient to older backend versions and cached responses.
  const events = Array.isArray(data) ? data : (data && typeof data === 'object' ? [data] : []);
  const useful = events
    .filter((event) => event && event.timestamp && event.description)
    .map((event) => ({ ...event, parsedDate: new Date(event.timestamp) }))
    .filter((event) => isValid(event.parsedDate))
    .sort((a, b) => a.parsedDate - b.parsedDate);

  return (
    <div className="timeline-container clean-panel">
      <div className="page-title"><div>
        <span className="eyebrow"><CalendarDays size={15}/> NARRATIVE EVOLUTION</span>
        <h2>What happened, and when?</h2>
        <p>Dated source observations are shown in chronological order. Dates reflect extracted metadata when available.</p>
      </div></div>
      <div className="timeline">
        {useful.length ? useful.map((event, index) => (
          <div className="timeline-event human-timeline" key={`${event.node_ids?.[0] || event.timestamp}-${index}`}>
            <div className="timeline-dot" />
            <div className="event-time">{format(event.parsedDate, 'MMM dd, yyyy')}</div>
            <div className="event-type">{String(event.event_type || 'Source observation').replaceAll('_', ' ')}</div>
            <div className="event-description">{event.description}</div>
          </div>
        )) : <div className="empty-friendly">No dated source observations are available yet. Upload evidence with a date and run analysis.</div>}
      </div>
    </div>
  );
};

export default Timeline;

