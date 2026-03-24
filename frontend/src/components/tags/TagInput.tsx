import { useState, KeyboardEvent } from "react";
import { X } from "lucide-react";
import clsx from "clsx";

interface Props {
  value: string[];
  onChange: (tags: string[]) => void;
  min?: number;
  max?: number;
}

export default function TagInput({ value, onChange, min = 3, max = 5 }: Props) {
  const [input, setInput] = useState("");

  const addTag = (raw: string) => {
    const tag = raw.trim().toLowerCase();
    if (!tag) return;
    if (value.includes(tag)) { setInput(""); return; }
    if (value.length >= max) return;
    onChange([...value, tag]);
    setInput("");
  };

  const removeTag = (tag: string) => onChange(value.filter((t) => t !== tag));

  const handleKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addTag(input);
    } else if (e.key === "Backspace" && !input && value.length > 0) {
      onChange(value.slice(0, -1));
    }
  };

  const atMax = value.length >= max;
  const hint = `${value.length}/${max} tags${value.length < min ? ` (need ${min - value.length} more)` : ""}`;

  return (
    <div className="space-y-2">
      <div className={clsx(
        "flex flex-wrap gap-2 rounded-lg border bg-gray-900 p-2 transition-colors",
        atMax ? "border-gray-700" : "border-gray-700 focus-within:border-brand-500"
      )}>
        {value.map((tag) => (
          <span key={tag} className="flex items-center gap-1 rounded-md bg-brand-900/50 px-2 py-0.5 text-sm text-brand-300 border border-brand-800">
            {tag}
            <button type="button" onClick={() => removeTag(tag)} className="hover:text-brand-100">
              <X className="h-3 w-3" />
            </button>
          </span>
        ))}
        {!atMax && (
          <input
            className="flex-1 min-w-24 bg-transparent text-sm text-gray-100 placeholder-gray-500 outline-none"
            placeholder={value.length === 0 ? `Type a tag and press Enter (${min}–${max} required)` : "Add another tag…"}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
            onBlur={() => addTag(input)}
          />
        )}
      </div>
      <p className={clsx("text-xs", value.length < min ? "text-gray-500" : "text-green-500")}>
        {hint}
      </p>
    </div>
  );
}
