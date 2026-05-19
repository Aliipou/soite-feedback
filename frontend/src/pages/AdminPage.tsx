import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Sidebar } from "../components/Sidebar";
import { QuestionTable } from "../components/admin/QuestionTable";
import { QuestionModal } from "../components/admin/QuestionModal";
import { UserTable } from "../components/admin/UserTable";
import {
  fetchAdminQuestions,
  createQuestion,
  updateQuestion,
  fetchAdminUsers,
  updateUser,
  exportCsv,
} from "../api/admin";
import type { AdminQuestion, AdminUser } from "../api/admin";
import { useAuth } from "../hooks/useAuth";

type Tab = "questions" | "users" | "export";

function isoToday() { return new Date().toISOString().slice(0, 10); }
function isoMonthAgo() { const d = new Date(); d.setMonth(d.getMonth() - 1); return d.toISOString().slice(0, 10); }

export function AdminPage() {
  const { t } = useTranslation();
  const { role } = useAuth();
  const [activeTab, setActiveTab] = useState<Tab>("questions");
  const [questions, setQuestions] = useState<AdminQuestion[]>([]);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [editingQuestion, setEditingQuestion] = useState<AdminQuestion | null | undefined>(undefined);
  const [exportFrom, setExportFrom] = useState(isoMonthAgo());
  const [exportTo, setExportTo] = useState(isoToday());
  const [exportLoading, setExportLoading] = useState(false);

  // Hooks must always be called in the same order — move all effects before any conditional return
  useEffect(() => {
    if (role !== "admin") return;
    void fetchAdminQuestions().then(setQuestions);
    void fetchAdminUsers().then(setUsers);
  }, [role]);

  if (role !== "admin") {
    return (
      <div className="flex min-h-screen bg-dash-bg">
        <Sidebar />
        <main className="flex-1 flex items-center justify-center p-8">
          <p className="text-gray-500">{t("admin.forbidden")}</p>
        </main>
      </div>
    );
  }

  const handleToggle = async (q: AdminQuestion) => {
    const updated = await updateQuestion(q.id, { is_active: !q.is_active });
    setQuestions((qs) => qs.map((x) => (x.id === updated.id ? updated : x)));
  };

  const handleDeactivateUser = async (u: AdminUser) => {
    const updated = await updateUser(u.id, { is_active: false });
    setUsers((us) => us.map((x) => (x.id === updated.id ? updated : x)));
  };

  const handleExport = async () => {
    setExportLoading(true);
    try {
      const blob = await exportCsv(exportFrom, exportTo);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `soite-palaute-${exportFrom}--${exportTo}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setExportLoading(false);
    }
  };

  const tabClass = (tab: Tab) =>
    `px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
      activeTab === tab
        ? "border-dash-accent text-dash-accent"
        : "border-transparent text-gray-500 hover:text-gray-700"
    }`;

  return (
    <div className="flex min-h-screen bg-dash-bg">
      <Sidebar />
      <main className="flex-1 p-8 overflow-y-auto">
        <div className="max-w-5xl mx-auto">
          <h1 className="text-2xl font-bold text-gray-800 mb-6">{t("admin.title")}</h1>

          <div className="flex border-b border-gray-200 mb-6">
            <button className={tabClass("questions")} onClick={() => setActiveTab("questions")}>
              {t("admin.tabs.questions")}
            </button>
            <button className={tabClass("users")} onClick={() => setActiveTab("users")}>
              {t("admin.tabs.users")}
            </button>
            <button className={tabClass("export")} onClick={() => setActiveTab("export")}>
              {t("admin.tabs.export")}
            </button>
          </div>

          {activeTab === "questions" && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100">
              <div className="p-4 flex justify-end border-b border-gray-100">
                <button
                  type="button"
                  onClick={() => setEditingQuestion(null)}
                  className="px-4 py-2 text-sm font-medium text-white bg-dash-accent rounded-lg hover:bg-blue-700 transition-colors"
                >
                  + {t("admin.questions.add")}
                </button>
              </div>
              <QuestionTable
                questions={questions}
                onEdit={(q) => setEditingQuestion(q)}
                onToggle={(q) => void handleToggle(q)}
              />
            </div>
          )}

          {activeTab === "users" && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100">
              <div className="p-4">
                <UserTable users={users} onDeactivate={(u) => void handleDeactivateUser(u)} />
              </div>
            </div>
          )}

          {activeTab === "export" && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 max-w-md">
              <h2 className="text-lg font-semibold text-gray-700 mb-4">{t("dashboard.export.title")}</h2>
              <p className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4">
                {t("dashboard.export.notice")}
              </p>
              <div className="space-y-4">
                <div>
                  <label htmlFor="exp-from" className="block text-sm font-medium text-gray-700 mb-1">
                    {t("dashboard.dateRange.from")}
                  </label>
                  <input
                    id="exp-from"
                    type="date"
                    value={exportFrom}
                    onChange={(e) => setExportFrom(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-dash-accent text-sm"
                  />
                </div>
                <div>
                  <label htmlFor="exp-to" className="block text-sm font-medium text-gray-700 mb-1">
                    {t("dashboard.dateRange.to")}
                  </label>
                  <input
                    id="exp-to"
                    type="date"
                    value={exportTo}
                    onChange={(e) => setExportTo(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-dash-accent text-sm"
                  />
                </div>
                <button
                  type="button"
                  onClick={() => void handleExport()}
                  disabled={exportLoading}
                  className="w-full py-3 text-sm font-semibold text-white bg-dash-accent hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50"
                >
                  {exportLoading ? t("dashboard.export.loading") : t("dashboard.export.download")}
                </button>
              </div>
            </div>
          )}
        </div>
      </main>

      {editingQuestion !== undefined && (
        <QuestionModal
          question={editingQuestion}
          onSave={async (payload) => {
            if (editingQuestion) {
              const updated = await updateQuestion(editingQuestion.id, payload);
              setQuestions((qs) => qs.map((x) => (x.id === updated.id ? updated : x)));
            } else {
              const created = await createQuestion(payload);
              setQuestions((qs) => [...qs, created].sort((a, b) => a.order - b.order));
            }
          }}
          onClose={() => setEditingQuestion(undefined)}
        />
      )}
    </div>
  );
}
