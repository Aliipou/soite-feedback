import { NavLink, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../hooks/useAuth";

export function Sidebar() {
  const { t } = useTranslation();
  const { role, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `block px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
      isActive
        ? "bg-dash-accent text-white"
        : "text-dash-sidebar-text hover:bg-white/10"
    }`;

  return (
    <nav
      className="w-56 min-h-screen bg-dash-sidebar flex flex-col p-4"
      aria-label="Sivunavigaatio"
    >
      <div className="mb-8">
        <div className="text-white font-bold text-lg leading-tight">Soite</div>
        <div className="text-dash-sidebar-text text-xs mt-1">Kotikuntoutus</div>
      </div>

      <div className="flex-1 space-y-1">
        <NavLink to="/dashboard" end className={linkClass}>
          {t("dashboard.nav.overview")}
        </NavLink>
        <NavLink to="/dashboard/freetext" className={linkClass}>
          {t("dashboard.nav.freetext")}
        </NavLink>
        {role === "admin" && (
          <>
            <NavLink to="/dashboard/export" className={linkClass}>
              {t("dashboard.nav.export")}
            </NavLink>
            <NavLink to="/admin" className={linkClass}>
              {t("admin.title")}
            </NavLink>
          </>
        )}
      </div>

      <button
        onClick={() => void handleLogout()}
        className="mt-4 px-4 py-2 text-sm text-dash-sidebar-text hover:text-white hover:bg-white/10 rounded-lg transition-colors text-left"
        aria-label={t("auth.logout")}
      >
        {t("auth.logout")}
      </button>
    </nav>
  );
}
