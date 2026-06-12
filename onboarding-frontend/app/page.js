'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';

const API = 'http://127.0.0.1:8000';

export default function Home() {
  const [tabId, setTabId] = useState(null);

  const [user, setUser] = useState(null);
  const [tickets, setTickets] = useState([]);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [newTicket, setNewTicket] = useState({
    employee_name: '', role: '', start_date: '', hardware: 'Standard'
  });

  useEffect(() => {
    let id = sessionStorage.getItem('tabId');
    if (!id) {
      id = Date.now().toString() + Math.random().toString(36).substr(2, 5);
      sessionStorage.setItem('tabId', id);
    }
    setTabId(id);
  }, []);

  useEffect(() => {
    if (!tabId) return;

    const token = localStorage.getItem(`token_${tabId}`);
    const role = localStorage.getItem(`role_${tabId}`);
    if (token && role) {
      setUser({ token, role });
      loadTickets(token);
    }
  }, [tabId]);

  const loadTickets = async (token) => {
    try {
      const res = await axios.get(`${API}/tickets`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTickets(res.data);
    } catch (error) {
      if (error.response?.status === 401) {
        logout();
      }
    }
  };

  const login = async () => {
    try {
      const res = await axios.post(`${API}/login`, { username, password });
      localStorage.setItem(`token_${tabId}`, res.data.token);
      localStorage.setItem(`role_${tabId}`, res.data.role);
      setUser({ token: res.data.token, role: res.data.role });
      loadTickets(res.data.token);
      setError('');
    } catch {
      setError('Username sau parola gresita!');
    }
  };

  const logout = () => {
    localStorage.removeItem(`token_${tabId}`);
    localStorage.removeItem(`role_${tabId}`);
    setUser(null);
    setTickets([]);
  };

  const createTicket = async () => {
    await axios.post(`${API}/tickets`, newTicket, {
      headers: { Authorization: `Bearer ${user.token}` }
    });
    setNewTicket({ employee_name: '', role: '', start_date: '', hardware: 'Standard' });
    loadTickets(user.token);
  };

  const approve = async (id) => {
    await axios.post(`${API}/tickets/${id}/approve`, {}, {
      headers: { Authorization: `Bearer ${user.token}` }
    });
    loadTickets(user.token);
  };

  const reject = async (id) => {
    await axios.post(`${API}/tickets/${id}/reject`, {}, {
      headers: { Authorization: `Bearer ${user.token}` }
    });
    loadTickets(user.token);
  };

  const edit = async (t) => {
    const employee_name = prompt('Nume angajat:', t.employee_name);
    const role = prompt('Rol:', t.role);
    const start_date = prompt('Data start (YYYY-MM-DD):', t.start_date);
    const hardware = prompt('Hardware (Standard/Premium):', t.hardware);
    await axios.put(`${API}/tickets/${t.id}`, { employee_name, role, start_date, hardware }, {
      headers: { Authorization: `Bearer ${user.token}` }
    });
    loadTickets(user.token);
  };

  if (!tabId) {
    return <div>Loading...</div>;
  }

  if (!user) {
    return (
      <div style={{ maxWidth: 400, margin: '100px auto', fontFamily: 'sans-serif', padding: 20 }}>
        <h1>Onboarding System</h1>
        <input placeholder="Username" value={username}
          onChange={e => setUsername(e.target.value)}
          style={{ display: 'block', width: '100%', padding: 8, marginBottom: 8 }} />
        <input placeholder="Parola" type="password" value={password}
          onChange={e => setPassword(e.target.value)}
          style={{ display: 'block', width: '100%', padding: 8, marginBottom: 8 }} />
        {error && <p style={{ color: 'red' }}>{error}</p>}
        <button onClick={login}
          style={{ width: '100%', padding: 10, backgroundColor: '#3b82f6', color: 'white', border: 'none', borderRadius: 6, cursor: 'pointer' }}>
          Login
        </button>
        <div style={{ marginTop: 20, fontSize: 13, color: '#666' }}>
          <b>Useri test:</b><br />
          hr_user / parola_hr<br />
          manager_user / parola_manager<br />
          finance_user / parola_finance<br />
          it_user / parola_it
        </div>
      </div>
    );
  }

  return (
    <div style={{ fontFamily: 'sans-serif', padding: 20, maxWidth: 1100, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h1 style={{ margin: 0 }}>Onboarding System</h1>
        <div>
          <span style={{ marginRight: 12, fontWeight: 'bold', color: '#3b82f6' }}>{user.role}</span>
          <button onClick={logout} style={{ padding: '6px 14px', cursor: 'pointer' }}>Logout</button>
        </div>
      </div>

      {user.role === 'HR' && (
      <div style={{ background: '#1a1a1a', padding: 16, borderRadius: 8, marginBottom: 20, color: 'white' }}>
        <h3 style={{ marginTop: 0, color: 'white' }}>Creeaza tichet nou</h3>
        <input placeholder="Nume angajat" value={newTicket.employee_name}
          onChange={e => setNewTicket({ ...newTicket, employee_name: e.target.value })}
          style={{ padding: 8, marginRight: 8, marginBottom: 8, background: '#2d2d2d', color: 'white', border: '1px solid #444' }} />
        <input placeholder="Rol" value={newTicket.role}
          onChange={e => setNewTicket({ ...newTicket, role: e.target.value })}
          style={{ padding: 8, marginRight: 8, marginBottom: 8, background: '#2d2d2d', color: 'white', border: '1px solid #444' }} />
        <input type="date" value={newTicket.start_date}
          onChange={e => setNewTicket({ ...newTicket, start_date: e.target.value })}
          style={{ padding: 8, marginRight: 8, marginBottom: 8, background: '#2d2d2d', color: 'white', border: '1px solid #444' }} />
        <select value={newTicket.hardware}
          onChange={e => setNewTicket({ ...newTicket, hardware: e.target.value })}
          style={{ padding: 8, marginRight: 8, marginBottom: 8, background: '#2d2d2d', color: 'white', border: '1px solid #444' }}>
          <option>Standard</option>
          <option>Premium</option>
        </select>
        <button onClick={createTicket}
          style={{ padding: '8px 16px', backgroundColor: '#3b82f6', color: 'white', border: 'none', borderRadius: 6, cursor: 'pointer' }}>
          Creeaza
        </button>
      </div>
    )}

      <table style={{ width: '100%', borderCollapse: 'collapse', background: 'white' }}>
        <thead>
          <tr style={{ background: '#f1f5f9' }}>
            <th style={th}>ID</th>
            <th style={th}>Angajat</th>
            <th style={th}>Rol</th>
            <th style={th}>Data start</th>
            <th style={th}>Hardware</th>
            <th style={th}>Status</th>
            <th style={th}>Actiuni</th>
          </tr>
        </thead>
        <tbody>
          {tickets.map(t => (
            <tr key={t.id} style={{ borderBottom: '1px solid #e2e8f0' }}>
              <td style={td}>{t.id}</td>
              <td style={td}>{t.employee_name}</td>
              <td style={td}>{t.role}</td>
              <td style={td}>{t.start_date}</td>
              <td style={td}>{t.hardware}</td>
              <td style={td}>
                <span style={{ padding: '3px 10px', borderRadius: 12, fontSize: 12, fontWeight: 'bold', background: statusColor(t.status), color: 'white' }}>
                  {t.status}
                </span>
              </td>
              <td style={td}>
                {((user.role === 'Manager' && t.status === 'PENDING_MANAGER') ||
                  (user.role === 'Finance' && t.status === 'PENDING_FINANCE') ||
                  (user.role === 'IT' && t.status === 'PENDING_IT')) && (
                  <>
                    <button onClick={() => approve(t.id)}
                      style={{ marginRight: 6, padding: '5px 12px', background: '#22c55e', color: 'white', border: 'none', borderRadius: 5, cursor: 'pointer' }}>
                      Aproba
                    </button>
                    <button onClick={() => reject(t.id)}
                      style={{ padding: '5px 12px', background: '#ef4444', color: 'white', border: 'none', borderRadius: 5, cursor: 'pointer' }}>
                      Respinge
                    </button>
                  </>
                )}
                {user.role === 'HR' && t.status === 'Needs Rework' && (
                  <button onClick={() => edit(t)}
                    style={{ padding: '5px 12px', background: '#f97316', color: 'white', border: 'none', borderRadius: 5, cursor: 'pointer' }}>
                    Editeaza
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
 
      {tickets.length === 0 && (
        <p style={{ color: '#888', textAlign: 'center', marginTop: 20 }}>Nu sunt tichete.</p>
      )}
    </div>
  );
}

function statusColor(status) {
  if (status === 'COMPLETED') return '#22c55e';
  if (status === 'Needs Rework') return '#f97316';
  if (status === 'PENDING_MANAGER') return '#3b82f6';
  if (status === 'PENDING_FINANCE') return '#a855f7';
  if (status === 'PENDING_IT') return '#06b6d4';
  return '#6b7280';
}

const th = { padding: '10px 14px', textAlign: 'left', fontWeight: 'bold', fontSize: 13, color: '#1e293b', background: '#f1f5f9' };
const td = { padding: '10px 14px', fontSize: 14, color: '#0f172a' };