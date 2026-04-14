import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import apiClient from "../../api/client";

const paymentSchema = z.object({
  merchant_upi: z.string().min(3, "Required"),
  amount: z.number().positive(),
  device_id: z.string(),
  ip_address: z.string(),
});

type PaymentFormType = z.infer<typeof paymentSchema>;

interface Props {
  deviceData: { device_id: string, ip_address: string };
  onFraudDetected: (score: number, reason: string) => void;
}

export function PaymentForm({ deviceData, onFraudDetected }: Props) {
  const queryClient = useQueryClient();
  const { register, handleSubmit, reset, formState: { errors } } = useForm<PaymentFormType>({
    resolver: zodResolver(paymentSchema),
    defaultValues: {
      ...deviceData,
      amount: 0,
      merchant_upi: ""
    }
  });

  const payMutation = useMutation({
    mutationFn: async (data: PaymentFormType) => {
      const res = await apiClient.post("/transactions/pay", data);
      return res.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      if (data.status === "APPROVED") {
        toast.success(`Sent ₹${data.amount} to ${data.merchant_upi}`);
        reset({ ...deviceData, amount: 0, merchant_upi: "" });
      } else if (data.status === "BLOCKED_FRAUD") {
        onFraudDetected(data.fraud_score, data.fraud_reason || "Unusual transaction pattern detected.");
      } else {
        toast(`Transaction ${data.status}`);
      }
    },
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Payment failed");
    }
  });

  return (
    <div className="col-span-1 lg:col-span-2 bg-surface-container-lowest rounded-[2rem] p-8 flex flex-col justify-between relative overflow-hidden group">
      <div className="relative z-10 space-y-6">
        <div className="space-y-2">
          <h2 className="text-3xl font-headline font-extrabold tracking-tighter text-on-surface">Secure Payment</h2>
          <p className="text-on-surface-variant max-w-md">Instantly transfer funds with bank-grade encryption and real-time fraud monitoring.</p>
        </div>
        <form onSubmit={handleSubmit((d) => payMutation.mutate(d))} className="space-y-4 max-w-sm relative z-20">
          <div>
            <label className="block text-xs font-bold uppercase tracking-widest text-on-surface-variant mb-1">Merchant UPI</label>
            <input 
              {...register("merchant_upi")}
              className="w-full px-4 py-3 bg-surface-container-highest rounded-xl focus:bg-surface-container-lowest focus:ring-1 focus:ring-primary outline-none transition-all"
              placeholder="merchant@bank"
            />
            {errors.merchant_upi && <p className="text-error text-xs mt-1">{errors.merchant_upi.message}</p>}
          </div>
          <div>
            <label className="block text-xs font-bold uppercase tracking-widest text-on-surface-variant mb-1">Amount (₹)</label>
            <input 
              {...register("amount", { valueAsNumber: true })}
              type="number"
              step="0.01"
              className="w-full px-4 py-3 bg-surface-container-highest rounded-xl focus:bg-surface-container-lowest focus:ring-1 focus:ring-primary outline-none transition-all"
              placeholder="0.00"
            />
            {errors.amount && <p className="text-error text-xs mt-1">{errors.amount.message}</p>}
          </div>
          <div className="pt-2">
            <button 
              type="submit" 
              disabled={payMutation.isPending}
              className="bg-primary text-on-primary px-8 py-3 rounded-xl font-headline font-bold text-sm hover:bg-primary-container shadow-xl transition-all active:scale-95 disabled:opacity-50"
            >
              {payMutation.isPending ? "Processing..." : "Send Money"}
            </button>
          </div>
        </form>
      </div>
      <div className="absolute -right-12 -bottom-12 w-64 h-64 bg-primary-fixed-dim/20 rounded-full blur-3xl group-hover:scale-110 transition-transform duration-700 pointer-events-none"></div>
    </div>
  );
}
