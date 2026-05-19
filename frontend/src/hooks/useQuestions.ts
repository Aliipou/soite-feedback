import { useState, useEffect } from "react";
import { fetchQuestions } from "../api/survey";
import type { Question } from "../api/survey";

interface UseQuestionsResult {
  questions: Question[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useQuestions(): UseQuestionsResult {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchQuestions()
      .then((res) => {
        if (!cancelled) {
          setQuestions(res.questions.sort((a, b) => a.order - b.order));
          setLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setError("Kysymysten lataus epäonnistui.");
          setLoading(false);
        }
      });

    return () => { cancelled = true; };
  }, [tick]);

  return { questions, loading, error, refetch: () => setTick((t) => t + 1) };
}
