import { useState } from "react";
import * as XLSX from "xlsx";
import { base_url } from "../config";

type Props = {
  className?: string;
  disabled?: boolean;
};

export default function DownloadDividesButton({ className, disabled }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const downloadExcel = async () => {
    if (loading || disabled) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${base_url}/delivery_assignment`, {
        method: "GET",
        headers: {
          Accept: "application/json",
        },
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || "Failed to fetch divides");
      }

      const data = await res.json();
      const worksheet = XLSX.utils.json_to_sheet(data);
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, "Assignments");
      XLSX.writeFile(workbook, "delivery_assignments.xlsx");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="sh-download-wrap">
      <button
        className={className}
        onClick={downloadExcel}
        disabled={loading || disabled}
      >
        {loading ? "מייצא לאקסל..." : "📥 הורדת אקסל"}
      </button>
      {error && <p className="sh-download-error">{error}</p>}
    </div>
  );
}
