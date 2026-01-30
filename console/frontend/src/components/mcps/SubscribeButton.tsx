'use client';

import { useState } from 'react';
import { Check, Loader2 } from 'lucide-react';
import { colors, fonts } from './theme';

interface SubscribeButtonProps {
  mcpName: string;
  isSubscribed: boolean;
  onSubscribe: (mcpName: string) => Promise<void>;
  price: string;
}

export default function SubscribeButton({ mcpName, isSubscribed, onSubscribe, price }: SubscribeButtonProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubscribe = async (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent card click

    if (isSubscribed) return;

    setLoading(true);
    setError(null);

    try {
      await onSubscribe(mcpName);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Subscription failed');
      setTimeout(() => setError(null), 3000);
    } finally {
      setLoading(false);
    }
  };

  if (isSubscribed) {
    return (
      <button
        disabled
        className="w-full py-3 px-4 rounded-lg font-semibold text-sm flex items-center justify-center gap-2 cursor-default border"
        style={{
          backgroundColor: colors.dark,
          color: colors.light,
          borderColor: colors.dark,
          fontFamily: fonts.heading
        }}
      >
        <Check className="w-4 h-4" />
        Subscribed
      </button>
    );
  }

  if (error) {
    return (
      <button
        onClick={handleSubscribe}
        className="w-full py-3 px-4 rounded-lg font-semibold text-sm border transition-all"
        style={{
          backgroundColor: '#dc2626',
          color: '#fff',
          borderColor: '#dc2626',
          fontFamily: fonts.heading
        }}
      >
        Failed - Retry
      </button>
    );
  }

  return (
    <button
      onClick={handleSubscribe}
      disabled={loading}
      className="w-full py-3 px-4 rounded-lg font-semibold text-sm transition-all border flex items-center justify-center gap-2"
      style={{
        backgroundColor: loading ? colors.midGray : colors.orange,
        color: colors.light,
        borderColor: loading ? colors.midGray : colors.orange,
        fontFamily: fonts.heading,
        cursor: loading ? 'not-allowed' : 'pointer',
        opacity: loading ? 0.7 : 1
      }}
      onMouseEnter={(e) => {
        if (!loading) {
          e.currentTarget.style.backgroundColor = colors.orange + 'dd';
        }
      }}
      onMouseLeave={(e) => {
        if (!loading) {
          e.currentTarget.style.backgroundColor = colors.orange;
        }
      }}
    >
      {loading ? (
        <>
          <Loader2 className="w-4 h-4 animate-spin" />
          Subscribing...
        </>
      ) : (
        <>
          Subscribe {price}
        </>
      )}
    </button>
  );
}
