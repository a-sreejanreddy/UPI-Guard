import { useState } from "react";
import { useAuthStore } from "../store/authStore";
import { Sidebar } from "../components/UserDashboard/Sidebar";
import { SummaryCards } from "../components/UserDashboard/SummaryCards";
import { TransactionTable } from "../components/UserDashboard/TransactionTable";
import { PaymentForm } from "../components/UserDashboard/PaymentForm";
import { FraudAlertModal } from "../components/UserDashboard/FraudAlertModal";

export function UserDashboard() {
  const { user } = useAuthStore();
  const [fraudAlert, setFraudAlert] = useState<{ score: number, reason: string } | null>(null);

  // Fallback device data for MVP simulation
  const deviceData = {
    device_id: "device-xyz123",
    ip_address: "192.168.1.10"
  };

  return (
    <div className="bg-surface text-on-surface flex min-h-screen">
      <Sidebar />
      <main className="flex-1 md:ml-64 flex flex-col min-h-screen">
        <header className="fixed top-0 w-full md:w-[calc(100%-16rem)] z-40 flex justify-between items-center px-6 h-16 bg-surface/80 backdrop-blur-xl shadow-xl shadow-on-surface/5">
          <div className="flex flex-col">
            <h1 className="font-headline font-bold text-lg text-primary">Welcome Back</h1>
            <p className="text-xs text-on-surface-variant">Your financial security overview</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3 pl-4 border-l border-outline-variant/20">
              <div className="text-right hidden sm:block">
                <p className="text-sm font-bold text-primary">{user?.name || "User"}</p>
                <p className="text-xs text-on-surface-variant">Premium User</p>
              </div>
            </div>
          </div>
        </header>

        <div className="pt-24 pb-12 px-6 lg:px-10 space-y-8 max-w-7xl mx-auto w-full">
          <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <PaymentForm 
              deviceData={deviceData}
              onFraudDetected={(score, reason) => setFraudAlert({ score, reason })} 
            />
            <SummaryCards />
          </section>
          <section className="bg-surface-container-low rounded-[2rem] p-1 overflow-hidden">
             <TransactionTable />
          </section>
        </div>
      </main>
      
      {fraudAlert && (
          <FraudAlertModal 
            score={fraudAlert.score} 
            reason={fraudAlert.reason} 
            onClose={() => setFraudAlert(null)} 
          />
      )}
    </div>
  );
}
