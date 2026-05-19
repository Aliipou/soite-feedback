import { useTranslation } from "react-i18next";

interface Props {
  onStart: () => void;
}

export function PrivacyNoticeScreen({ onStart }: Props) {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-kiosk-bg px-8 py-12">
      <div className="max-w-2xl w-full text-center">
        <div className="mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-kiosk-primary/10 mb-4">
            <span className="text-4xl" role="img" aria-label="Tietosuoja">🔒</span>
          </div>
          <h1 className="text-3xl font-bold text-kiosk-text-primary mb-6">
            {t("kiosk.privacy.title")}
          </h1>
          <p className="text-xl text-kiosk-text-secondary leading-relaxed">
            {t("kiosk.privacy.body")}
          </p>
        </div>

        <button
          type="button"
          onClick={onStart}
          className="w-full min-h-touch text-button-lg font-semibold text-white bg-kiosk-primary hover:bg-kiosk-primary-hover rounded-2xl transition-colors focus:outline-none focus:ring-4 focus:ring-offset-2 focus:ring-kiosk-primary/50 shadow-md"
          autoFocus
        >
          {t("kiosk.privacy.start")}
        </button>
      </div>
    </div>
  );
}
