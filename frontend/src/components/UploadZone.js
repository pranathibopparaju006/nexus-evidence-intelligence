import React, { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from 'react-query';
import { Upload } from 'lucide-react';
import api from '../services/api';

const formatApiError = (error, fallback) => {
  const detail = error?.response?.data?.detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => item?.msg || JSON.stringify(item)).join('; ');
  }
  if (detail && typeof detail === 'object') {
    return detail.msg || detail.message || JSON.stringify(detail);
  }
  return detail || error?.message || fallback;
};

const UploadZone = ({ projectId }) => {
  const queryClient = useQueryClient();
  const [sourceId, setSourceId] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  const uploadMutation = useMutation(
    (file) => {
      const formData = new FormData();
      formData.append('file', file);
      return api.post(`/projects/${projectId}/ingest`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      }).then(res => res.data);
    },
    {
      onSuccess: (data) => {
        setErrorMessage('');
        const id = Number(data?.id);
        if (!Number.isInteger(id) || id <= 0) {
          setErrorMessage('Upload succeeded but the server did not return a valid upload ID.');
          return;
        }
        setSourceId(id);
        queryClient.invalidateQueries(['ingest', projectId]);
        queryClient.invalidateQueries(['graph', projectId]);
        queryClient.invalidateQueries(['timeline', projectId]);
      },
      onError: (error) => {
        setErrorMessage(formatApiError(error, 'Upload failed. Check that the backend is running.'));
      }
    }
  );

  const { data: uploadStatus } = useQuery(
    ['ingest-status', projectId, sourceId],
    () => api.get(`/projects/${projectId}/ingest/${sourceId}/status`).then(res => res.data),
    {
      enabled: Boolean(sourceId),
      refetchInterval: (data) => {
        if (!data) return 1500;
        return ['pending', 'processing'].includes(data.ingestion_status) ? 1500 : false;
      },
      retry: 2,
      onError: (error) => {
        setErrorMessage(formatApiError(error, 'Failed to get upload status. Refresh the page and try again.'));
      }
    }
  );

  useEffect(() => {
    if (uploadStatus?.ingestion_status === 'completed') {
      queryClient.invalidateQueries(['graph', projectId]);
      queryClient.invalidateQueries(['timeline', projectId]);
    }
    if (uploadStatus?.ingestion_status === 'error') {
      const detail = uploadStatus?.extracted_metadata?.error;
      setErrorMessage(typeof detail === 'string' ? detail : (detail ? JSON.stringify(detail) : 'File processing failed.'));
    }
  }, [uploadStatus, projectId, queryClient]);

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setErrorMessage('');
    setSourceId(null);
    uploadMutation.mutate(file);
    event.target.value = '';
  };

  const status = uploadStatus?.ingestion_status;

  return (
    <div className="upload-zone">
      <Upload size={32} />
      <label htmlFor="nexus-file-upload" style={{ display: 'block', cursor: 'pointer', marginTop: '12px' }}>
        <strong>Select a file</strong>
        <p>Click here to upload PDF, TXT, JSON, CSV or Image</p>
      </label>
      <input
        id="nexus-file-upload"
        type="file"
        accept=".pdf,.txt,.json,.csv,.png,.jpg,.jpeg"
        onChange={handleFileChange}
        disabled={uploadMutation.isLoading}
        style={{ display: 'block', width: '100%', marginTop: '15px', cursor: 'pointer' }}
      />
      <span className="upload-hint">Supported: PDF, TXT, JSON, CSV, Images</span>

      {uploadMutation.isLoading && <div className="upload-progress">Uploading...</div>}
      {!uploadMutation.isLoading && status === 'pending' && <div className="upload-progress">Upload received — waiting for processing...</div>}
      {!uploadMutation.isLoading && status === 'processing' && <div className="upload-progress">Processing file...</div>}
      {!uploadMutation.isLoading && status === 'completed' && <div className="upload-progress">Upload & processing complete ✓</div>}
      {errorMessage && <div className="upload-progress">{errorMessage}</div>}
    </div>
  );
};

export default UploadZone;
