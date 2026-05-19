import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import type { ReactNode } from "react";

interface Props {
  children: ReactNode;
  requireAdmin?: boolean;
}

export function ProtectedRoute({ children, requireAdmin = false }: Props) {
  const location = useLocation();
  const { isAuthenticated, role, initializing } = useAuth();

  if (initializing) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-dash-bg">
        <span className="text-gray-400 text-sm">Ladataan...</span>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requireAdmin && role !== "admin") {
    return <Navigate to="/dashboard" state={{ forbidden: true }} replace />;
  }

  return <>{children}</>;
}
