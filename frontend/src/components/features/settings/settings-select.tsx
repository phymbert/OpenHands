import { cn } from "#/utils/utils";
import { OptionalTag } from "./optional-tag";

interface SettingsSelectOption {
  value: string;
  label: string;
}

interface SettingsSelectProps {
  testId?: string;
  name?: string;
  label: string;
  value?: string;
  placeholder?: string;
  options: SettingsSelectOption[];
  showOptionalTag?: boolean;
  isDisabled?: boolean;
  className?: string;
  labelClassName?: string;
  onChange?: (value: string) => void;
}

export function SettingsSelect({
  testId,
  name,
  label,
  value,
  placeholder,
  options,
  showOptionalTag,
  isDisabled,
  className,
  labelClassName,
  onChange,
}: SettingsSelectProps) {
  return (
    <label className={cn("flex flex-col gap-2.5 w-fit", className)}>
      <div className="flex items-center gap-2">
        <span className={cn("text-sm", labelClassName)}>{label}</span>
        {showOptionalTag && <OptionalTag />}
      </div>
      <select
        data-testid={testId}
        name={name}
        value={value ?? ""}
        disabled={isDisabled}
        onChange={(event) => onChange?.(event.target.value)}
        className={cn(
          "bg-tertiary border border-[#717888] h-10 w-full rounded-sm p-2",
          "disabled:bg-[#2D2F36] disabled:border-[#2D2F36] disabled:cursor-not-allowed",
        )}
      >
        {placeholder && (
          <option value="" disabled hidden>
            {placeholder}
          </option>
        )}
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}
