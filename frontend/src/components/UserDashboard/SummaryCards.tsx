export function SummaryCards() {
  return (
    <div className="flex flex-col gap-6">
      <div className="bg-surface-container-low p-6 rounded-[2rem] flex items-center justify-between">
        <div className="space-y-1">
          <p className="text-xs font-bold text-on-surface-variant uppercase tracking-widest">Transaction Volume</p>
          <p className="text-2xl font-headline font-extrabold text-on-surface">Live Data</p>
        </div>
        <div className="w-12 h-12 bg-surface-container-lowest rounded-xl flex items-center justify-center">
          <span className="material-symbols-outlined text-primary" data-icon="account_balance_wallet">account_balance_wallet</span>
        </div>
      </div>
      <div className="bg-error-container p-6 rounded-[2rem] flex items-center justify-between">
        <div className="space-y-1">
          <p className="text-xs font-bold text-on-error-container uppercase tracking-widest">Fraud Guard</p>
          <p className="text-2xl font-headline font-extrabold text-on-error-container">Active</p>
        </div>
        <div className="w-12 h-12 bg-white/40 rounded-xl flex items-center justify-center">
          <span className="material-symbols-outlined text-on-error-container" data-icon="gpp_bad">gpp_bad</span>
        </div>
      </div>
    </div>
  );
}
