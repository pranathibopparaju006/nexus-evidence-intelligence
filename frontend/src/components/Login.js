import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

const Login = () => {
  const navigate = useNavigate();

  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: ''
  });
  const [error, setError] = useState('');

  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);

    try {
      if (!formData.username.trim() || !formData.password) {
        throw new Error('Enter your username and password.');
      }

      if (isLogin) {
        const body = new URLSearchParams();
        body.set('username', formData.username.trim());
        body.set('password', formData.password);
        const response = await api.post('/auth/login', body, {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        });
        localStorage.setItem('token', response.data.access_token);
        navigate('/', { replace: true });
      } else {
        if (!formData.email.trim()) throw new Error('Enter your email address.');
        await api.post('/auth/register', {
          username: formData.username.trim(),
          email: formData.email.trim(),
          password: formData.password,
        });
        const body = new URLSearchParams();
        body.set('username', formData.username.trim());
        body.set('password', formData.password);
        const response = await api.post('/auth/login', body, {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        });
        localStorage.setItem('token', response.data.access_token);
        navigate('/', { replace: true });
      }
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(Array.isArray(detail)
        ? detail.map((item) => item?.msg || String(item)).join(', ')
        : (typeof detail === 'string' ? detail : err?.message || 'Unable to sign in. Check the backend and try again.'));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">

        <h1>NEXUS</h1>

        <p className="subtitle">
          Narrative Evolution & Evidence Intelligence
        </p>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>

          <input
            type="text"
            placeholder="Username"
            value={formData.username}
            onChange={(e) =>
              setFormData({
                ...formData,
                username: e.target.value
              })
            }
            required
          />

          {!isLogin && (
            <input
              type="email"
              placeholder="Email"
              value={formData.email}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  email: e.target.value
                })
              }
              required
            />
          )}

          <input
            type="password"
            placeholder="Password"
            value={formData.password}
            onChange={(e) =>
              setFormData({
                ...formData,
                password: e.target.value
              })
            }
            required
          />

          <button type="submit" className="btn-primary" disabled={isSubmitting}>
            {isSubmitting ? 'Please wait…' : (isLogin ? 'Login' : 'Register')}
          </button>

        </form>

        <p className="toggle-text">
          {isLogin
            ? "Don't have an account? "
            : "Already have an account? "}

          <button
            type="button"
            className="btn-link"
            onClick={() => {
              setIsLogin(!isLogin);
              setError('');
            }}
          >
            {isLogin ? 'Register' : 'Login'}
          </button>
        </p>

      </div>
    </div>
  );
};

export default Login;