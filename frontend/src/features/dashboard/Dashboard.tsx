import { useTranslation } from "react-i18next";

import { useUser } from "@/lib/useUser";
import TaskList from "@/features/tasks/TaskList";

export default function Dashboard() {
  const { t } = useTranslation();
  const { data: user } = useUser();

  const calendarPref = user?.calendar_pref ?? "gregorian";
  const locale = user?.locale ?? "en";

  return (
    <div className="max-w-xl">
      <h1 className="mb-4 text-xl font-semibold">{t("nav.dashboard")}</h1>
      <TaskList
        queryKey={["tasks"]}
        calendarPref={calendarPref}
        locale={locale}
      />
    </div>
  );
}
