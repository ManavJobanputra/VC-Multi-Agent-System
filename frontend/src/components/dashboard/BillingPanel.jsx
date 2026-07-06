import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Loader2 } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const PACK_ORDER = ['single', 'five', 'fifteen'];

function loadRazorpayScript() {
  return new Promise((resolve) => {
    if (window.Razorpay) return resolve(true);
    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
}

function BillingPanel({ token, user, onCreditsUpdated }) {
  const [packs, setPacks] = useState(null);
  const [buyingPack, setBuyingPack] = useState(null);
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState(null);
  const [justPurchased, setJustPurchased] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/billing/packs`)
      .then((res) => res.json())
      .then(setPacks)
      .catch(() => setError('Could not load pricing.'));
  }, []);

  const pollForCredits = async (startingCredits) => {
    setConfirming(true);
    for (let i = 0; i < 10; i++) {
      await new Promise((r) => setTimeout(r, 2000));
      try {
        const res = await fetch(`${API_BASE}/me`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const data = await res.json();
          if (data.credits > startingCredits) {
            onCreditsUpdated(data);
            setConfirming(false);
            setJustPurchased(true);
            return;
          }
        }
      } catch (e) {
        // keep polling
      }
    }
    setConfirming(false);
    setError('Payment received but credits are still processing. Refresh in a moment.');
  };

  const handleBuy = async (pack) => {
    setError(null);
    setJustPurchased(false);
    setBuyingPack(pack);

    const scriptLoaded = await loadRazorpayScript();
    if (!scriptLoaded) {
      setError('Could not load the payment provider. Check your connection and try again.');
      setBuyingPack(null);
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/billing/create-order`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ pack }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || 'Could not start checkout.');
      }
      const order = await res.json();

      const rzp = new window.Razorpay({
        key: order.key_id,
        amount: order.amount,
        currency: order.currency,
        order_id: order.order_id,
        name: 'VC Pitch Analyzer',
        description: packs[pack].label,
        theme: { color: '#e15b3f' },
        handler: () => pollForCredits(user?.credits ?? 0),
        modal: { ondismiss: () => setBuyingPack(null) },
      });
      rzp.on('payment.failed', () => {
        setError('Payment failed. No charge was made.');
        setBuyingPack(null);
      });
      rzp.open();
    } catch (err) {
      setError(err.message);
      setBuyingPack(null);
    }
  };

  return (
    <div>
      <p className="text-xs font-mono uppercase tracking-widest text-coral mb-2">04 · Billing</p>
      <h1 className="font-display text-3xl text-ink mb-1">Credits &amp; Sessions</h1>
      <p className="text-ink-soft mb-8">No subscription - credits never expire.</p>

      <div className="bg-card border border-border rounded-lg p-5 flex items-center justify-between mb-10">
        <div>
          <p className="text-[11px] text-ink-soft uppercase tracking-wide">Current Balance</p>
          <p className="font-display text-3xl text-ink">{user?.credits ?? 0} <span className="text-sm text-ink-soft font-sans">credits</span></p>
        </div>
        <p className="text-sm text-ink-soft">{user?.free_session_used ? 'Free session used' : 'Free session available'}</p>
      </div>

      {confirming && (
        <div className="flex items-center gap-2 mb-6 text-sm text-ink-soft">
          <Loader2 className="w-4 h-4 animate-spin text-coral" /> Confirming your payment…
        </div>
      )}

      {justPurchased && <p className="text-sm text-sage mb-6">Credits added to your account.</p>}
      {error && <p className="text-sm text-maroon mb-6">{error}</p>}

      {packs && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
          {PACK_ORDER.map((key) => {
            const pack = packs[key];
            const perSession = Math.round(pack.amount_inr / pack.credits);
            return (
              <Card key={key} className={key === 'five' ? 'border-coral' : ''}>
                <CardHeader>
                  <p className="text-xs font-mono uppercase tracking-widest text-ink-soft">{pack.label}</p>
                  <p className="font-display text-3xl text-ink mt-2">₹{pack.amount_inr}</p>
                  <p className="text-xs text-ink-soft mt-1">₹{perSession} / session</p>
                </CardHeader>
                <CardContent>
                  <Button
                    onClick={() => handleBuy(key)}
                    disabled={buyingPack === key}
                    className="w-full"
                    variant={key === 'five' ? 'default' : 'outline'}
                  >
                    {buyingPack === key ? 'Opening checkout…' : 'Buy'}
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default BillingPanel;
