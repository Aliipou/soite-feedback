import api from "./axios";

export interface SummaryPeriod {
  from: string;
  to: string;
}

export interface QuestionSummary {
  question_id: string;
  text_fi: string;
  type: "scale5" | "yesno" | "text";
  counts?: Record<string, number>;
  mean?: number;
  total?: number;
}

export interface DashboardSummary {
  period: SummaryPeriod;
  total_submissions: number;
  by_question: QuestionSummary[];
}

export interface FreetextItem {
  text: string;
}

export interface FreetextResponse {
  total: number;
  page: number;
  items: FreetextItem[];
}

export async function fetchSummary(from?: string, to?: string): Promise<DashboardSummary> {
  const params: Record<string, string> = {};
  if (from) params.from = from;
  if (to) params.to = to;
  const { data } = await api.get<DashboardSummary>("/dashboard/summary", { params });
  return data;
}

export async function fetchFreetext(
  questionId: string,
  page = 1,
  perPage = 20
): Promise<FreetextResponse> {
  const { data } = await api.get<FreetextResponse>("/dashboard/freetext", {
    params: { question_id: questionId, page, per_page: perPage },
  });
  return data;
}
