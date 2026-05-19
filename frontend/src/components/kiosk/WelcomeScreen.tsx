import { useTranslation } from "react-i18next";

interface Props {
  onStart: () => void;
}

export function WelcomeScreen({ onStart }: Props) {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-kiosk-bg px-8 py-12">
      <div className="max-w-2xl w-full text-center">
        <div className="mb-8">
          <div className="text-8xl mb-6" role="img" aria-label="Tervetuloa">💙</div>
          <h1 className="text-4xl font-bold text-kiosk-text-primary mb-4">
            {t("kiosk.welcome.heading")}
          </h1>
          <p className="text-xl text-kiosk-text-secondary mb-3 leading-relaxed">
            {t("kiosk.welcome.subtext")}
          </p>
          <p className="text-xl text-kiosk-text-secondary mb-3 leading-relaxed">
            {t("kiosk.welcome.anonymity")}
          </p>
          <p className="text-xl font-semibold text-kiosk-text-primary leading-relaxed">
            {t("kiosk.welcome.instruction")}
          </p>
        </div>

        <button
          type="button"
          onClick={onStart}
          className="w-full min-h-touch text-button-lg font-semibold text-white bg-kiosk-primary hover:bg-kiosk-primary-hover active:scale-95 rounded-2xl transition-all duration-150 focus:outline-none focus:ring-4 focus:ring-offset-2 focus:ring-kiosk-primary/50 shadow-md"
          autoFocus
        >
          {t("kiosk.welcome.cta")}
        </button>
      </div>
    </div>
  );
}
