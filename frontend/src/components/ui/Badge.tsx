import clsx from "clsx";

const STATUS_STYLES: Record<string, string> = {
  pending: "bg-gray-200 text-gray-700",
  ocr_in_progress: "bg-blue-100 text-blue-700",
  nlp_in_progress: "bg-indigo-100 text-indigo-700",
  ai_evaluated: "bg-purple-100 text-purple-700",
  under_review: "bg-amber-100 text-amber-700",
  approved: "bg-emerald-100 text-emerald-700",
  rejected: "bg-red-100 text-red-700",
  re_evaluation_requested: "bg-orange-100 text-orange-700",
  failed: "bg-red-200 text-red-800",
};

export default function Badge({ status }: { status: string }) {
  return (
    <span
      className={clsx(
        "rounded-full px-3 py-1 text-xs font-semibold capitalize",
        STATUS_STYLES[status] || "bg-gray-100 text-gray-600"
      )}
    >
      {status.replace(/_/g, " ")}
    </span>
  );
}
