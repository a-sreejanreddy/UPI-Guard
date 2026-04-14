import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import apiClient from "../api/client";

interface SMSInboxPanelProps {
  mobile: string;
}

export function SMSInboxPanel({ mobile }: SMSInboxPanelProps) {
  const { data: inbox } = useQuery<{ mobile: string; otp: string; expires_in_seconds: number; message: string }>({
    queryKey: ["otp-inbox", mobile],
    queryFn: async () => {
      const res = await apiClient.get(`/auth/otp-inbox/${mobile}`);
      return res.data;
    },
    refetchInterval: 3000,
    staleTime: 0,
  });

  const [timeLeft, setTimeLeft] = useState<number | null>(null);

  useEffect(() => {
    if (inbox?.expires_in_seconds !== undefined) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setTimeLeft(inbox.expires_in_seconds);
    }
  }, [inbox?.expires_in_seconds]);

  useEffect(() => {
    if (timeLeft === null || timeLeft <= 0) return;
    const timer = setInterval(() => {
      setTimeLeft(prev => (prev !== null && prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, [timeLeft]);

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  return (
    <div className="bg-surface-container-highest rounded-2xl p-4 shadow-lg border border-outline-variant/30 flex items-start gap-4 animate-in slide-in-from-bottom-4 duration-500">
      <div className="bg-tertiary-container text-on-tertiary-container w-10 h-10 rounded-full flex items-center justify-center shrink-0">
        <span className="material-symbols-outlined text-xl" data-icon="chat">chat</span>
      </div>
      <div>
        <p className="text-sm font-bold text-on-surface">UPI Guard (Simulator)</p>
        <p className="text-xs text-on-surface-variant mt-1">
          {inbox && inbox.otp ? (
             <span>Your UPI Guard login code is <strong className="text-on-surface text-base ml-1">{inbox.otp}</strong>. Valid for {timeLeft !== null ? formatTime(timeLeft) : '...'}</span>
          ) : (
            <span className="animate-pulse">Waiting for SMS...</span>
          )}
        </p>
      </div>
    </div>
  );
}
