import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useNavigate } from 'react-router-dom';
import { Plus, Folder, Trash2, Activity, LogOut, AlertCircle } from 'lucide-react';
import api from '../services/api';

const readableError = (error) => {
  const detail = error?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map((item) => item?.msg || JSON.stringify(item)).join(', ');
  if (detail) return JSON.stringify(detail);
  if (error?.code === 'ERR_NETWORK') return 'Cannot connect to the NEXUS API. Check that the backend is running at http://localhost:8000.';
  return error?.message || 'Request failed. Check the backend logs and try again.';
};

const Dashboard = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [newProjectName, setNewProjectName] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [formError, setFormError] = useState('');

  const { data: projects, isLoading, error: projectsError } = useQuery(
    'projects',
    () => api.get('/projects').then((res) => {
      const data = res.data;
      if (Array.isArray(data)) return data;
      if (Array.isArray(data?.value)) return data.value;
      if (Array.isArray(data?.projects)) return data.projects;
      if (Array.isArray(data?.items)) return data.items;
      return [];
    }),
    { retry: 1 }
  );

  const createMutation = useMutation(
    (data) => api.post('/projects', data).then((res) => res.data),
    {
      onSuccess: (project) => {
        setFormError('');
        setNewProjectName('');
        setIsCreating(false);
        queryClient.invalidateQueries('projects');
        if (project?.id !== undefined && project?.id !== null) {
          navigate(`/project/${project.id}`);
        }
      },
      onError: (error) => setFormError(readableError(error)),
    }
  );

  const deleteMutation = useMutation(
    (id) => api.delete(`/projects/${id}`).then((res) => res.data),
    {
      onSuccess: () => queryClient.invalidateQueries('projects'),
    }
  );

  const handleCreate = (e) => {
    e.preventDefault();
    setFormError('');
    const name = newProjectName.trim();
    if (!name) {
      setFormError('Enter a project name.');
      return;
    }
    createMutation.mutate({ name, description: '' });
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  if (isLoading) return <div className="loading">Loading projects...</div>;

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div>
          <h1>NEXUS</h1>
          <p className="subtitle">Narrative Evolution &amp; Evidence Intelligence System</p>
        </div>
        <button className="btn-icon" onClick={handleLogout} aria-label="Log out" title="Log out">
          <LogOut size={20} />
        </button>
      </header>

      <div className="dashboard-content">
        <div className="create-section">
          {!isCreating ? (
            <button className="btn-primary" onClick={() => { setFormError(''); setIsCreating(true); }}>
              <Plus size={20} /> New Investigation
            </button>
          ) : (
            <form onSubmit={handleCreate} className="create-form">
              <input
                type="text"
                placeholder="Project name"
                value={newProjectName}
                onChange={(e) => { setNewProjectName(e.target.value); setFormError(''); }}
                autoFocus
                maxLength={160}
                aria-label="Project name"
              />
              <button type="submit" className="btn-primary" disabled={createMutation.isLoading}>
                {createMutation.isLoading ? 'Creatingâ€¦' : 'Create'}
              </button>
              <button type="button" className="btn-secondary" disabled={createMutation.isLoading}
                onClick={() => { setIsCreating(false); setFormError(''); }}>
                Cancel
              </button>
            </form>
          )}
          {formError && (
            <div className="mutation-error" role="alert">
              <AlertCircle size={17} />
              <span>{formError}</span>
            </div>
          )}
        </div>

        {projectsError && (
          <div className="mutation-error" role="alert">
            <AlertCircle size={17} />
            <span>{readableError(projectsError)}</span>
          </div>
        )}

        <div className="projects-grid">
          {(Array.isArray(projects) ? projects : []).map((project) => (
            <div key={project.id} className="project-card" onClick={() => navigate(`/project/${project.id}`)}>
              <div className="project-header">
                <Folder size={24} />
                <h3>{project.name}</h3>
              </div>
              <div className="project-meta">
                <span className={`status status-${String(project.status || 'created').toLowerCase()}`}>
                  <Activity size={14} /> {project.status || 'created'}
                </span>
                <span className="date">
                  {project.created_at ? new Date(project.created_at).toLocaleDateString() : 'Just created'}
                </span>
              </div>
              <button className="delete-btn" aria-label={`Delete ${project.name}`} title="Delete project"
                onClick={(e) => { e.stopPropagation(); deleteMutation.mutate(project.id); }}>
                <Trash2 size={16} />
              </button>
            </div>
          ))}
          {!projectsError && Array.isArray(projects) && projects.length === 0 && (
            <div className="empty-friendly">No investigations yet. Create your first project to get started.</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

