import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Sidebar } from "../components/Sidebar";
import { fetchFreetext, fetchSummary } from "../api/dashboard";
import type { FreetextResponse, QuestionSummary } from "../api/dashboard";

const PER_PAGE = 20;

export function FreetextPage() {
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();
  const [questions, setQuestions] = useState<QuestionSummary[]>([]);
  const [result, setResult] = useState<FreetextResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const questionId = searchParams.get("question_id") ?? "";
  const page = parseInt(searchParams.get("page") ?? "1");

  useEffect(() => {
    fetchSummary()
      .then((s) => setQuestions(s.by_question.filter((q) => q.type === "text")))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!questionId) return;
    setLoading(true);
    fetchFreetext(questionId, page, PER_PAGE)
      .then(setResult)
      .catch(() => setError(t("common.error")))
      .finally(() => setLoading(false));
  }, [questionId, page, t]);

  const totalPages = result ? Math.ceil(result.total / PER_PAGE) : 1;

  const setPage = (p: number) => {
    setSearchParams({ question_id: questionId, page: String(p) });
  };

  return (
    <div className="flex min-h-screen bg-dash-bg">
      <Sidebar />
      <main className="flex-1 p-8 overflow-y-auto">
        <div className="max-w-3xl mx-auto">
          <h1 className="text-2xl font-bold text-gray-800 mb-6">
            {t("dashboard.freetext.title")}
          </h1>

          <div className="mb-6">
            <label htmlFor="question-select" className="block text-sm font-medium text-gray-700 mb-1">
              {t("dashboard.freetext.selectQuestion")}
            </label>
            <select
              id="question-select"
              value={questionId}
              onChange={(e) => setSearchParams({ question_id: e.target.value, page: "1" })}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-dash-accent text-sm"
            >
              <option value="">— {t("dashboard.freetext.selectQuestion")} —</option>
              {questions.map((q) => (
                <option key={q.question_id} value={q.question_id}>
                  {q.text_fi}
                </option>
              ))}
            </select>
          </div>

          {loading && <p className="text-gray-400">{t("common.loading")}</p>}
          {error && <p className="text-red-500" role="alert">{error}</p>}

          {result && !loading && (
            <>
              {result.items.length === 0 ? (
                <p className="text-gray-400">{t("dashboard.freetext.noResults")}</p>
              ) : (
                <ul className="space-y-3" aria-label="Vastaukset">
                  {result.items.map((item, i) => (
                    <li
                      key={i}
                      className="bg-white rounded-xl p-4 shadow-sm border border-gray-100 text-sm text-gray-700 leading-relaxed"
                    >
                      {item.text}
                    </li>
                  ))}
                </ul>
              )}

              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-6" aria-label="Sivutus">
                  <button
                    type="button"
                    onClick={() => setPage(page - 1)}
                    disabled={page <= 1}
                    className="px-4 py-2 text-sm font-medium text-gray-600 border border-gray-200 rounded-lg disabled:opacity-40 hover:bg-gray-50"
                  >
                    {t("dashboard.freetext.prev")}
                  </button>
                  <span className="text-sm text-gray-500">
                    {t("dashboard.freetext.page", { page, total: totalPages })}
                  </span>
                  <button
                    type="button"
                    onClick={() => setPage(page + 1)}
                    disabled={page >= totalPages}
                    className="px-4 py-2 text-sm font-medium text-gray-600 border border-gray-200 rounded-lg disabled:opacity-40 hover:bg-gray-50"
                  >
                    {t("dashboard.freetext.next")}
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}
