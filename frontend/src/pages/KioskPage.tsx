import { useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { v4 as uuidv4 } from "uuid";
import { useQuestions } from "../hooks/useQuestions";
import { useOnlineStatus } from "../hooks/useOnlineStatus";
import { submitFeedback, getDeviceToken } from "../api/feedback";
import type { Answer } from "../api/feedback";
import { enqueue } from "../offline/queue";
import { PrivacyNoticeScreen } from "../components/kiosk/PrivacyNoticeScreen";
import { WelcomeScreen } from "../components/kiosk/WelcomeScreen";
import { QuestionScreen } from "../components/kiosk/QuestionScreen";
import { ThankYouScreen } from "../components/kiosk/ThankYouScreen";

type Stage = "privacy" | "welcome" | "questions" | "thankyou";

const APP_VERSION = "1.0.0";

export function KioskPage() {
  const { t } = useTranslation();
  const { questions, loading, error, refetch } = useQuestions();
  const isOnline = useOnlineStatus();

  const [stage, setStage] = useState<Stage>("privacy");
  const [questionIndex, setQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Answer[]>([]);
  const [offlineQueued, setOfflineQueued] = useState(false);

  const handleAnswer = useCallback(
    async (answer: Answer) => {
      const newAnswers = [...answers, answer];
      setAnswers(newAnswers);

      if (questionIndex < questions.length - 1) {
        setQuestionIndex((i) => i + 1);
      } else {
        const payload = {
          submission_id: uuidv4(),
          answers: newAnswers,
          submitted_at_local: new Date().toISOString(),
          app_version: APP_VERSION,
        };

        if (isOnline) {
          try {
            await submitFeedback(payload);
          } catch {
            await enqueue(payload);
            setOfflineQueued(true);
          }
        } else {
          await enqueue(payload);
          setOfflineQueued(true);
        }

        setStage("thankyou");
      }
    },
    [answers, questionIndex, questions.length, isOnline]
  );

  const handleReset = useCallback(() => {
    setStage("privacy");
    setQuestionIndex(0);
    setAnswers([]);
    setOfflineQueued(false);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-kiosk-bg flex items-center justify-center">
        <p className="text-xl text-kiosk-text-secondary">{t("common.loading")}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-kiosk-bg flex items-center justify-center p-8">
        <div className="text-center">
          <p className="text-xl text-kiosk-text-secondary mb-6">{t("kiosk.error.loadFailed")}</p>
          <button
            onClick={refetch}
            className="px-8 py-4 text-button-lg font-semibold text-white bg-kiosk-primary rounded-2xl hover:bg-kiosk-primary-hover transition-colors"
          >
            {t("kiosk.error.retry")}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-kiosk-bg">
      {!isOnline && (
        <div
          className="bg-amber-50 border-b border-amber-200 px-4 py-2 text-center text-sm text-amber-700"
          role="status"
          aria-live="polite"
        >
          {t("kiosk.offline.notice")}
        </div>
      )}

      {stage === "privacy" && <PrivacyNoticeScreen onStart={() => setStage("welcome")} />}
      {stage === "welcome" && <WelcomeScreen onStart={() => setStage("questions")} />}
      {stage === "questions" && questions[questionIndex] && (
        <QuestionScreen
          key={questionIndex}
          question={questions[questionIndex]}
          questionIndex={questionIndex}
          totalQuestions={questions.length}
          onAnswer={(answer) => void handleAnswer(answer)}
        />
      )}
      {stage === "thankyou" && <ThankYouScreen onReset={handleReset} offlineQueued={offlineQueued} />}
    </div>
  );
}
