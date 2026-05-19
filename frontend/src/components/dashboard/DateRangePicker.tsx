import { useState } from "react";
import { useTranslation } from "react-i18next";

type Preset = "week" | "month" | "custom";

interface DateRange {
  from: string;
  to: string;
}

interface Props {
  onChange: (range: DateRange) => void;
}

function isoToday(): string {
  return new Date().toISOString().slice(0, 10);
}

function isoWeekAgo(): string {
  const d = new Date();
  d.setDate(d.getDate() - 7);
  return d.toISOString().slice(0, 10);
}

function isoMonthAgo(): string {
  const d = new Date();
  d.setMonth(d.getMonth() - 1);
  return d.toISOString().slice(0, 10);
}

export function DateRangePicker({ onChange }: Props) {
  const { t } = useTranslation();
  const [preset, setPreset] = useState<Preset>("week");
  const [from, setFrom] = useState(isoWeekAgo());
  const [to, setTo] = useState(isoToday());

  const applyPreset = (p: Preset) => {
    setPreset(p);
    let f = from, tVal = to;
    if (p === "week") { f = isoWeekAgo(); tVal = isoToday(); }
    if (p === "month") { f = isoMonthAgo(); tVal = isoToday(); }
    setFrom(f);
    setTo(tVal);
    onChange({ from: f, to: tVal });
  };

  const btnClass = (active: boolean) =>
    `px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
      active
        ? "bg-dash-accent text-white"
        : "bg-white text-gray-600 border border-gray-200 hover:bg-gray-50"
    }`;

  return (
    <div className="flex items-center gap-3 flex-wrap" role="group" aria-label="Aikaväli">
      <button className={btnClass(preset === "week")} onClick={() => applyPreset("week")}>
        {t("dashboard.dateRange.thisWeek")}
      </button>
      <button className={btnClass(preset === "month")} onClick={() => applyPreset("month")}>
        {t("dashboard.dateRange.thisMonth")}
      </button>
      <button className={btnClass(preset === "custom")} onClick={() => applyPreset("custom")}>
        {t("dashboard.dateRange.custom")}
      </button>

      {preset === "custom" && (
        <div className="flex items-center gap-2">
          <label htmlFor="range-from" className="text-sm text-gray-500">
            {t("dashboard.dateRange.from")}
          </label>
          <input
            id="range-from"
            type="date"
            value={from}
            onChange={(e) => { setFrom(e.target.value); onChange({ from: e.target.value, to }); }}
            className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-dash-accent"
          />
          <label htmlFor="range-to" className="text-sm text-gray-500">
            {t("dashboard.dateRange.to")}
          </label>
          <input
            id="range-to"
            type="date"
            value={to}
            onChange={(e) => { setTo(e.target.value); onChange({ from, to: e.target.value }); }}
            className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-dash-accent"
          />
        </div>
      )}
    </div>
  );
}
