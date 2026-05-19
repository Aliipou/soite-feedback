import { useTranslation } from "react-i18next";
import type { AdminUser } from "../../api/admin";

interface Props {
  users: AdminUser[];
  onDeactivate: (user: AdminUser) => void;
}

export function UserTable({ users, onDeactivate }: Props) {
  const { t } = useTranslation();

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm" aria-label={t("admin.tabs.users")}>
        <thead>
          <tr className="border-b border-gray-200">
            <th className="text-left py-3 px-4 font-medium text-gray-500">{t("admin.users.email")}</th>
            <th className="text-left py-3 px-4 font-medium text-gray-500">{t("admin.users.role")}</th>
            <th className="text-left py-3 px-4 font-medium text-gray-500">{t("admin.users.lastLogin")}</th>
            <th className="text-left py-3 px-4 font-medium text-gray-500">{t("admin.users.status")}</th>
            <th className="py-3 px-4 font-medium text-gray-500 text-right">Toiminnot</th>
          </tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id} className="border-b border-gray-100 hover:bg-gray-50">
              <td className="py-3 px-4 text-gray-800">{u.email}</td>
              <td className="py-3 px-4 text-gray-600">
                {u.role === "admin" ? t("admin.users.roleAdmin") : t("admin.users.roleStaff")}
              </td>
              <td className="py-3 px-4 text-gray-500">
                {u.last_login_at
                  ? new Date(u.last_login_at).toLocaleDateString("fi-FI")
                  : "—"}
              </td>
              <td className="py-3 px-4">
                <span
                  className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                    u.is_active
                      ? "bg-green-100 text-green-700"
                      : "bg-gray-100 text-gray-500"
                  }`}
                >
                  {u.is_active ? t("admin.users.active") : t("admin.users.inactive")}
                </span>
              </td>
              <td className="py-3 px-4 text-right">
                {u.is_active && (
                  <button
                    type="button"
                    onClick={() => onDeactivate(u)}
                    className="px-3 py-1 text-xs font-medium text-red-600 border border-red-300 rounded-lg hover:bg-red-50 transition-colors"
                    aria-label={`${t("admin.users.deactivate")}: ${u.email}`}
                  >
                    {t("admin.users.deactivate")}
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {users.length === 0 && (
        <p className="text-center text-gray-400 py-8">Ei käyttäjiä.</p>
      )}
    </div>
  );
}
