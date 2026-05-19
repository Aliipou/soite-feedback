import api from "./axios";
import type { QuestionType } from "./survey";

export interface AdminQuestion {
  id: string;
  text_fi: string;
  text_en: string;
  type: QuestionType;
  order: number;
  is_active: boolean;
}

export interface AdminUser {
  id: string;
  email: string;
  role: "staff" | "admin";
  is_active: boolean;
  last_login_at: string | null;
}

export interface CreateQuestionPayload {
  text_fi: string;
  text_en?: string;
  type: QuestionType;
  order: number;
}

export interface UpdateQuestionPayload {
  text_fi?: string;
  text_en?: string;
  order?: number;
  is_active?: boolean;
}

export interface CreateUserPayload {
  email: string;
  password: string;
  role: "staff" | "admin";
}

export async function fetchAdminQuestions(): Promise<AdminQuestion[]> {
  const { data } = await api.get<AdminQuestion[]>("/admin/questions");
  return data;
}

export async function createQuestion(payload: CreateQuestionPayload): Promise<AdminQuestion> {
  const { data } = await api.post<AdminQuestion>("/admin/questions", payload);
  return data;
}

export async function updateQuestion(id: string, payload: UpdateQuestionPayload): Promise<AdminQuestion> {
  const { data } = await api.patch<AdminQuestion>(`/admin/questions/${id}`, payload);
  return data;
}

export async function fetchAdminUsers(): Promise<AdminUser[]> {
  const { data } = await api.get<AdminUser[]>("/admin/users");
  return data;
}

export async function createUser(payload: CreateUserPayload): Promise<AdminUser> {
  const { data } = await api.post<AdminUser>("/admin/users", payload);
  return data;
}

export async function updateUser(id: string, payload: Partial<{ is_active: boolean; role: string }>): Promise<AdminUser> {
  const { data } = await api.patch<AdminUser>(`/admin/users/${id}`, payload);
  return data;
}

export async function exportCsv(from?: string, to?: string): Promise<Blob> {
  const params: Record<string, string> = {};
  if (from) params.from = from;
  if (to) params.to = to;
  const { data } = await api.get<Blob>("/admin/export", {
    params,
    responseType: "blob",
  });
  return data;
}

export async function login(email: string, password: string): Promise<{ access_token: string; token_type: string; expires_in: number }> {
  const { data } = await api.post("/auth/login", { email, password });
  return data as { access_token: string; token_type: string; expires_in: number };
}

export async function logout(): Promise<void> {
  await api.post("/auth/logout");
}
