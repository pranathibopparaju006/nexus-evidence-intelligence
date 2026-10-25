import React, { useState } from 'react';
import { useQuery, useMutation } from 'react-query';
import { Play, Loader, CheckCircle, AlertCircle } from 'lucide-react';
import api from '../services/api';

const AnalysisStatus = ({ projectId }) => {
  const [jobId, setJobId] = useState(null);

  const { data: status } = useQuery(
    ['analysis', projectId, jobId],
    () =>
      api
        .get(`/projects/${projectId}/analyze/${jobId}/status`)
        .then(res => res.data),
    {
      enabled: !!jobId,
      refetchInterval: 3000,
    }
  );

  const analysisMutation = useMutation(
    () =>
      api
        .post(`/projects/${projectId}/analyze`, {
          analysis_type: 'full',
          options: {},
        })
        .then(res => res.data),
    {
      onSuccess: (data) => {
        setJobId(data.job_id);
      },
    }
  );

  const getStatusIcon = () => {
    if (status?.status === 'running') {
      return <Loader className="spin" />;
    }

    if (status?.status === 'completed') {
      return <CheckCircle className="icon-green" />;
    }

    if (status?.status === 'error') {
      return <AlertCircle className="icon-red" />;
    }

    return <Play />;
  };

  if (status?.status === 'completed') {
    return (
      <div className="analysis-status">
        <div className="status-completed">
          {getStatusIcon()}
          <span>Analysis Complete</span>
        </div>
      </div>
    );
  }

  if (status?.status === 'running') {
    return (
      <div className="analysis-status">
        <div className="status-running">
          {getStatusIcon()}
          <span>{status.current_stage || 'Analyzing...'}</span>
        </div>
      </div>
    );
  }

  if (status?.status === 'error') {
    return (
      <div className="analysis-status">
        <div className="status-running">
          {getStatusIcon()}
          <span>{status.message || 'Analysis failed'}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="analysis-status">
      <button
        className="btn-analyze"
        onClick={() => {
          setJobId(null);
          analysisMutation.mutate();
        }}
        disabled={analysisMutation.isLoading}
      >
        {getStatusIcon()}
        <span>
          {analysisMutation.isLoading ? 'Starting...' : 'Run Analysis'}
        </span>
      </button>
    </div>
  );
};

export default AnalysisStatus;