import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useNavigate } from "react-router-dom";
import { useAuthStore, type User } from "../store/authStore";
import apiClient from "../api/client";
import { SMSInboxPanel } from "../components/SMSInboxPanel";

const mobileSchema = z.object({
  mobile: z.string().regex(/^\d{10}$/, "Mobile number must be 10 digits"),
});

const otpSchema = z.object({
  otp: z.string().regex(/^\d{6}$/, "OTP must be 6 digits"),
});

type MobileForm = z.infer<typeof mobileSchema>;
type OtpForm = z.infer<typeof otpSchema>;

export function Login() {
  const [step, setStep] = useState<"mobile" | "otp">("mobile");
  const [mobileNumber, setMobileNumber] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  
  const navigate = useNavigate();
  const setAuth = useAuthStore((state) => state.setAuth);

  const { register: registerMobile, handleSubmit: handleMobileSubmit, formState: { errors: mobileErrors } } = useForm<MobileForm>({
    resolver: zodResolver(mobileSchema),
  });

  const { register: registerOtp, handleSubmit: handleOtpSubmit, formState: { errors: otpErrors } } = useForm<OtpForm>({
    resolver: zodResolver(otpSchema),
  });

  const onMobileSubmit = async (data: MobileForm) => {
    setIsLoading(true);
    setErrorMsg("");
    try {
      await apiClient.post("/auth/request-otp", { mobile: data.mobile });
      setMobileNumber(data.mobile);
      setStep("otp");
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (error: any) {
      setErrorMsg(error.response?.data?.detail || "Failed to request OTP");
    } finally {
      setIsLoading(false);
    }
  };

  const onOtpSubmit = async (data: OtpForm) => {
    setIsLoading(true);
    setErrorMsg("");
    try {
      const resp = await apiClient.post("/auth/verify-otp", {
        mobile: mobileNumber,
        otp: data.otp,
      });
      const user: User = { 
        id: resp.data.user_id, 
        mobile: mobileNumber,
        role: resp.data.role, 
        name: resp.data.name 
      };
      setAuth(user);
      
      if (user.role === "admin") navigate("/admin");
      else if (user.role === "merchant") navigate("/merchant");
      else navigate("/user");
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (error: any) {
      setErrorMsg(error.response?.data?.detail || "Invalid OTP");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-surface text-on-surface min-h-screen flex flex-col items-center justify-center p-6 relative overflow-hidden">
      {/* Atmospheric Background Decoration */}
      <div className="absolute top-0 left-0 w-full h-full pointer-events-none overflow-hidden z-0">
        <div className="absolute -top-[10%] -left-[5%] w-[40%] h-[40%] rounded-full bg-secondary-fixed/20 blur-[120px]"></div>
        <div className="absolute -bottom-[10%] -right-[5%] w-[40%] h-[40%] rounded-full bg-primary-fixed/20 blur-[120px]"></div>
      </div>

      <main className="w-full max-w-md z-10">
        <div className="mb-10 text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary rounded-full mb-4 shadow-xl shadow-primary/10">
            <span className="material-symbols-outlined text-on-primary text-3xl" data-icon="shield_with_heart" style={{fontVariationSettings: "'FILL' 1"}}>shield_with_heart</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tighter text-on-surface font-headline">
            UPI Guard
          </h1>
          <p className="text-on-surface-variant font-medium mt-2">Atmospheric Security for Modern Banking</p>
        </div>

        <div className="bg-surface-container-lowest rounded-[2rem] p-8 md:p-10 shadow-xl shadow-on-surface/5 flex flex-col gap-8">
          {errorMsg && (
            <div className="p-3 rounded-lg bg-error-container text-on-error-container text-sm font-semibold text-center border border-error/20">
              {errorMsg}
            </div>
          )}

          {step === "mobile" && (
            <section className="space-y-6" id="identification-step">
              <div className="space-y-2">
                <h2 className="text-xl font-bold text-on-surface font-headline">Welcome back</h2>
                <p className="text-sm text-on-surface-variant">Enter your mobile number to receive a secure login code.</p>
              </div>
              <form onSubmit={handleMobileSubmit(onMobileSubmit)} className="space-y-4">
                <div className="group">
                  <label className="block text-xs font-bold uppercase tracking-widest text-on-surface-variant mb-2 ml-1">Mobile Number</label>
                  <div className="relative flex items-center">
                    <span className="absolute left-4 text-on-surface-variant font-semibold border-r border-outline-variant pr-3">+91</span>
                    <input 
                      {...registerMobile("mobile")} 
                      className={`w-full pl-16 pr-4 py-4 bg-surface-container-highest rounded-full border-none focus:ring-1 focus:ring-primary focus:bg-surface-container-lowest transition-all text-lg font-medium tracking-widest placeholder:text-outline placeholder:tracking-normal ${mobileErrors.mobile ? 'ring-1 ring-error' : ''}`}
                      maxLength={10} 
                      placeholder="00000 00000" 
                      type="tel"
                      disabled={isLoading}
                    />
                  </div>
                  {mobileErrors.mobile && <p className="text-error text-xs mt-1 ml-2">{mobileErrors.mobile.message}</p>}
                </div>
                <button 
                  type="submit" 
                  disabled={isLoading}
                  className="w-full bg-primary text-on-primary font-bold py-4 rounded-full shadow-lg hover:bg-primary-container transition-all active:scale-[0.98] flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {isLoading ? "Sending..." : "Send OTP"}
                  <span className="material-symbols-outlined text-xl" data-icon="arrow_forward">arrow_forward</span>
                </button>
              </form>
            </section>
          )}

          {step === "otp" && (
            <section className="space-y-6 pt-4" id="otp-step">
              <div className="space-y-2">
                <h2 className="text-xl font-bold text-on-surface font-headline">Verify Identity</h2>
                <p className="text-sm text-on-surface-variant">We've sent a 6-digit code to your registered mobile number.</p>
              </div>
              <form onSubmit={handleOtpSubmit(onOtpSubmit)} className="space-y-8">
                <div>
                  <input 
                    {...registerOtp("otp")}
                    className="w-full text-center tracking-[1em] text-2xl font-bold bg-surface-container-highest rounded-xl py-4 border-none focus:ring-2 focus:ring-primary focus:bg-surface-container-lowest transition-all"
                    maxLength={6} 
                    placeholder="------"
                    type="text"
                    disabled={isLoading}
                  />
                  {otpErrors.otp && <p className="text-error text-xs mt-2 text-center">{otpErrors.otp.message}</p>}
                </div>

                <div className="space-y-4">
                  <button 
                    type="submit" 
                    disabled={isLoading}
                    className="w-full bg-primary text-on-primary font-bold py-4 rounded-full shadow-lg hover:bg-primary-container transition-all active:scale-[0.98] flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {isLoading ? "Verifying..." : "Verify & Login"}
                    <span className="material-symbols-outlined text-xl" data-icon="lock_open">lock_open</span>
                  </button>
                  <div className="text-center">
                    <button type="button" onClick={() => { setStep("mobile"); setErrorMsg(""); }} className="text-sm font-semibold text-secondary hover:text-on-secondary-container transition-colors">
                      Change Mobile Number
                    </button>
                  </div>
                </div>
              </form>
            </section>
          )}

        </div>
        
        {step === "otp" && (
           <div className="mt-8">
             <SMSInboxPanel mobile={mobileNumber} />
           </div>
        )}

        <footer className="mt-8 text-center space-y-4">
          <div className="flex items-center justify-center gap-6">
            {/* TODO: Add functional link for Privacy Policy */}
            <a href="#" className="text-xs font-bold uppercase tracking-widest text-on-surface-variant hover:text-primary transition-colors">Privacy Policy</a>
            {/* TODO: Add functional link for Help Center */}
            <a href="#" className="text-xs font-bold uppercase tracking-widest text-on-surface-variant hover:text-primary transition-colors">Help Center</a>
          </div>
          <div className="flex flex-col items-center gap-2">
            <p className="text-[10px] text-on-surface-variant italic">Trusted by over 2 million secure UPI users nationwide.</p>
          </div>
        </footer>
      </main>

      <div className="fixed bottom-0 left-0 p-12 opacity-5 hidden lg:block select-none">
        <span className="material-symbols-outlined text-[200px]" data-icon="fingerprint">fingerprint</span>
      </div>
      <div className="fixed top-0 right-0 p-12 opacity-5 hidden lg:block select-none">
        <span className="material-symbols-outlined text-[200px]" data-icon="security">security</span>
      </div>
    </div>
  );
}
