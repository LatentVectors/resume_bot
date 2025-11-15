import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";

interface ButtonConfig {
  label: string;
  onClick?: () => void;
  variant?: "default" | "outline";
  disabled?: boolean;
  loading?: boolean;
  type?: "button" | "submit";
  form?: string;
}

interface IntakeStepHeaderProps {
  step: 1 | 2 | 3;
  subtitle: string;
  leftButtons?: ButtonConfig[];
  rightButtons?: ButtonConfig[];
}

export function IntakeStepHeader({
  step,
  subtitle,
  leftButtons,
  rightButtons,
}: IntakeStepHeaderProps) {
  return (
    <div className="flex items-center justify-between pt-3 pb-2">
      <div className="flex items-center gap-4">
        <h1 className="text-xl font-semibold">
          Job Intake: Step {step} of 3 - {subtitle}
        </h1>
      </div>
      <div className="flex items-center gap-4">
        {leftButtons && leftButtons.length > 0 && (
          <div className="flex gap-2">
            {leftButtons.map((button, index) => (
              <Button
                key={index}
                variant={button.variant || "outline"}
                onClick={button.onClick}
                disabled={button.disabled || button.loading}
                type={button.type || "button"}
                form={button.form}
              >
                {button.loading && (
                  <Loader2 className="mr-2 size-4 animate-spin" />
                )}
                {button.label}
              </Button>
            ))}
          </div>
        )}
        {rightButtons && rightButtons.length > 0 && (
          <div className="flex gap-2">
            {rightButtons.map((button, index) => (
              <Button
                key={index}
                variant={button.variant || "default"}
                onClick={button.onClick}
                disabled={button.disabled || button.loading}
                type={button.type || "button"}
                form={button.form}
              >
                {button.loading && (
                  <Loader2 className="mr-2 size-4 animate-spin" />
                )}
                {button.label}
              </Button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
