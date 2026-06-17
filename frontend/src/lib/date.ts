// Display-only calendar conversion. Backend stores UTC; we format per user pref.
// Jalali via native Intl (fa-IR-u-ca-persian). Pickers use react-multi-date-picker.

export type CalendarPref = "gregorian" | "jalali";

export function formatDate(
  value: string | Date,
  calendar: CalendarPref,
  locale: string,
  opts: Intl.DateTimeFormatOptions = { year: "numeric", month: "short", day: "numeric" },
): string {
  const d = typeof value === "string" ? new Date(value) : value;
  if (calendar === "jalali") {
    return new Intl.DateTimeFormat("fa-IR-u-ca-persian", opts).format(d);
  }
  return new Intl.DateTimeFormat(locale === "fa" ? "fa-IR" : "en-US", opts).format(d);
}

export function formatDateTime(value: string | Date, calendar: CalendarPref, locale: string): string {
  return formatDate(value, calendar, locale, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
