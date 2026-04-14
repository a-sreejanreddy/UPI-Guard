interface Props {
  score: number;
  reason: string;
  onClose: () => void;
}

export function FraudAlertModal({ score, reason, onClose }: Props) {
  const percentage = (score * 100).toFixed(1);
  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm px-4">
      <div className="bg-surface-container-lowest rounded-[2rem] max-w-md w-full p-8 shadow-2xl animate-in zoom-in-95 duration-200 border border-error/20">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-16 h-16 rounded-full bg-error-container flex items-center justify-center shrink-0">
             <span className="material-symbols-outlined text-on-error-container text-3xl" data-icon="gpp_bad">gpp_bad</span>
          </div>
          <div>
            <h2 className="text-2xl font-headline font-extrabold text-error">Access Blocked</h2>
            <p className="text-on-surface-variant text-sm">Security AI Intervention</p>
          </div>
        </div>
        
        <div className="bg-surface-container-highest p-6 rounded-2xl mb-6">
           <p className="text-xs uppercase tracking-widest text-on-surface-variant font-bold mb-2">Threat Assessment</p>
           <div className="flex items-end justify-between">
              <span className="text-5xl font-headline font-black text-error">{percentage}%</span>
              <span className="text-sm font-bold text-on-surface">Fraud Probability</span>
           </div>
           
           <div className="w-full bg-outline-variant/30 h-2 rounded-full mt-4 overflow-hidden">
              <div className="bg-error h-full" style={{ width: `${percentage}%` }}></div>
           </div>
           
           <p className="mt-4 text-sm text-on-surface-variant"><strong>Reason:</strong> {reason}</p>
        </div>

        <button 
          onClick={onClose}
          className="w-full bg-error text-on-error py-4 rounded-full font-bold shadow-lg hover:bg-[#93000a] transition-all"
        >
          Understood, Dismiss
        </button>
      </div>
    </div>
  );
}
