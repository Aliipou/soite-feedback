import { useTranslation } from "react-i18next";
import type { DashboardSummary } from "../../api/dashboard";

interface Props {
  summary: DashboardSummary;
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 flex-1 min-w-0">
      <p className="text-sm text-gray-500 mb-1">{label}</p>
      <p className="text-3xl font-bold text-dash-accent">{value}</p>
    </div>
  );
}

export function SummaryRow({ summary }: Props) {
  const { t } = useTranslation();

  const scale5Questions = summary.by_question.filter((q) => q.type === "scale5");
  const overallMean =
    scale5Questions.length > 0
      ? (
          scale5Questions.reduce((sum, q) => sum + (q.mean ?? 0), 0) /
          scale5Questions.length
        ).toFixed(2)
      : "—";

  return (
    <section
      className="flex gap-4 flex-wrap"
      aria-label={t("dashboard.summary.total")}
    >
      <StatCard label={t("dashboard.summary.total")} value={summary.total_submissions} />
      <StatCard label={`${t("dashboard.summary.total")} (${summary.period.from})`} value={summary.total_submissions} />
      <StatCard
        label={t("dashboard.summary.mean")}
        value={overallMean}
      />
    </section>
  );
}
