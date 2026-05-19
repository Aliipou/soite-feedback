import api from "./axios";

export type QuestionType = "scale5" | "yesno" | "text" | "face4";

export interface Question {
  id: string;
  text_fi: string;
  text_sv: string | null;
  type: QuestionType;
  order: number;
}

export interface QuestionsResponse {
  questions: Question[];
  version: string;
}

export async function fetchQuestions(): Promise<QuestionsResponse> {
  const { data } = await api.get<QuestionsResponse>("/survey/questions");
  return data;
}
