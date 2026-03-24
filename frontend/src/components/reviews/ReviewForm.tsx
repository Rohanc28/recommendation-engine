import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Star } from "lucide-react";
import { reviewsApi } from "../../services/api";

interface Props {
  movieId: string;
}

export default function ReviewForm({ movieId }: Props) {
  const [content, setContent] = useState("");
  const [rating, setRating] = useState(0);
  const [hover, setHover] = useState(0);
  const qc = useQueryClient();

  const mutation = useMutation({
    mutationFn: () => reviewsApi.create(movieId, { content, rating }),
    onSuccess: () => {
      setContent("");
      setRating(0);
      qc.invalidateQueries({ queryKey: ["reviews", movieId] });
      qc.invalidateQueries({ queryKey: ["movie", movieId] });
    },
  });

  const canSubmit = content.trim().length >= 10 && rating > 0;

  return (
    <form
      onSubmit={(e) => { e.preventDefault(); if (canSubmit) mutation.mutate(); }}
      className="card space-y-4"
    >
      <h3 className="font-semibold text-gray-200">Write a Review</h3>

      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => setRating(s)}
            onMouseEnter={() => setHover(s)}
            onMouseLeave={() => setHover(0)}
          >
            <Star
              className={`h-6 w-6 transition-colors ${
                s <= (hover || rating) ? "fill-yellow-400 text-yellow-400" : "text-gray-600"
              }`}
            />
          </button>
        ))}
        {rating > 0 && <span className="ml-2 text-sm text-gray-400">{rating}/5</span>}
      </div>

      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        rows={4}
        placeholder="Share your thoughts (min. 10 characters)…"
        className="input resize-none"
      />

      {mutation.isError && (
        <p className="text-sm text-red-400">
          {(mutation.error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Failed to submit review"}
        </p>
      )}

      <button type="submit" disabled={!canSubmit || mutation.isPending} className="btn-primary">
        {mutation.isPending ? "Submitting…" : "Submit Review"}
      </button>
    </form>
  );
}
