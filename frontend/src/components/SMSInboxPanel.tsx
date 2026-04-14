import { useQuery } from "@tanstack/react-query";
import apiClient from "../api/client";

interface SMSInboxPanelProps {
  mobile: string;
}

export function SMSInboxPanel({ mobile }: SMSInboxPanelProps) {
  const { data: inbox } = useQuery<{ otp: string; expires_at: string; created_at: string }>({
    queryKey: ["otp-inbox", mobile],
    queryFn: async () => {
      const res = await apiClient.get(`/auth/otp-inbox/${mobile}`);
      return res.data;
    },
    refetchInterval: 3000,
    staleTime: 0,
  });

  return (
    <div className="bg-surface-container-highest rounded-2xl p-4 shadow-lg border border-outline-variant/30 flex items-start gap-4 animate-in slide-in-from-bottom-4 duration-500">
      <div className="bg-tertiary-container text-on-tertiary-container w-10 h-10 rounded-full flex items-center justify-center shrink-0">
        <span className="material-symbols-outlined text-xl" data-icon="chat">chat</span>
      </div>
      <div>
        <p className="text-sm font-bold text-on-surface">UPI Guard (Simulator)</p>
        <p className="text-xs text-on-surface-variant mt-1">
          {inbox ? (
             <span>Your UPI Guard login code is <strong className="text-on-surface text-base ml-1">{inbox.otp}</strong>. Valid for 5 minutes.</span>
          ) : (
            <span className="animate-pulse">Waiting for SMS...</span>
          )}
        </p>
      </div>
    </div>
  );
}
