import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import fi from "./fi.json";
import sv from "./sv.json";

i18n.use(initReactI18next).init({
  resources: {
    fi: { translation: fi },
    sv: { translation: sv },
  },
  lng: "fi",
  fallbackLng: "fi",
  interpolation: { escapeValue: false },
});

export default i18n;
