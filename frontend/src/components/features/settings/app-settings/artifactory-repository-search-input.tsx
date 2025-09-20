/* eslint-disable react/jsx-props-no-spreading */
import React from "react";
import { useCombobox } from "downshift";

import { useArtifactoryRepositorySearch } from "#/hooks/query/use-artifactory-repository-search";
import { useDebounce } from "#/hooks/use-debounce";
import type { ArtifactoryRepositoryType } from "#/types/settings";
import { cn } from "#/utils/utils";

interface ArtifactoryRepositorySearchInputProps {
  label: string;
  placeholder?: string;
  repositoryType?: ArtifactoryRepositoryType | "";
  value?: string;
  disabled?: boolean;
  className?: string;
  testId?: string;
  onChange?: (value: string) => void;
  loadingText: string;
  emptyText: string;
}

export function ArtifactoryRepositorySearchInput({
  label,
  placeholder,
  repositoryType,
  value,
  disabled,
  className,
  testId,
  onChange,
  loadingText,
  emptyText,
}: ArtifactoryRepositorySearchInputProps) {
  const [inputValue, setInputValue] = React.useState(value ?? "");
  const debouncedQuery = useDebounce(inputValue, 300);

  const { data: repositories = [], isFetching } =
    useArtifactoryRepositorySearch(
      debouncedQuery,
      repositoryType,
      disabled || !repositoryType,
    );

  React.useEffect(() => {
    setInputValue(value ?? "");
  }, [value]);

  const {
    isOpen,
    getMenuProps,
    getInputProps,
    getItemProps,
    highlightedIndex,
    openMenu,
  } = useCombobox({
    items: repositories,
    itemToString: (item) => item ?? "",
    inputValue,
    onInputValueChange: ({ inputValue: newValue }) => {
      const nextValue = newValue ?? "";
      setInputValue(nextValue);
      onChange?.(nextValue);
    },
    onSelectedItemChange: ({ selectedItem }) => {
      if (selectedItem) {
        setInputValue(selectedItem);
        onChange?.(selectedItem);
      }
    },
  });

  return (
    <label className={cn("flex flex-col gap-2.5", className)}>
      <span className="text-sm">{label}</span>
      <div className="relative">
        <input
          {...getInputProps({
            "data-testid": testId,
            placeholder,
            disabled: disabled || !repositoryType,
            onFocus: () => {
              if (!disabled && repositoryType) {
                openMenu();
              }
            },
            className: cn(
              "bg-tertiary border border-[#717888] h-10 w-full rounded-sm p-2 placeholder:italic placeholder:text-tertiary-alt",
              "disabled:bg-[#2D2F36] disabled:border-[#2D2F36] disabled:cursor-not-allowed",
            ),
          })}
        />
        <ul
          {...getMenuProps({
            className: cn(
              "absolute z-10 mt-1 w-full max-h-48 overflow-auto rounded-sm border border-[#717888] bg-[#1E1F25] shadow-lg",
              !isOpen && "hidden",
            ),
          })}
        >
          {isOpen && (
            <>
              {isFetching && (
                <li className="px-3 py-2 text-xs text-tertiary">
                  {loadingText}
                </li>
              )}
              {!isFetching && repositories.length === 0 && (
                <li className="px-3 py-2 text-xs text-tertiary">{emptyText}</li>
              )}
              {!isFetching &&
                repositories.map((item, index) => (
                  <li
                    key={item}
                    className={cn(
                      "px-3 py-2 text-sm cursor-pointer hover:bg-white/10",
                      highlightedIndex === index && "bg-white/10",
                    )}
                    {...getItemProps({ item, index })}
                  >
                    {item}
                  </li>
                ))}
            </>
          )}
        </ul>
      </div>
    </label>
  );
}
