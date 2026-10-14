type StatusBadgeProps = {
  status: string | null | undefined;
};

const statusStyles: Record<string, string> = {
  new: "bg-slate-100 text-slate-700",
  researched: "bg-blue-100 text-blue-700",
  scored: "bg-indigo-100 text-indigo-700",
  drafted: "bg-amber-100 text-amber-700",
  approved: "bg-emerald-100 text-emerald-700",
  rejected: "bg-rose-100 text-rose-700",
  skipped: "bg-gray-200 text-gray-700",
  failed: "bg-red-100 text-red-700",
  pending: "bg-yellow-100 text-yellow-800",
  edited: "bg-purple-100 text-purple-700",
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const value = (status || "new").toLowerCase();
  const styles =
    statusStyles[value] || "bg-slate-100 text-slate-700";

  return (
    <span
      className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold capitalize ${styles}`}
    >
      {value}
    </span>
  );
}