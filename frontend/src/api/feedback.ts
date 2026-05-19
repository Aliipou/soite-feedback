import api from "./axios";

export interface Answer {
  question_id: string;
  int_value?: number;
  text_value?: string;
}

export interface FeedbackPayload {
  submission_id: string;
  answers: Answer[];
  submitted_at_local: string;
  app_version: string;
}

export interface FeedbackResponse {
  received: boolean;
}

export function getDeviceToken(): string {
  const key = "soite_device_token";
  let token = localStorage.getItem(key);
  if (!token) {
    token = crypto.randomUUID();
    localStorage.setItem(key, token);
  }
  return token;
}

export async function submitFeedback(payload: FeedbackPayload): Promise<FeedbackResponse> {
  const { data } = await api.post<FeedbackResponse>("/feedback", payload, {
    headers: { "X-Device-Token": getDeviceToken() },
  });
  return data;
}
