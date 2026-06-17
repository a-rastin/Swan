import { useTranslation } from "react-i18next";

const OPTIONS: { label: string; labelFa: string; value: string | null }[] = [
  { label: "None",     labelFa: "بدون تکرار",  value: null },
  { label: "Daily",    labelFa: "روزانه",       value: "FREQ=DAILY" },
  { label: "Weekdays", labelFa: "روزهای کاری", value: "FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR" },
  { label: "Weekly",   labelFa: "هفتگی",        value: "FREQ=WEEKLY" },
  { label: "Monthly",  labelFa: "ماهانه",       value: "FREQ=MONTHLY" },
  { label: "Yearly",   labelFa: "سالانه",       value: "FREQ=YEARLY" },
];

interface Props {
  value: string | null;
  onChange: (v: string | null) => void;
}

export default function RecurrencePicker({ value, onChange }: Props) {
  const { i18n } = useTranslation();
  const isFa = i18n.language === "fa";

  return (
    <select
      value={value ?? ""}
      onChange={(e) => onChange(e.target.value || null)}
      className="w-full rounded border px-3 py-2 text-sm"
    >
      {OPTIONS.map((o) => (
        <option key={o.value ?? ""} value={o.value ?? ""}>
          {isFa ? o.labelFa : o.label}
        </option>
      ))}
    </select>
  );
}
