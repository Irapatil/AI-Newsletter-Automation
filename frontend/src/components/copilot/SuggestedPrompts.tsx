import { motion } from "framer-motion";
import { SUGGESTED_PROMPTS, type PromptKey } from "@/hooks/use-copilot-chat";
import { cn } from "@/lib/utils";

interface SuggestedPromptsProps {
  onSelect: (key: PromptKey, label: string) => void;
  disabled?: boolean;
  className?: string;
}

export function SuggestedPrompts({ onSelect, disabled, className }: SuggestedPromptsProps) {
  return (
    <div className={cn("flex flex-wrap justify-center gap-2.5", className)}>
      {SUGGESTED_PROMPTS.map((prompt, index) => (
        <motion.button
          key={prompt.key}
          type="button"
          disabled={disabled}
          onClick={() => onSelect(prompt.key, prompt.label)}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.05, duration: 0.3 }}
          whileHover={{ scale: disabled ? 1 : 1.03 }}
          whileTap={{ scale: disabled ? 1 : 0.98 }}
          className={cn(
            "rounded-full border border-border/70 bg-card/60 px-4 py-2 text-sm text-foreground/90",
            "backdrop-blur-sm transition-colors hover:border-primary/50 hover:bg-accent hover:text-accent-foreground",
            "disabled:cursor-not-allowed disabled:opacity-50",
          )}
        >
          {prompt.label}
        </motion.button>
      ))}
    </div>
  );
}
