import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  ResponsiveContainer,
} from "recharts";
import { scaleColors, scaleEmojis } from "../../styles/tokens";
import type { QuestionSummary } from "../../api/dashboard";

interface Props {
  question: QuestionSummary;
}

export function Scale5Chart({ question }: Props) {
  const data = [1, 2, 3, 4, 5].map((v) => ({
    label: `${scaleEmojis[v]} ${v}`,
    count: question.counts?.[String(v)] ?? 0,
    fill: scaleColors[v],
  }));

  const total = data.reduce((s, d) => s + d.count, 0);

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
      <h2 className="text-base font-semibold text-gray-700 mb-1">{question.text_fi}</h2>
      {question.mean != null && (
        <p className="text-sm text-gray-400 mb-4">
          Keskiarvo: <strong>{question.mean.toFixed(2)}</strong> · {total} vastausta
        </p>
      )}
      <div
        aria-label={`Pylväskaavio: ${question.text_fi}. Vastauksia yhteensä ${total}.`}
        role="img"
      >
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={false} />
            <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12 }} />
            <YAxis type="category" dataKey="label" tick={{ fontSize: 14 }} width={60} />
            <Tooltip
              formatter={(value: number) => [value, "Vastauksia"]}
              labelFormatter={(l) => `${l}`}
            />
            <Bar dataKey="count" radius={[0, 4, 4, 0]}>
              {data.map((entry, i) => (
                <Cell key={i} fill={entry.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
