import { useState } from "react";

/** On/off toggle for the Power Automate page's real-time workflow narration. */
export function useAutomationInsights(): [boolean, (value: boolean) => void] {
  const [enabled, setEnabled] = useState(false);
  return [enabled, setEnabled];
}
