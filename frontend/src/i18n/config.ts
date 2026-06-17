import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import en from "./en.json";
import fa from "./fa.json";

export const RTL_LANGS = ["fa"];

i18n.use(initReactI18next).init({
  resources: { en: { translation: en }, fa: { translation: fa } },
  lng: localStorage.getItem("locale") || "en",
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});

export function applyDir(lang: string) {
  const dir = RTL_LANGS.includes(lang) ? "rtl" : "ltr";
  document.documentElement.setAttribute("dir", dir);
  document.documentElement.setAttribute("lang", lang);
}

applyDir(i18n.language);
i18n.on("languageChanged", (lng) => {
  localStorage.setItem("locale", lng);
  applyDir(lng);
});

export default i18n;
