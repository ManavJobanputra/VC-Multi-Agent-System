import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import DashboardLayout from '@/components/dashboard/DashboardLayout';
import OverviewPanel from '@/components/dashboard/OverviewPanel';
import SessionsPanel from '@/components/dashboard/SessionsPanel';
import ProgressPanel from '@/components/dashboard/ProgressPanel';
import BillingPanel from '@/components/dashboard/BillingPanel';

function DashboardPage({ token, user, onLogout, onCreditsUpdated }) {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    if (!token) navigate('/signin');
  }, [token, navigate]);

  if (!token) return null;

  return (
    <DashboardLayout activeTab={activeTab} onTabChange={setActiveTab} user={user} onLogout={onLogout}>
      {activeTab === 'overview' && <OverviewPanel token={token} user={user} onTabChange={setActiveTab} />}
      {activeTab === 'sessions' && <SessionsPanel token={token} />}
      {activeTab === 'progress' && <ProgressPanel token={token} />}
      {activeTab === 'billing' && <BillingPanel token={token} user={user} onCreditsUpdated={onCreditsUpdated} />}
    </DashboardLayout>
  );
}

export default DashboardPage;
