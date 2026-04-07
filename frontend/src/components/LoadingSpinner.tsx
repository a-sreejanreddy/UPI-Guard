import { Loader2 } from "lucide-react";

export function LoadingSpinner({ className = "" }: { className?: string }) {
  return (
    <div className="flex items-center justify-center p-4" role="status" aria-live="polite">
      <Loader2 className={`h-8 w-8 animate-spin text-blue-600 ${className}`} aria-hidden="true" />
      <span className="sr-only">Loading...</span>
    </div>
  );
}
