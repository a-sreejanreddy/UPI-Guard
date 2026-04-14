import { useQuery } from "@tanstack/react-query";
import apiClient from "../../api/client";
import { LoadingSpinner } from "../LoadingSpinner";

interface Transaction {
  id: number;
  merchant_upi: string;
  amount: number;
  status: "APPROVED" | "BLOCKED_FRAUD" | "PENDING" | "ADMIN_OVERRIDDEN";
  fraud_score: number;
  created_at: string;
}

export function TransactionTable() {
  const { data, isLoading } = useQuery<Transaction[]>({
    queryKey: ["transactions"],
    queryFn: async () => {
      const resp = await apiClient.get("/transactions/my");
      return resp.data;
    },
    refetchInterval: 5000
  });

  return (
    <div className="bg-surface-container-lowest rounded-t-[2rem] p-8 min-h-[400px]">
      <div className="flex justify-between items-end mb-8">
        <div className="space-y-1">
          <h3 className="text-2xl font-headline font-extrabold text-on-surface tracking-tight">Recent Transactions</h3>
          <p className="text-sm text-on-surface-variant">Live updates from your verified banking channels.</p>
        </div>
      </div>
      {isLoading ? (
         <div className="py-12"><LoadingSpinner /></div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="text-on-surface-variant uppercase text-[10px] font-bold tracking-[0.2em]">
                <th className="pb-6 px-4">Merchant</th>
                <th className="pb-6 px-4">Amount (₹)</th>
                <th className="pb-6 px-4">Time</th>
                <th className="pb-6 px-4">Status</th>
                <th className="pb-6 px-4 hidden md:table-cell">Risk Score</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant/10">
              {data && data.length > 0 ? (
                data.map((txn) => (
                  <tr key={txn.id} className="group hover:bg-surface-container-low/50 transition-colors">
                    <td className="py-5 px-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-secondary-container flex items-center justify-center font-bold text-on-secondary-container">
                          {txn.merchant_upi.substring(0, 2).toUpperCase()}
                        </div>
                        <div>
                          <p className="text-sm font-bold text-on-surface">{txn.merchant_upi}</p>
                        </div>
                      </div>
                    </td>
                    <td className={`py-5 px-4 text-sm font-headline font-bold ${txn.status === 'BLOCKED_FRAUD' ? 'text-error' : 'text-on-surface'}`}>
                       ₹{txn.amount.toFixed(2)}
                    </td>
                    <td className="py-5 px-4 text-sm text-on-surface-variant">
                      {new Date(txn.created_at).toLocaleString(undefined, {
                         month: 'short', day: 'numeric', year: 'numeric',
                         hour: '2-digit', minute:'2-digit'
                      })}
                    </td>
                    <td className="py-5 px-4">
                      {txn.status === "APPROVED" && (
                        <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-[11px] font-bold bg-tertiary-container text-on-tertiary-container">
                          <span className="w-1.5 h-1.5 rounded-full bg-on-tertiary-container"></span>
                          Approved
                        </span>
                      )}
                      {txn.status === "BLOCKED_FRAUD" && (
                        <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-[11px] font-bold bg-error-container text-on-error-container">
                          <span className="w-1.5 h-1.5 rounded-full bg-on-error-container"></span>
                          Blocked (Fraud)
                        </span>
                      )}
                      {txn.status === "ADMIN_OVERRIDDEN" && (
                        <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-[11px] font-bold bg-secondary-container text-on-secondary-container">
                          <span className="w-1.5 h-1.5 rounded-full bg-on-secondary-container"></span>
                          Overridden
                        </span>
                      )}
                    </td>
                    <td className="py-5 px-4 hidden md:table-cell text-xs font-bold">
                        {(txn.fraud_score * 100).toFixed(1)}%
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                   <td colSpan={5} className="py-8 text-center text-sm text-on-surface-variant">No transactions found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
