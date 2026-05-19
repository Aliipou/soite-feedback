import { useState, type FormEvent } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../hooks/useAuth";

export function LoginPage() {
  const { t } = useTranslation();
  const { login, loading, error } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: { pathname: string } } | null)?.from?.pathname ?? "/dashboard";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const ok = await login(email, password);
    if (ok) navigate(from, { replace: true });
  };

  return (
    <div className="min-h-screen bg-dash-bg flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="text-3xl font-bold text-dash-accent">Soite</div>
          <div className="text-gray-500 text-sm mt-1">Kotikuntoutus — Palautepaneeli</div>
        </div>

        <div className="bg-white rounded-2xl shadow-sm p-8 border border-gray-100">
          <h1 className="text-xl font-semibold text-gray-800 mb-6">
            {t("auth.login.title")}
          </h1>

          <form onSubmit={(e) => void handleSubmit(e)} noValidate>
            <div className="space-y-4">
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                  {t("auth.login.email")}
                </label>
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-dash-accent text-sm"
                  aria-describedby={error ? "login-error" : undefined}
                />
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                  {t("auth.login.password")}
                </label>
                <input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-dash-accent text-sm"
                  aria-describedby={error ? "login-error" : undefined}
                />
              </div>

              {error && (
                <p id="login-error" className="text-sm text-red-600" role="alert">
                  {t("auth.login.error")}
                </p>
              )}

              <button
                type="submit"
                disabled={loading || !email || !password}
                className="w-full py-3 text-sm font-semibold text-white bg-dash-accent hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-dash-accent"
              >
                {loading ? t("auth.login.loading") : t("auth.login.submit")}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
