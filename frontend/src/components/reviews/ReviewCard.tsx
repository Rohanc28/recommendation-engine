import { Star, Trash2 } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { reviewsApi } from "../../services/api";
import { useAuthStore } from "../../store/authStore";
import type { Review } from "../../types";

interface Props {
  review: Review;
  movieId: string;
}

export default function ReviewCard({ review, movieId }: Props) {
  const { user } = useAuthStore();
  const qc = useQueryClient();

  const deleteMutation = useMutation({
    mutationFn: () => reviewsApi.delete(movieId, review.id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["reviews", movieId] }),
  });

  return (
    <div className="card space-y-2">
      <div className="flex items-start justify-between">
        <div>
          <span className="font-medium text-gray-200">{review.username}</span>
          <div className="flex gap-0.5 mt-0.5">
            {[1, 2, 3, 4, 5].map((s) => (
              <Star
                key={s}
                className={`h-3.5 w-3.5 ${s <= review.rating ? "fill-yellow-400 text-yellow-400" : "text-gray-600"}`}
              />
            ))}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">
            {new Date(review.created_at).toLocaleDateString()}
          </span>
          {user?.id === review.user_id && (
            <button
              onClick={() => deleteMutation.mutate()}
              disabled={deleteMutation.isPending}
              className="text-gray-600 hover:text-red-400 transition-colors"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
      </div>
      <p className="text-sm text-gray-300 leading-relaxed">{review.content}</p>
    </div>
  );
}
