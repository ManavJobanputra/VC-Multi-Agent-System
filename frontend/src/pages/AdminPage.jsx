import { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Lock, RefreshCw, Power } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const TOKEN_KEY = 'admin_token';

async function apiFetch(path, token, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });
  if (res.status === 401) {
    sessionStorage.removeItem(TOKEN_KEY);
    throw new Error('Session expired. Please log in again.');
  }
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || `Request failed (${res.status})`);
  }
  return res.json();
}

function LoginForm({ onLoggedIn }) {
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/admin/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      });
      if (!res.ok) throw new Error('Incorrect password.');
      const data = await res.json();
      sessionStorage.setItem(TOKEN_KEY, data.token);
      onLoggedIn(data.token);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-paper flex items-center justify-center p-4 phase-in">
      <form onSubmit={handleSubmit} className="w-full max-w-sm bg-card border border-border rounded-xl p-8">
        <div className="w-10 h-10 rounded-full bg-accent flex items-center justify-center mb-5">
          <Lock className="w-4.5 h-4.5 text-coral" />
        </div>
        <h1 className="font-display text-2xl text-ink mb-1">Admin</h1>
        <p className="text-sm text-ink-soft mb-6">Enter the admin password to continue.</p>

        <div className="space-y-2 mb-4">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoFocus
          />
        </div>

        {error && <p className="text-sm text-maroon mb-4">{error}</p>}

        <Button type="submit" disabled={!password || loading} className="w-full">
          {loading ? 'Checking…' : 'Log In'}
        </Button>
      </form>
    </div>
  );
}

function ConfigField({ fieldKey, field, draft, onChange }) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={fieldKey} className="font-mono text-xs">{fieldKey}</Label>
      <Input
        id={fieldKey}
        type={field.is_secret ? 'password' : 'text'}
        value={draft ?? ''}
        onChange={(e) => onChange(fieldKey, e.target.value)}
        placeholder={field.is_secret ? (field.is_set ? `Set (${field.value}) — leave blank to keep` : 'Not set') : field.value}
      />
    </div>
  );
}

function Dashboard({ token, onLogout }) {
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const [drafts, setDrafts] = useState({});
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState(null);
  const [togglingCron, setTogglingCron] = useState(false);

  const load = useCallback(async () => {
    try {
      const data = await apiFetch('/admin/status', token);
      setStatus(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      if (err.message.includes('expired')) onLogout();
    }
  }, [token, onLogout]);

  useEffect(() => { load(); }, [load]);

  const handleToggleCron = async () => {
    setTogglingCron(true);
    try {
      const cron = await apiFetch('/admin/cron/toggle', token, {
        method: 'POST',
        body: JSON.stringify({ enabled: !status.cron.enabled }),
      });
      setStatus((prev) => ({ ...prev, cron }));
    } catch (err) {
      setError(err.message);
    } finally {
      setTogglingCron(false);
    }
  };

  const handleFieldChange = (key, value) => {
    setDrafts((prev) => ({ ...prev, [key]: value }));
  };

  const handleSave = async () => {
    setSaving(true);
    setSaveMessage(null);
    try {
      const data = await apiFetch('/admin/config', token, {
        method: 'POST',
        body: JSON.stringify({ updates: drafts }),
      });
      setSaveMessage(data.note);
      setDrafts({});
      setStatus((prev) => ({ ...prev, config: data.config }));
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  if (!status) {
    return (
      <div className="min-h-screen bg-paper flex items-center justify-center">
        <p className="text-ink-soft text-sm">{error || 'Loading…'}</p>
      </div>
    );
  }

  const { cron, config } = status;
  const hasDrafts = Object.values(drafts).some((v) => v && v.length > 0);

  return (
    <div className="min-h-screen bg-paper phase-in">
      <div className="border-b border-border">
        <div className="max-w-4xl mx-auto px-6 py-5 flex items-center justify-between">
          <div>
            <h1 className="font-display text-xl text-ink">Admin</h1>
            <p className="text-xs font-mono uppercase tracking-widest text-ink-soft">Backend Controls</p>
          </div>
          <Button variant="ghost" size="sm" onClick={onLogout}>Log Out</Button>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 py-10 space-y-10">
        {error && (
          <div className="bg-destructive/10 text-maroon text-sm px-4 py-3 rounded-lg">{error}</div>
        )}

        {/* Cron */}
        <section className="bg-card border border-border rounded-xl p-6">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h2 className="font-display text-xl text-ink">Keep-Alive Ping</h2>
              <p className="text-sm text-ink-soft mt-0.5">
                Pings {cron.url} every {cron.interval_minutes} minutes.
              </p>
            </div>
            <Button
              variant={cron.enabled ? 'default' : 'outline'}
              onClick={handleToggleCron}
              disabled={togglingCron}
              className="gap-2"
            >
              <Power className="w-4 h-4" />
              {cron.enabled ? 'Enabled' : 'Disabled'}
            </Button>
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-xs text-ink-soft uppercase tracking-wide mb-1">Last Ping</p>
              <p className="text-ink font-mono text-xs">{cron.last_ping_at || 'Never'}</p>
              {cron.last_ping_status !== null && (
                <p className="text-ink-soft text-xs mt-0.5">Status: {String(cron.last_ping_status)}</p>
              )}
            </div>
            <div>
              <p className="text-xs text-ink-soft uppercase tracking-wide mb-1">Next Ping</p>
              <p className="text-ink font-mono text-xs">{cron.next_ping_at || 'Pending'}</p>
            </div>
          </div>
        </section>

        {/* Config */}
        <section className="bg-card border border-border rounded-xl p-6">
          <div className="flex items-center justify-between mb-1">
            <h2 className="font-display text-xl text-ink">Environment Configuration</h2>
            <Button variant="ghost" size="icon" onClick={load}>
              <RefreshCw className="w-4 h-4" />
            </Button>
          </div>
          <p className="text-sm text-ink-soft mb-5">
            Changes are written to .env immediately but require a server restart to take effect.
            Secret fields are masked — leave blank to keep the current value.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
            {Object.entries(config).map(([key, field]) => (
              <ConfigField
                key={key}
                fieldKey={key}
                field={field}
                draft={drafts[key]}
                onChange={handleFieldChange}
              />
            ))}
          </div>

          {saveMessage && <p className="text-sm text-sage mb-4">{saveMessage}</p>}

          <Button onClick={handleSave} disabled={!hasDrafts || saving}>
            {saving ? 'Saving…' : 'Save Changes'}
          </Button>
        </section>
      </div>
    </div>
  );
}

function AdminPage() {
  const [token, setToken] = useState(() => sessionStorage.getItem(TOKEN_KEY));

  const handleLogout = () => {
    sessionStorage.removeItem(TOKEN_KEY);
    setToken(null);
  };

  if (!token) {
    return <LoginForm onLoggedIn={setToken} />;
  }

  return <Dashboard token={token} onLogout={handleLogout} />;
}

export default AdminPage;
