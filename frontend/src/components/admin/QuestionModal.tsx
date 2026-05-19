import { useState, useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import type { AdminQuestion, CreateQuestionPayload } from "../../api/admin";
import type { QuestionType } from "../../api/survey";

interface Props {
  question?: AdminQuestion | null;
  onSave: (payload: CreateQuestionPayload) => Promise<void>;
  onClose: () => void;
}

export function QuestionModal({ question, onSave, onClose }: Props) {
  const { t } = useTranslation();
  const [textFi, setTextFi] = useState(question?.text_fi ?? "");
  const [textSv, setTextSv] = useState(question?.text_sv ?? "");
  const [type, setType] = useState<QuestionType>(question?.type ?? "face4");
  const [order, setOrder] = useState(question?.order ?? 10);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const firstInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    firstInputRef.current?.focus();
  }, []);

  const handleSave = async () => {
    if (!textFi.trim()) { setError("Suomenkielinen teksti vaaditaan."); return; }
    setSaving(true);
    setError(null);
    try {
      await onSave({
        text_fi: textFi.trim(),
        text_sv: textSv.trim() || undefined,
        type,
        order,
      });
      onClose();
    } catch {
      setError(t("common.error"));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6">
        <h2 id="modal-title" className="text-xl font-semibold text-gray-800 mb-6">
          {question ? t("admin.questions.edit") : t("admin.questions.add")}
        </h2>

        <div className="space-y-4">
          <div>
            <label htmlFor="q-text-fi" className="block text-sm font-medium text-gray-700 mb-1">
              {t("admin.questions.text")} *
            </label>
            <input
              ref={firstInputRef}
              id="q-text-fi"
              type="text"
              value={textFi}
              onChange={(e) => setTextFi(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-dash-accent text-sm"
              maxLength={500}
            />
          </div>

          <div>
            <label htmlFor="q-text-sv" className="block text-sm font-medium text-gray-700 mb-1">
              {t("admin.questions.textSv")}
            </label>
            <input
              id="q-text-sv"
              type="text"
              value={textSv}
              onChange={(e) => setTextSv(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-dash-accent text-sm"
              maxLength={500}
            />
          </div>

          <div className="flex gap-4">
            <div className="flex-1">
              <label htmlFor="q-type" className="block text-sm font-medium text-gray-700 mb-1">
                {t("admin.questions.type")}
              </label>
              <select
                id="q-type"
                value={type}
                onChange={(e) => setType(e.target.value as QuestionType)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-dash-accent text-sm"
              >
                <option value="face4">{t("admin.questions.typeFace4")}</option>
                <option value="text">{t("admin.questions.typeText")}</option>
                <option value="scale5">{t("admin.questions.typeScale")}</option>
                <option value="yesno">{t("admin.questions.typeYesNo")}</option>
              </select>
            </div>

            <div className="w-28">
              <label htmlFor="q-order" className="block text-sm font-medium text-gray-700 mb-1">
                {t("admin.questions.order")}
              </label>
              <input
                id="q-order"
                type="number"
                min={1}
                value={order}
                onChange={(e) => setOrder(parseInt(e.target.value) || 1)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-dash-accent text-sm"
              />
            </div>
          </div>

          {error && (
            <p className="text-sm text-red-600" role="alert">{error}</p>
          )}
        </div>

        <div className="flex gap-3 mt-6 justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            {t("admin.questions.cancel")}
          </button>
          <button
            type="button"
            onClick={() => void handleSave()}
            disabled={saving}
            className="px-4 py-2 text-sm font-medium text-white bg-dash-accent hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50"
          >
            {saving ? t("common.loading") : t("admin.questions.save")}
          </button>
        </div>
      </div>
    </div>
  );
}
