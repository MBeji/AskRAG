import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useToast } from '../contexts/ToastContext';

const Register = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { showToast } = useToast();
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const response = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password }),
      });
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Registration failed');
      }
      showToast('success', 'Registration Successful!', 'Your account has been created. Please log in.');
      navigate('/login');
    } catch (err) {
      setError(err.message);
      showToast('error', 'Registration Failed', err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-10 p-6 bg-white rounded shadow">
      <h2 className="text-2xl font-bold mb-4">Register</h2>
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className="block mb-1">Username</label>
          <input type="text" className="w-full border px-3 py-2 rounded" value={username} onChange={e => setUsername(e.target.value)} required />
        </div>
        <div className="mb-4">
          <label className="block mb-1">Email</label>
          <input type="email" className="w-full border px-3 py-2 rounded" value={email} onChange={e => setEmail(e.target.value)} required />
        </div>
        <div className="mb-4">
          <label className="block mb-1">Password</label>
          <input type="password" className="w-full border px-3 py-2 rounded" value={password} onChange={e => setPassword(e.target.value)} required />
        </div>
        {error && <div className="text-red-500 mb-2">{error}</div>}
        <button type="submit" className="w-full bg-blue-600 text-white py-2 rounded" disabled={loading}>
          {loading ? 'Registering...' : 'Register'}
        </button>
      </form>
      <div className="mt-4 text-sm text-center">
        Already have an account? <a href="/login" className="text-blue-600">Login</a>
      </div>
    </div>
  );
};

export default Register;
