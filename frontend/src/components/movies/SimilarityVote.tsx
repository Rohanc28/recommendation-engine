import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import clsx from "clsx";
import { votesApi } from "../../services/api";
import type { VoteType, VoteCounts } from "../../types";

interface Props {
  sourceMovieId: string;
  targetMovieId: string;
  targetTitle: string;
  voteCounts: VoteCounts;
}

const OPTIONS: { value: VoteType; label: string; color: string; emoji: string }[] = [
  { value: "close",     label: "Very Similar",   color: "border-green-500  text-green-400  hover:bg-green-900/30",  emoji: "🟢" },
  { value: "somewhat",  label: "Somewhat Similar",color: "border-yellow-500 text-yellow-400 hover:bg-yellow-900/30",emoji: "🟡" },
  { value: "different", label: "Different",       color: "border-red-500    text-red-400    hover:bg-red-900/30",   emoji: "🔴" },
];

export default function SimilarityVote({ sourceMovieId, targetMovieId, targetTitle, voteCounts }: Props) {
  const [selected, setSelected] = useState<VoteType | null>(null);
  const qc = useQueryClient();

  const mutation = useMutation({
    mutationFn: (vt: VoteType) => votesApi.cast(sourceMovieId, targetMovieId, vt),
    onSuccess: (_, vt) => {
      setSelected(vt);
      qc.invalidateQueries({ queryKey: ["recommendations", sourceMovieId] });
    },
  });

  const total = (voteCounts.close ?? 0) + (voteCounts.somewhat ?? 0) + (voteCounts.different ?? 0);

  return (
    <div className="space-y-2">
      <p className="text-xs text-gray-500">How similar is this to <span className="text-gray-300">{targetTitle}</span>?</p>
      <div className="flex gap-2">
        {OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => mutation.mutate(opt.value)}
            disabled={mutation.isPending}
            className={clsx(
              "flex-1 rounded-lg border px-2 py-1.5 text-xs font-medium transition-all",
              opt.color,
              selected === opt.value && "ring-2 ring-offset-1 ring-offset-gray-900 ring-current",
              "disabled:opacity-50"
            )}
          >
            {opt.emoji} {opt.label}
          </button>
        ))}
      </div>
      {total > 0 && (
        <div className="flex gap-2 text-xs text-gray-500">
          <span>🟢 {voteCounts.close ?? 0}</span>
          <span>🟡 {voteCounts.somewhat ?? 0}</span>
          <span>🔴 {voteCounts.different ?? 0}</span>
          <span className="ml-auto">{total} vote{total !== 1 ? "s" : ""}</span>
        </div>
      )}
    </div>
  );
}
