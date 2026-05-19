import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Sidebar } from "../components/Sidebar";
import { SummaryRow } from "../components/dashboard/SummaryRow";
import { Scale5Chart } from "../components/dashboard/Scale5Chart";
import { Face4Chart } from "../components/dashboard/Face4Chart";
import { YesNoChart } from "../components/dashboard/YesNoChart";
import { DateRangePicker } from "../components/dashboard/DateRangePicker";
import { fetchSummary } from "../api/dashboard";
import type { DashboardSummary } from "../api/dashboard";

function isoToday() { return new Date().toISOString().slice(0, 10); }
function isoWeekAgo() { const d = new Date(); d.setDate(d.getDate() - 7); return d.toISOString().slice(0, 10); }

export function DashboardPage() {
  const { t } = useTranslation();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [range, setRange] = useState({ from: isoWeekAgo(), to: isoToday() });

  useEffect(() => {
    setLoading(true);
    fetchSummary(range.from, range.to)
      .then(setSummary)
      .catch(() => setError(t("common.error")))
      .finally(() => setLoading(false));
  }, [range, t]);

  return (
    <div className="flex min-h-screen bg-dash-bg">
      <Sidebar />
      <main className="flex-1 p-8 overflow-y-auto" aria-label={t("dashboard.title")}>
        <div className="max-w-5xl mx-auto">
          <h1 className="text-2xl font-bold text-gray-800 mb-6">{t("dashboard.title")}</h1>

          <div className="mb-6">
            <DateRangePicker onChange={setRange} />
          </div>

          {loading && (
            <p className="text-gray-400" aria-live="polite">{t("common.loading")}</p>
          )}

          {error && (
            <p className="text-red-500" role="alert">{error}</p>
          )}

          {summary && !loading && (
            <div className="space-y-8">
              <SummaryRow summary={summary} />

              <section aria-label="Kysymyskohtaiset tulokset" className="space-y-4">
                {summary.by_question.map((q) => {
                  if (q.type === "face4") return <Face4Chart key={q.question_id} question={q} />;
                  if (q.type === "scale5") return <Scale5Chart key={q.question_id} question={q} />;
                  if (q.type === "yesno") return <YesNoChart key={q.question_id} question={q} />;
                  return (
                    <div
                      key={q.question_id}
                      className="bg-white rounded-xl p-6 shadow-sm border border-gray-100"
                    >
                      <h2 className="text-base font-semibold text-gray-700 mb-2">{q.text_fi}</h2>
                      <Link
                        to={`/dashboard/freetext?question_id=${q.question_id}`}
                        className="text-sm text-dash-accent hover:underline"
                      >
                        {q.total ?? 0} vapaamuotoista vastausta →
                      </Link>
                    </div>
                  );
                })}
              </section>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
