import { useTranslation } from "react-i18next";
import type { AdminQuestion, UpdateQuestionPayload } from "../../api/admin";

interface Props {
  questions: AdminQuestion[];
  onEdit: (question: AdminQuestion) => void;
  onToggle: (question: AdminQuestion) => void;
}

const TYPE_LABELS: Record<string, string> = {
  scale5: "Asteikko 1–5",
  yesno: "Kyllä/Ei",
  text: "Vapaa teksti",
};

export function QuestionTable({ questions, onEdit, onToggle }: Props) {
  const { t } = useTranslation();

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm" aria-label={t("admin.tabs.questions")}>
        <thead>
          <tr className="border-b border-gray-200">
            <th className="text-left py-3 px-4 font-medium text-gray-500">{t("admin.questions.order")}</th>
            <th className="text-left py-3 px-4 font-medium text-gray-500">{t("admin.questions.text")}</th>
            <th className="text-left py-3 px-4 font-medium text-gray-500">{t("admin.questions.type")}</th>
            <th className="text-left py-3 px-4 font-medium text-gray-500">{t("admin.questions.status")}</th>
            <th className="py-3 px-4 font-medium text-gray-500 text-right">Toiminnot</th>
          </tr>
        </thead>
        <tbody>
          {questions.map((q) => (
            <tr key={q.id} className="border-b border-gray-100 hover:bg-gray-50">
              <td className="py-3 px-4 text-gray-600">{q.order}</td>
              <td className="py-3 px-4 text-gray-800 max-w-xs truncate">{q.text_fi}</td>
              <td className="py-3 px-4 text-gray-600">{TYPE_LABELS[q.type]}</td>
              <td className="py-3 px-4">
                <span
                  className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                    q.is_active
                      ? "bg-green-100 text-green-700"
                      : "bg-gray-100 text-gray-500"
                  }`}
                >
                  {q.is_active ? t("admin.questions.active") : t("admin.questions.inactive")}
                </span>
              </td>
              <td className="py-3 px-4 text-right">
                <div className="flex gap-2 justify-end">
                  <button
                    type="button"
                    onClick={() => onEdit(q)}
                    className="px-3 py-1 text-xs font-medium text-dash-accent border border-dash-accent rounded-lg hover:bg-dash-accent/10 transition-colors"
                    aria-label={`${t("admin.questions.edit")}: ${q.text_fi}`}
                  >
                    {t("admin.questions.edit")}
                  </button>
                  <button
                    type="button"
                    onClick={() => onToggle(q)}
                    className={`px-3 py-1 text-xs font-medium rounded-lg transition-colors ${
                      q.is_active
                        ? "text-red-600 border border-red-300 hover:bg-red-50"
                        : "text-green-600 border border-green-300 hover:bg-green-50"
                    }`}
                    aria-label={
                      q.is_active
                        ? `${t("admin.questions.deactivate")}: ${q.text_fi}`
                        : `${t("admin.questions.activate")}: ${q.text_fi}`
                    }
                  >
                    {q.is_active ? t("admin.questions.deactivate") : t("admin.questions.activate")}
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {questions.length === 0 && (
        <p className="text-center text-gray-400 py-8">Ei kysymyksiä.</p>
      )}
    </div>
  );
}
