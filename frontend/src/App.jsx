import { useState, useEffect, useCallback } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import HomePage from './pages/HomePage';
import PersonaSelect from './pages/PersonaSelect';
import LoadingScreen from './components/LoadingScreen';
import ConversationInterface from './pages/ConversationInterface';
import AdminPage from './pages/AdminPage';
import SignInPage from './pages/SignInPage';
import AuthCallbackPage from './pages/AuthCallbackPage';
import PaywallPage from './pages/PaywallPage';
import './App.css';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const AUTH_TOKEN_KEY = 'auth_token';

const readFileAsBase64 = (file) => new Promise((resolve, reject) => {
  const reader = new FileReader();
  reader.onload = () => {
    const result = reader.result || '';
    const base64 = typeof result === 'string' ? result.split(',')[1] || '' : '';
    resolve(base64);
  };
  reader.onerror = reject;
  reader.readAsDataURL(file);
});

function App() {
  const navigate = useNavigate();
  const [authToken, setAuthToken] = useState(() => localStorage.getItem(AUTH_TOKEN_KEY));
  const [user, setUser] = useState(null);
  const [selectedPersona, setSelectedPersona] = useState(null);
  const [pitchData, setPitchData] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [agentProgress, setAgentProgress] = useState({});

  const refreshUser = useCallback(async (token) => {
    try {
      const res = await fetch(`${API_BASE}/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setUser(await res.json());
      } else {
        localStorage.removeItem(AUTH_TOKEN_KEY);
        setAuthToken(null);
        setUser(null);
      }
    } catch (e) {
      console.error('Failed to load account:', e);
    }
  }, []);

  useEffect(() => {
    if (authToken) refreshUser(authToken);
  }, [authToken, refreshUser]);

  const handleAuthenticated = (token, userInfo) => {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
    setAuthToken(token);
    setUser(userInfo);
  };

  const handleBeginSession = () => {
    navigate(authToken ? '/personas' : '/signin');
  };

  const handlePersonaSelect = (persona) => {
    setSelectedPersona(persona);
    navigate('/pitch');
  };

  const handleBackToHome = () => {
    setPitchData(null);
    setResult(null);
    navigate('/pitch');
  };

  const handlePitchSubmit = async ({ formData, file }) => {
    if (!authToken) {
      navigate('/signin');
      return;
    }

    setPitchData({ formData, fileName: file?.name });
    setError(null);
    setAgentProgress({});
    navigate('/evaluating');

    try {
      let pitchFileBase64 = '';
      if (file) {
        pitchFileBase64 = await readFileAsBase64(file);
      }

      const payload = {
        pitch_data: {
          content: `${formData.problemStatement}\n\n${formData.solution}\n\n${formData.traction}`,
          company_name: formData.companyName,
          founder_name: '',
          email: '',
          industry: formData.industry,
          stage: formData.currentStage,
          pitch_file_name: file?.name,
          pitch_file_base64: pitchFileBase64,
        },
        persona: selectedPersona,
      };

      // Start polling for progress
      const pollInterval = setInterval(async () => {
        try {
          const progressRes = await fetch(`${API_BASE}/progress`);
          if (progressRes.ok) {
            const progress = await progressRes.json();
            setAgentProgress(progress);
          }
        } catch (e) {
          console.error('Progress poll error:', e);
        }
      }, 500);

      const response = await fetch(`${API_BASE}/evaluate_pitch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify(payload),
      });

      clearInterval(pollInterval);

      if (response.status === 401) {
        navigate('/signin');
        return;
      }

      if (response.status === 402) {
        navigate('/paywall');
        return;
      }

      if (!response.ok) {
        const detail = await response.text();
        throw new Error(detail || 'Failed to submit pitch');
      }

      const data = await response.json();
      setResult(data);
      refreshUser(authToken);

      // Pass pitch data with session_id to conversation interface
      setPitchData({
        formData,
        fileName: file?.name,
        session_id: data.session_id
      });

      navigate('/session');
    } catch (e) {
      console.error(e);
      setError(e.message || 'Submission failed');
      navigate('/pitch');
    }
  };

  return (
    <Routes>
      <Route path="/" element={<LandingPage onStart={handleBeginSession} />} />
      <Route path="/signin" element={<SignInPage />} />
      <Route path="/auth/callback" element={<AuthCallbackPage onAuthenticated={handleAuthenticated} />} />
      <Route
        path="/paywall"
        element={
          <PaywallPage
            token={authToken}
            user={user}
            onCreditsUpdated={setUser}
          />
        }
      />
      <Route path="/personas" element={<PersonaSelect onPersonaSelect={handlePersonaSelect} />} />
      <Route
        path="/pitch"
        element={
          <>
            {error && (
              <div className="bg-destructive/10 text-destructive text-sm px-6 py-3 text-center font-medium">
                {error}
              </div>
            )}
            <HomePage onSubmit={handlePitchSubmit} />
          </>
        }
      />
      <Route path="/evaluating" element={<LoadingScreen agentProgress={agentProgress} />} />
      <Route path="/admin" element={<AdminPage />} />
      <Route
        path="/session"
        element={
          <ConversationInterface
            pitch={pitchData?.formData}
            persona={selectedPersona}
            onBack={handleBackToHome}
            evaluation={result}
            sessionId={pitchData?.session_id}
          />
        }
      />
    </Routes>
  );
}

export default App;
