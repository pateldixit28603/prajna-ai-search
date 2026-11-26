/** The 7 answer languages: the world's top 5 by total speakers, plus Russian and Hinglish. */
export const LANGS = [
  { code: "en", native: "English", label: "English", dir: "ltr" },
  { code: "zh", native: "简体中文", label: "Chinese", dir: "ltr" },
  { code: "hi", native: "हिन्दी", label: "Hindi", dir: "ltr" },
  { code: "es", native: "Español", label: "Spanish", dir: "ltr" },
  { code: "ar", native: "العربية", label: "Arabic", dir: "rtl" },
  { code: "ru", native: "Русский", label: "Russian", dir: "ltr" },
  { code: "hinglish", native: "Hinglish", label: "Hinglish", dir: "ltr" },
] as const;

export const langDir = (code?: string): "ltr" | "rtl" => (code === "ar" ? "rtl" : "ltr");
export const langName = (code?: string) => LANGS.find((l) => l.code === code)?.native ?? code ?? "";
