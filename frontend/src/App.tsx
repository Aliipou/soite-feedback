import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Suspense } from "react";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { KioskPage } from "./pages/KioskPage";
import { LoginPage } from "./pages/LoginPage";
import { DashboardPage } from "./pages/DashboardPage";
import { FreetextPage } from "./pages/FreetextPage";
import { AdminPage } from "./pages/AdminPage";

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<KioskPage />} />
      <Route path="/login" element={<LoginPage />} />

      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/dashboard/freetext"
        element={
          <ProtectedRoute>
            <FreetextPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin"
        element={
          <ProtectedRoute requireAdmin>
            <AdminPage />
          </ProtectedRoute>
        }
      />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Suspense fallback={null}>
          <AppRoutes />
        </Suspense>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
