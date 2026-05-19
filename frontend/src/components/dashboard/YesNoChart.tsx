import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { colors } from "../../styles/tokens";
import type { QuestionSummary } from "../../api/dashboard";

interface Props {
  question: QuestionSummary;
}

export function YesNoChart({ question }: Props) {
  const yes = question.counts?.["1"] ?? 0;
  const no = question.counts?.["0"] ?? 0;
  const total = yes + no;

  const data = [
    { name: "Kyllä", value: yes, color: colors.yes },
    { name: "Ei", value: no, color: colors.no },
  ];

  const yesPct = total > 0 ? Math.round((yes / total) * 100) : 0;

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
      <h2 className="text-base font-semibold text-gray-700 mb-1">{question.text_fi}</h2>
      <p className="text-sm text-gray-400 mb-4">{total} vastausta</p>
      <div
        aria-label={`Donitsikaavio: ${question.text_fi}. Kyllä ${yesPct}%, Ei ${100 - yesPct}%.`}
        role="img"
      >
        <ResponsiveContainer width="100%" height={200}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={50}
              outerRadius={80}
              dataKey="value"
              label={({ name, percent }) => `${name} ${Math.round((percent as number) * 100)}%`}
            >
              {data.map((entry, i) => (
                <Cell key={i} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip formatter={(v: number) => [v, "Vastauksia"]} />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
