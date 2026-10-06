import { cn } from '../utils/cn';

interface ProgressProps {
    value?: number;
    className?: string;
}

/** Accessible horizontal progress bar (0-100). */
export function Progress({ value = 0, className }: ProgressProps) {
    const pct = Math.max(0, Math.min(100, value));
    return (
        <div
            role="progressbar"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={Math.round(pct)}
            className={cn('relative h-2 w-full overflow-hidden rounded-full bg-primary/20', className)}
        >
            <div className="h-full bg-primary transition-all" style={{ width: `${pct}%` }} />
        </div>
    );
}
