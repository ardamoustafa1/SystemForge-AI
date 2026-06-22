import { LucideIcon } from "lucide-react";
import { Button } from "@/components/ui/button";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function EmptyState({ icon: Icon, title, description, actionLabel, onAction }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-white/10 bg-white/[0.01] px-6 py-24 text-center">
      <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-white/[0.03] ring-1 ring-white/5">
        <Icon className="h-8 w-8 text-white/40" strokeWidth={1.5} />
      </div>
      <h3 className="text-xl font-medium text-white/90">{title}</h3>
      <p className="mt-2 max-w-sm text-sm text-white/50">{description}</p>
      {actionLabel && onAction && (
        <Button 
          onClick={onAction} 
          className="mt-8 rounded-full bg-indigo-500 hover:bg-indigo-600 text-white shadow-[0_0_15px_rgba(99,102,241,0.2)] transition-all hover:scale-105 active:scale-95"
        >
          {actionLabel}
        </Button>
      )}
    </div>
  );
}
