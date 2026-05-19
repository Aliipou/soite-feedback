import { useTranslation } from "react-i18next";
import type { Question } from "../../api/survey";
import type { Answer } from "../../api/feedback";
import { ProgressDots } from "./ProgressDots";
import { Scale5Input } from "./Scale5Input";
import { YesNoInput } from "./YesNoInput";
import { TextInput } from "./TextInput";
import { Face4Input } from "./Face4Input";

interface Props {
  question: Question;
  questionIndex: number;
  totalQuestions: number;
  onAnswer: (answer: Answer) => void;
}

export function QuestionScreen({ question, questionIndex, totalQuestions, onAnswer }: Props) {
  const { i18n } = useTranslation();

  const questionText =
    i18n.language === "sv" && question.text_sv ? question.text_sv : question.text_fi;

  const handleScale = (value: number) => {
    onAnswer({ question_id: question.id, int_value: value });
  };

  const handleYesNo = (value: number) => {
    onAnswer({ question_id: question.id, int_value: value });
  };

  const handleText = (text: string) => {
    const answer: Answer = { question_id: question.id };
    if (text) answer.text_value = text;
    onAnswer(answer);
  };

  return (
    <div className="flex flex-col items-center gap-8 w-full max-w-3xl mx-auto px-6 py-8">
      <ProgressDots total={totalQuestions} current={questionIndex} />

      <h1
        className="text-question text-kiosk-text-primary text-center leading-snug"
        id="question-heading"
      >
        {questionText}
      </h1>

      <div className="w-full" role="region" aria-labelledby="question-heading">
        {question.type === "face4" && (
          <Face4Input onSelect={handleScale} />
        )}
        {question.type === "scale5" && (
          <Scale5Input onSelect={handleScale} />
        )}
        {question.type === "yesno" && (
          <YesNoInput onSelect={handleYesNo} />
        )}
        {question.type === "text" && (
          <TextInput onSubmit={handleText} onSkip={() => handleText("")} />
        )}
      </div>
    </div>
  );
}
