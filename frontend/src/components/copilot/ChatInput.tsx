import { useState, type FormEvent } from "react";
import { ArrowUp, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSubmit: (text: string) => void;
  disabled?: boolean;
  className?: string;
}

export function ChatInput({ onSubmit, disabled, className }: ChatInputProps) {
  const [value, setValue] = useState("");

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSubmit(trimmed);
    setValue("");
  }

  return (
    <form
      onSubmit={handleSubmit}
      className={cn(
        "glass flex items-center gap-2 rounded-2xl p-2 shadow-lg shadow-black/5",
        className,
      )}
    >
      <Sparkles className="ml-2 h-4 w-4 shrink-0 text-primary" />
      <input
        value={value}
        onChange={(event) => setValue(event.target.value)}
        disabled={disabled}
        placeholder="Ask the Copilot — e.g. “What's happening in AI funding today?”"
        className="h-10 flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground disabled:cursor-not-allowed"
      />
      <Button
        type="submit"
        size="icon"
        disabled={disabled || value.trim().length === 0}
        className="shrink-0 rounded-xl"
        aria-label="Send"
      >
        <ArrowUp className="h-4 w-4" />
      </Button>
    </form>
  );
}
