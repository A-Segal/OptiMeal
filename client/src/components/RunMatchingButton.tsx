import { useState } from "react";
import { base_url } from "../config";

export type MatchingResult = {
  message: string;
  created_count: number;
  total_requested_today: number;
  unassigned: number;
  unique_centers_used: number;
  assignments: Array<{
    recipient_id: number;
    recipient_name: string;
    center_id: number;
    center_name: string;
    meals: number;
    score: number;
  }>;
};

type Props = {
  onSuccess?: (payload: MatchingResult) => void;
  onError?: (errorMessage: string) => void;
  onRunningChange?: (isRunning: boolean) => void;
  onProgressTextChange?: (text: string | null) => void;
  onStepIndexChange?: (index: number) => void;
  className?: string;
  disabled?: boolean;
};

const LOADING_STEPS = [
  "המערכת החכמה מריצה Gale-Shapley...",
  "מחשב התאמות בין מוטבים למרכזים...",
  "יוצר שיבוצי חלוקה ומשימות משלוח...",
  "מעבד סטטיסטיקות ומכין דוח הרצה...",
  "מייצר שכבת ייצוא לאקסל...",
];

export default function RunMatchingButton({
  onSuccess,
  onError,
  onRunningChange,
  onProgressTextChange,
  onStepIndexChange,
  className,
  disabled,
}: Props) {
  const [loading, setLoading] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);

  const runMatching = async () => {
    if (disabled || loading) return;

    setLoading(true);
    onRunningChange?.(true);
    setStepIndex(0);
    onStepIndexChange?.(0);
    onProgressTextChange?.(LOADING_STEPS[0]);

    const intervalId = window.setInterval(() => {
      setStepIndex((prev) => {
        const next = (prev + 1) % LOADING_STEPS.length;
        onStepIndexChange?.(next);
        onProgressTextChange?.(LOADING_STEPS[next]);
        return next;
      });
    }, 1450);

    try {
      const res = await fetch(`${base_url}/delivery_assignment/run_matching`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });

      const data: MatchingResult = await res.json();

      if (!res.ok) throw new Error((data as any).error || "Failed");

      onSuccess?.(data);
    } catch (err: any) {
      const errorMessage = err.message || "אירעה שגיאה בהרצת השיבוץ";
      onError?.(errorMessage);
    } finally {
      window.clearInterval(intervalId);
      onProgressTextChange?.(null);
      onRunningChange?.(false);
      setLoading(false);
    }
  };

  return (
    <div className={className}>
      <button onClick={runMatching} disabled={loading || disabled}>
        {loading ? LOADING_STEPS[stepIndex] : "הרץ שיבוץ Smart Batch"}
      </button>
    </div>
  );
}
