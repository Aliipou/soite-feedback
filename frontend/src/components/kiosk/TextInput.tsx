import { useState } from "react";
import { useTranslation } from "react-i18next";

const MAX_CHARS = 500;

interface Props {
  onSubmit: (text: string) => void;
  onSkip: () => void;
}

export function TextInput({ onSubmit, onSkip }: Props) {
  const { t } = useTranslation();
  const [value, setValue] = useState("");

  return (
    <div className="w-full max-w-2xl mx-auto flex flex-col gap-4">
      <label htmlFor="freetext-input" className="sr-only">
        {t("kiosk.question.placeholder")}
      </label>
      <textarea
        id="freetext-input"
        value={value}
        onChange={(e) => setValue(e.target.value.slice(0, MAX_CHARS))}
        placeholder={t("kiosk.question.placeholder")}
        className="w-full min-h-[200px] p-4 rounded-2xl border-2 border-kiosk-border bg-white text-kiosk-text-primary text-xl resize-none focus:outline-none focus:ring-4 focus:ring-kiosk-primary/30 focus:border-kiosk-primary transition-colors"
        aria-describedby="char-count"
        maxLength={MAX_CHARS}
      />
      <p
        id="char-count"
        className="text-sm text-kiosk-text-secondary text-right"
        aria-live="polite"
      >
        {t("kiosk.question.charCount", { count: value.length })}
      </p>
      <div className="flex gap-3">
        <button
          type="button"
          onClick={onSkip}
          className="flex-1 py-5 rounded-2xl text-button-lg font-semibold text-kiosk-text-secondary hover:bg-kiosk-secondary transition-colors focus:outline-none focus:ring-4 focus:ring-offset-2 focus:ring-kiosk-primary/30"
        >
          {t("kiosk.question.skip")}
        </button>
        <button
          type="button"
          onClick={() => onSubmit(value.trim())}
          className="flex-[2] py-5 rounded-2xl text-button-lg font-semibold text-white bg-kiosk-primary hover:bg-kiosk-primary-hover transition-colors focus:outline-none focus:ring-4 focus:ring-offset-2 focus:ring-kiosk-primary/50"
        >
          {t("kiosk.question.submit")}
        </button>
      </div>
    </div>
  );
}
