import React from "react";
import { useTranslation } from "react-i18next";
import { useSaveSettings } from "#/hooks/mutation/use-save-settings";
import { useSettings } from "#/hooks/query/use-settings";
import { AvailableLanguages } from "#/i18n";
import { DEFAULT_SETTINGS } from "#/services/settings";
import { BrandButton } from "#/components/features/settings/brand-button";
import { SettingsSwitch } from "#/components/features/settings/settings-switch";
import { SettingsInput } from "#/components/features/settings/settings-input";
import { SettingsSelect } from "#/components/features/settings/settings-select";
import { I18nKey } from "#/i18n/declaration";
import { LanguageInput } from "#/components/features/settings/app-settings/language-input";
import { ArtifactoryRepositorySearchInput } from "#/components/features/settings/app-settings/artifactory-repository-search-input";
import { handleCaptureConsent } from "#/utils/handle-capture-consent";
import {
  displayErrorToast,
  displaySuccessToast,
} from "#/utils/custom-toast-handlers";
import { retrieveAxiosErrorMessage } from "#/utils/retrieve-axios-error-message";
import { AppSettingsInputsSkeleton } from "#/components/features/settings/app-settings/app-settings-inputs-skeleton";
import { useConfig } from "#/hooks/query/use-config";
import { parseMaxBudgetPerTask } from "#/utils/settings-utils";
import type { PostSettings } from "#/types/settings";
import {
  ArtifactoryRepositoryType,
  ArtifactoryRepositoryTypes,
} from "#/types/settings";
import { useArtifactoryRepositoryTypes } from "#/hooks/query/use-artifactory-repository-types";

const SUPPORTED_ARTIFACTORY_REPO_TYPES = Object.values(
  ArtifactoryRepositoryTypes,
) as ArtifactoryRepositoryType[];

const ARTIFACTORY_REPO_LABELS: Record<ArtifactoryRepositoryType, I18nKey> = {
  pypi: I18nKey.SETTINGS$ARTIFACTORY_REPO_PYPI,
  npm: I18nKey.SETTINGS$ARTIFACTORY_REPO_NPM,
  maven: I18nKey.SETTINGS$ARTIFACTORY_REPO_MAVEN,
  gradle: I18nKey.SETTINGS$ARTIFACTORY_REPO_GRADLE,
  go: I18nKey.SETTINGS$ARTIFACTORY_REPO_GO,
  nuget: I18nKey.SETTINGS$ARTIFACTORY_REPO_NUGET,
  docker: I18nKey.SETTINGS$ARTIFACTORY_REPO_DOCKER,
  helm: I18nKey.SETTINGS$ARTIFACTORY_REPO_HELM,
  terraform: I18nKey.SETTINGS$ARTIFACTORY_REPO_TERRAFORM,
  conan: I18nKey.SETTINGS$ARTIFACTORY_REPO_CONAN,
  cargo: I18nKey.SETTINGS$ARTIFACTORY_REPO_CARGO,
  composer: I18nKey.SETTINGS$ARTIFACTORY_REPO_COMPOSER,
  gems: I18nKey.SETTINGS$ARTIFACTORY_REPO_GEMS,
  cocoapods: I18nKey.SETTINGS$ARTIFACTORY_REPO_COCOAPODS,
  cran: I18nKey.SETTINGS$ARTIFACTORY_REPO_CRAN,
  pub: I18nKey.SETTINGS$ARTIFACTORY_REPO_PUB,
  sbt: I18nKey.SETTINGS$ARTIFACTORY_REPO_SBT,
  ivy: I18nKey.SETTINGS$ARTIFACTORY_REPO_IVY,
  swift: I18nKey.SETTINGS$ARTIFACTORY_REPO_SWIFT,
  bower: I18nKey.SETTINGS$ARTIFACTORY_REPO_BOWER,
};

type ArtifactoryRepositoryIntegration = {
  id: string;
  repositoryType: ArtifactoryRepositoryType | "";
  repositoryKey: string;
};

const createIntegration = (
  repositoryType?: ArtifactoryRepositoryType,
  repositoryKey?: string,
  id?: string,
): ArtifactoryRepositoryIntegration => ({
  id: id ?? `artifactory-${Math.random().toString(36).slice(2, 10)}`,
  repositoryType: repositoryType ?? "",
  repositoryKey: repositoryKey ?? "",
});

const mapRepositoriesToIntegrations = (
  repositories?: Partial<Record<ArtifactoryRepositoryType, string>>,
): ArtifactoryRepositoryIntegration[] => {
  if (!repositories) {
    return [];
  }

  return Object.entries(repositories).map(([type, repositoryKey]) =>
    createIntegration(
      type as ArtifactoryRepositoryType,
      repositoryKey || "",
      `artifactory-${type}`,
    ),
  );
};

const integrationsToRepositoryMap = (
  integrations: ArtifactoryRepositoryIntegration[],
): Partial<Record<ArtifactoryRepositoryType, string>> => {
  const result: Partial<Record<ArtifactoryRepositoryType, string>> = {};

  integrations.forEach(({ repositoryType, repositoryKey }) => {
    if (!repositoryType) {
      return;
    }
    const trimmed = repositoryKey.trim();
    if (trimmed) {
      result[repositoryType as ArtifactoryRepositoryType] = trimmed;
    }
  });

  return result;
};

const normalizeRepositoryMap = (
  map?: Partial<Record<ArtifactoryRepositoryType, string>>,
) => {
  const normalized: Record<string, string> = {};
  if (!map) {
    return normalized;
  }

  Object.entries(map).forEach(([type, repositoryKey]) => {
    if (typeof repositoryKey === "string") {
      const trimmed = repositoryKey.trim();
      if (trimmed) {
        normalized[type] = trimmed;
      }
    }
  });

  return normalized;
};

const repositoryMapsEqual = (
  a?: Partial<Record<ArtifactoryRepositoryType, string>>,
  b?: Partial<Record<ArtifactoryRepositoryType, string>>,
) => {
  const normalizedA = normalizeRepositoryMap(a);
  const normalizedB = normalizeRepositoryMap(b);
  const keysA = Object.keys(normalizedA);
  const keysB = Object.keys(normalizedB);
  if (keysA.length !== keysB.length) {
    return false;
  }
  return keysA.every((key) => normalizedA[key] === normalizedB[key]);
};

function AppSettingsScreen() {
  const { t } = useTranslation();

  const { mutate: saveSettings, isPending } = useSaveSettings();
  const { data: settings, isLoading } = useSettings();
  const { data: config } = useConfig();
  const { data: repoTypesFromApi } = useArtifactoryRepositoryTypes();

  const repositoryTypes = React.useMemo(
    () => repoTypesFromApi ?? SUPPORTED_ARTIFACTORY_REPO_TYPES,
    [repoTypesFromApi],
  );
  const artifactoryRepositoryOptions = React.useMemo(
    () =>
      repositoryTypes.map((type) => {
        const labelKey = ARTIFACTORY_REPO_LABELS[type];
        return {
          value: type,
          label: labelKey ? t(labelKey) : type,
        };
      }),
    [repositoryTypes, t],
  );

  const [languageInputHasChanged, setLanguageInputHasChanged] =
    React.useState(false);
  const [analyticsSwitchHasChanged, setAnalyticsSwitchHasChanged] =
    React.useState(false);
  const [
    soundNotificationsSwitchHasChanged,
    setSoundNotificationsSwitchHasChanged,
  ] = React.useState(false);
  const [
    proactiveConversationsSwitchHasChanged,
    setProactiveConversationsSwitchHasChanged,
  ] = React.useState(false);
  const [
    solvabilityAnalysisSwitchHasChanged,
    setSolvabilityAnalysisSwitchHasChanged,
  ] = React.useState(false);
  const [maxBudgetPerTaskHasChanged, setMaxBudgetPerTaskHasChanged] =
    React.useState(false);
  const [gitUserNameHasChanged, setGitUserNameHasChanged] =
    React.useState(false);
  const [gitUserEmailHasChanged, setGitUserEmailHasChanged] =
    React.useState(false);
  const [artifactoryHostHasChanged, setArtifactoryHostHasChanged] =
    React.useState(false);
  const [
    artifactoryCliInstallUrlHasChanged,
    setArtifactoryCliInstallUrlHasChanged,
  ] = React.useState(false);
  const [artifactoryApiKeyHasChanged, setArtifactoryApiKeyHasChanged] =
    React.useState(false);
  const [artifactoryClearApiKey, setArtifactoryClearApiKey] =
    React.useState(false);
  const [artifactoryApiKeyInputValue, setArtifactoryApiKeyInputValue] =
    React.useState("");
  const [artifactoryIntegrations, setArtifactoryIntegrations] = React.useState<
    ArtifactoryRepositoryIntegration[]
  >([]);

  React.useEffect(() => {
    const repositories = settings?.ARTIFACTORY_REPOSITORIES;
    setArtifactoryIntegrations(mapRepositoriesToIntegrations(repositories));
  }, [settings?.ARTIFACTORY_REPOSITORIES]);

  const artifactoryRepositoriesPayload = React.useMemo(
    () => integrationsToRepositoryMap(artifactoryIntegrations),
    [artifactoryIntegrations],
  );

  const artifactoryReposHaveChanged = React.useMemo(
    () =>
      !repositoryMapsEqual(
        settings?.ARTIFACTORY_REPOSITORIES,
        artifactoryRepositoriesPayload,
      ),
    [settings?.ARTIFACTORY_REPOSITORIES, artifactoryRepositoriesPayload],
  );

  React.useEffect(() => {
    setArtifactoryHostHasChanged(false);
    setArtifactoryCliInstallUrlHasChanged(false);
    setArtifactoryApiKeyHasChanged(false);
    setArtifactoryClearApiKey(false);
    setArtifactoryApiKeyInputValue("");
  }, [
    settings?.ARTIFACTORY_HOST,
    settings?.ARTIFACTORY_CLI_INSTALL_URL,
    settings?.ARTIFACTORY_API_KEY_SET,
  ]);

  const formAction = (formData: FormData) => {
    const languageLabel = formData.get("language-input")?.toString();
    const languageValue = AvailableLanguages.find(
      ({ label }) => label === languageLabel,
    )?.value;
    const language = languageValue || DEFAULT_SETTINGS.LANGUAGE;

    const enableAnalytics =
      formData.get("enable-analytics-switch")?.toString() === "on";
    const enableSoundNotifications =
      formData.get("enable-sound-notifications-switch")?.toString() === "on";

    const enableProactiveConversations =
      formData.get("enable-proactive-conversations-switch")?.toString() ===
      "on";

    const enableSolvabilityAnalysis =
      formData.get("enable-solvability-analysis-switch")?.toString() === "on";

    const maxBudgetPerTaskValue = formData
      .get("max-budget-per-task-input")
      ?.toString();
    const maxBudgetPerTask = parseMaxBudgetPerTask(maxBudgetPerTaskValue || "");

    const gitUserName =
      formData.get("git-user-name-input")?.toString() ||
      DEFAULT_SETTINGS.GIT_USER_NAME;
    const gitUserEmail =
      formData.get("git-user-email-input")?.toString() ||
      DEFAULT_SETTINGS.GIT_USER_EMAIL;

    const artifactoryHost =
      formData.get("artifactory-host-input")?.toString().trim() || "";
    const artifactoryCliInstallUrl =
      formData.get("artifactory-cli-install-url-input")?.toString().trim() ??
      "";
    const artifactoryApiKeyInput =
      formData.get("artifactory-api-key-input")?.toString().trim() || "";

    const shouldSendArtifactoryKey =
      artifactoryClearApiKey || artifactoryApiKeyHasChanged;

    let artifactoryApiKeyPayload: string | undefined;
    if (artifactoryClearApiKey) {
      artifactoryApiKeyPayload = "";
    } else if (artifactoryApiKeyHasChanged) {
      artifactoryApiKeyPayload = artifactoryApiKeyInput;
    }

    const payload: Partial<PostSettings> = {
      LANGUAGE: language,
      user_consents_to_analytics: enableAnalytics,
      ENABLE_SOUND_NOTIFICATIONS: enableSoundNotifications,
      ENABLE_PROACTIVE_CONVERSATION_STARTERS: enableProactiveConversations,
      ENABLE_SOLVABILITY_ANALYSIS: enableSolvabilityAnalysis,
      MAX_BUDGET_PER_TASK: maxBudgetPerTask,
      GIT_USER_NAME: gitUserName,
      GIT_USER_EMAIL: gitUserEmail,
      ARTIFACTORY_HOST: artifactoryHost,
      ARTIFACTORY_CLI_INSTALL_URL: artifactoryCliInstallUrl,
      ARTIFACTORY_REPOSITORIES: artifactoryRepositoriesPayload,
    };

    if (shouldSendArtifactoryKey) {
      payload.artifactory_api_key = artifactoryApiKeyPayload ?? "";
    }

    saveSettings(payload, {
      onSuccess: () => {
        handleCaptureConsent(enableAnalytics);
        displaySuccessToast(t(I18nKey.SETTINGS$SAVED));
      },
      onError: (error) => {
        const errorMessage = retrieveAxiosErrorMessage(error);
        displayErrorToast(errorMessage || t(I18nKey.ERROR$GENERIC));
      },
      onSettled: () => {
        setLanguageInputHasChanged(false);
        setAnalyticsSwitchHasChanged(false);
        setSoundNotificationsSwitchHasChanged(false);
        setProactiveConversationsSwitchHasChanged(false);
        setMaxBudgetPerTaskHasChanged(false);
        setGitUserNameHasChanged(false);
        setGitUserEmailHasChanged(false);
        setArtifactoryHostHasChanged(false);
        setArtifactoryCliInstallUrlHasChanged(false);
        setArtifactoryApiKeyHasChanged(false);
        setArtifactoryClearApiKey(false);
        setArtifactoryApiKeyInputValue("");
      },
    });
  };

  const checkIfLanguageInputHasChanged = (value: string) => {
    const selectedLanguage = AvailableLanguages.find(
      ({ label: langValue }) => langValue === value,
    )?.label;
    const currentLanguage = AvailableLanguages.find(
      ({ value: langValue }) => langValue === settings?.LANGUAGE,
    )?.label;

    setLanguageInputHasChanged(selectedLanguage !== currentLanguage);
  };

  const checkIfAnalyticsSwitchHasChanged = (checked: boolean) => {
    const currentAnalytics = !!settings?.USER_CONSENTS_TO_ANALYTICS;
    setAnalyticsSwitchHasChanged(checked !== currentAnalytics);
  };

  const checkIfSoundNotificationsSwitchHasChanged = (checked: boolean) => {
    const currentSoundNotifications = !!settings?.ENABLE_SOUND_NOTIFICATIONS;
    setSoundNotificationsSwitchHasChanged(
      checked !== currentSoundNotifications,
    );
  };

  const checkIfProactiveConversationsSwitchHasChanged = (checked: boolean) => {
    const currentProactiveConversations =
      !!settings?.ENABLE_PROACTIVE_CONVERSATION_STARTERS;
    setProactiveConversationsSwitchHasChanged(
      checked !== currentProactiveConversations,
    );
  };

  const checkIfSolvabilityAnalysisSwitchHasChanged = (checked: boolean) => {
    const currentSolvabilityAnalysis = !!settings?.ENABLE_SOLVABILITY_ANALYSIS;
    setSolvabilityAnalysisSwitchHasChanged(
      checked !== currentSolvabilityAnalysis,
    );
  };

  const checkIfMaxBudgetPerTaskHasChanged = (value: string) => {
    const newValue = parseMaxBudgetPerTask(value);
    const currentValue = settings?.MAX_BUDGET_PER_TASK;
    setMaxBudgetPerTaskHasChanged(newValue !== currentValue);
  };

  const checkIfGitUserNameHasChanged = (value: string) => {
    const currentValue = settings?.GIT_USER_NAME;
    setGitUserNameHasChanged(value !== currentValue);
  };

  const checkIfGitUserEmailHasChanged = (value: string) => {
    const currentValue = settings?.GIT_USER_EMAIL;
    setGitUserEmailHasChanged(value !== currentValue);
  };

  const checkIfArtifactoryHostHasChanged = (value: string) => {
    const currentHost = settings?.ARTIFACTORY_HOST || "";
    setArtifactoryHostHasChanged(value !== currentHost);
  };

  const checkIfArtifactoryCliInstallUrlHasChanged = (value: string) => {
    const normalizedValue = value.trim();
    const currentValue =
      settings?.ARTIFACTORY_CLI_INSTALL_URL ??
      DEFAULT_SETTINGS.ARTIFACTORY_CLI_INSTALL_URL ??
      "";
    setArtifactoryCliInstallUrlHasChanged(
      normalizedValue !== currentValue.trim(),
    );
  };

  const handleArtifactoryApiKeyInputChange = (value: string) => {
    const trimmed = value.trim();
    setArtifactoryApiKeyInputValue(value);
    setArtifactoryApiKeyHasChanged(trimmed.length > 0);
    if (trimmed.length > 0) {
      setArtifactoryClearApiKey(false);
    }
  };
  const handleArtifactoryTypeChange = React.useCallback(
    (id: string, value: string) => {
      setArtifactoryIntegrations((prev) =>
        prev.map((integration) => {
          if (integration.id !== id) {
            return integration;
          }

          const candidate = value as ArtifactoryRepositoryType;
          const isValid = repositoryTypes.includes(candidate);
          const nextType = isValid ? candidate : "";
          const shouldResetRepository = nextType !== integration.repositoryType;

          return {
            ...integration,
            repositoryType: nextType,
            repositoryKey: shouldResetRepository
              ? ""
              : integration.repositoryKey,
          };
        }),
      );
    },
    [repositoryTypes],
  );

  const handleArtifactoryRepositoryChange = React.useCallback(
    (id: string) => (value: string) => {
      setArtifactoryIntegrations((prev) =>
        prev.map((integration) =>
          integration.id === id
            ? { ...integration, repositoryKey: value }
            : integration,
        ),
      );
    },
    [],
  );

  const handleRemoveArtifactoryIntegration = React.useCallback((id: string) => {
    setArtifactoryIntegrations((prev) =>
      prev.filter((integration) => integration.id !== id),
    );
  }, []);

  const handleAddArtifactoryIntegration = React.useCallback(() => {
    setArtifactoryIntegrations((prev) => [...prev, createIntegration()]);
  }, []);

  const formIsClean =
    !languageInputHasChanged &&
    !analyticsSwitchHasChanged &&
    !soundNotificationsSwitchHasChanged &&
    !proactiveConversationsSwitchHasChanged &&
    !solvabilityAnalysisSwitchHasChanged &&
    !maxBudgetPerTaskHasChanged &&
    !gitUserNameHasChanged &&
    !gitUserEmailHasChanged &&
    !artifactoryHostHasChanged &&
    !artifactoryCliInstallUrlHasChanged &&
    !artifactoryApiKeyHasChanged &&
    !artifactoryClearApiKey &&
    !artifactoryReposHaveChanged;

  const shouldBeLoading = !settings || isLoading || isPending;

  return (
    <form
      data-testid="app-settings-screen"
      action={formAction}
      className="flex flex-col h-full justify-between"
    >
      {shouldBeLoading && <AppSettingsInputsSkeleton />}
      {!shouldBeLoading && (
        <div className="p-9 flex flex-col gap-6">
          <LanguageInput
            name="language-input"
            defaultKey={settings.LANGUAGE}
            onChange={checkIfLanguageInputHasChanged}
          />

          <SettingsSwitch
            testId="enable-analytics-switch"
            name="enable-analytics-switch"
            defaultIsToggled={!!settings.USER_CONSENTS_TO_ANALYTICS}
            onToggle={checkIfAnalyticsSwitchHasChanged}
          >
            {t(I18nKey.ANALYTICS$SEND_ANONYMOUS_DATA)}
          </SettingsSwitch>

          <SettingsSwitch
            testId="enable-sound-notifications-switch"
            name="enable-sound-notifications-switch"
            defaultIsToggled={!!settings.ENABLE_SOUND_NOTIFICATIONS}
            onToggle={checkIfSoundNotificationsSwitchHasChanged}
          >
            {t(I18nKey.SETTINGS$SOUND_NOTIFICATIONS)}
          </SettingsSwitch>

          {config?.APP_MODE === "saas" && (
            <SettingsSwitch
              testId="enable-proactive-conversations-switch"
              name="enable-proactive-conversations-switch"
              defaultIsToggled={
                !!settings.ENABLE_PROACTIVE_CONVERSATION_STARTERS
              }
              onToggle={checkIfProactiveConversationsSwitchHasChanged}
            >
              {t(I18nKey.SETTINGS$PROACTIVE_CONVERSATION_STARTERS)}
            </SettingsSwitch>
          )}

          {config?.APP_MODE === "saas" && (
            <SettingsSwitch
              testId="enable-solvability-analysis-switch"
              name="enable-solvability-analysis-switch"
              defaultIsToggled={!!settings.ENABLE_SOLVABILITY_ANALYSIS}
              onToggle={checkIfSolvabilityAnalysisSwitchHasChanged}
            >
              {t(I18nKey.SETTINGS$SOLVABILITY_ANALYSIS)}
            </SettingsSwitch>
          )}

          <SettingsInput
            testId="max-budget-per-task-input"
            name="max-budget-per-task-input"
            type="number"
            label={t(I18nKey.SETTINGS$MAX_BUDGET_PER_CONVERSATION)}
            defaultValue={settings.MAX_BUDGET_PER_TASK?.toString() || ""}
            onChange={checkIfMaxBudgetPerTaskHasChanged}
            placeholder={t(I18nKey.SETTINGS$MAXIMUM_BUDGET_USD)}
            min={1}
            step={1}
            className="w-full max-w-[680px]" // Match the width of the language field
          />

          <div className="border-t border-t-tertiary pt-6 mt-2">
            <h3 className="text-lg font-medium mb-2">
              {t(I18nKey.SETTINGS$GIT_SETTINGS)}
            </h3>
            <p className="text-xs mb-4">
              {t(I18nKey.SETTINGS$GIT_SETTINGS_DESCRIPTION)}
            </p>
            <div className="flex flex-col gap-6">
              <SettingsInput
                testId="git-user-name-input"
                name="git-user-name-input"
                type="text"
                label={t(I18nKey.SETTINGS$GIT_USERNAME)}
                defaultValue={settings.GIT_USER_NAME || ""}
                onChange={checkIfGitUserNameHasChanged}
                placeholder="Username for git commits"
                className="w-full max-w-[680px]"
              />
              <SettingsInput
                testId="git-user-email-input"
                name="git-user-email-input"
                type="email"
                label={t(I18nKey.SETTINGS$GIT_EMAIL)}
                defaultValue={settings.GIT_USER_EMAIL || ""}
                onChange={checkIfGitUserEmailHasChanged}
                placeholder="Email for git commits"
                className="w-full max-w-[680px]"
              />
            </div>
          </div>

          <div className="border-t border-t-tertiary pt-6 mt-2 flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <h3 className="text-lg font-medium">
                {t(I18nKey.SETTINGS$ARTIFACTORY_TITLE)}
              </h3>
              <p className="text-xs text-tertiary">
                {t(I18nKey.SETTINGS$ARTIFACTORY_DESCRIPTION)}
              </p>
            </div>
            <SettingsInput
              testId="artifactory-host-input"
              name="artifactory-host-input"
              type="text"
              label={t(I18nKey.SETTINGS$ARTIFACTORY_HOST)}
              defaultValue={settings.ARTIFACTORY_HOST || ""}
              onChange={checkIfArtifactoryHostHasChanged}
              placeholder="https://example.jfrog.io/artifactory"
              className="w-full max-w-[680px]"
            />
            <SettingsInput
              testId="artifactory-cli-install-url-input"
              name="artifactory-cli-install-url-input"
              type="text"
              label={t(I18nKey.SETTINGS$ARTIFACTORY_CLI_INSTALL_URL)}
              defaultValue={
                settings.ARTIFACTORY_CLI_INSTALL_URL ??
                DEFAULT_SETTINGS.ARTIFACTORY_CLI_INSTALL_URL ??
                ""
              }
              onChange={checkIfArtifactoryCliInstallUrlHasChanged}
              placeholder={t(
                I18nKey.SETTINGS$ARTIFACTORY_CLI_INSTALL_URL_PLACEHOLDER,
              )}
              className="w-full max-w-[680px]"
            />
            <SettingsInput
              testId="artifactory-api-key-input"
              name="artifactory-api-key-input"
              type="password"
              label={t(I18nKey.SETTINGS$ARTIFACTORY_API_KEY)}
              placeholder={t(I18nKey.SETTINGS$ARTIFACTORY_API_KEY_PLACEHOLDER)}
              onChange={handleArtifactoryApiKeyInputChange}
              className="w-full max-w-[680px]"
            />
            {settings.ARTIFACTORY_API_KEY_SET && (
              <SettingsSwitch
                testId="clear-artifactory-api-key-switch"
                name="clear-artifactory-api-key-switch"
                defaultIsToggled={false}
                onToggle={(checked) => {
                  setArtifactoryClearApiKey(checked);
                  if (checked) {
                    setArtifactoryApiKeyHasChanged(true);
                  } else {
                    setArtifactoryApiKeyHasChanged(
                      artifactoryApiKeyInputValue.trim().length > 0,
                    );
                  }
                }}
              >
                {t(I18nKey.SETTINGS$ARTIFACTORY_CLEAR_KEY)}
              </SettingsSwitch>
            )}
            <div className="flex flex-col gap-3">
              <div>
                <span className="text-sm font-medium">
                  {t(I18nKey.SETTINGS$ARTIFACTORY_REPOSITORIES)}
                </span>
                <p className="text-xs text-tertiary mt-1">
                  {t(I18nKey.SETTINGS$ARTIFACTORY_REPOSITORIES_DESCRIPTION)}
                </p>
              </div>
              <div className="flex flex-col gap-4">
                {artifactoryIntegrations.length === 0 && (
                  <p className="text-xs text-tertiary">
                    {t(I18nKey.SETTINGS$ARTIFACTORY_REPOSITORIES_EMPTY)}
                  </p>
                )}
                {artifactoryIntegrations.map((integration) => {
                  const usedTypes = artifactoryIntegrations
                    .filter(
                      (item) =>
                        item.id !== integration.id && item.repositoryType,
                    )
                    .map(
                      (item) => item.repositoryType,
                    ) as ArtifactoryRepositoryType[];

                  const availableOptions = artifactoryRepositoryOptions.filter(
                    (option) =>
                      option.value === integration.repositoryType ||
                      !usedTypes.includes(
                        option.value as ArtifactoryRepositoryType,
                      ),
                  );

                  return (
                    <div
                      key={integration.id}
                      className="flex flex-col gap-3 rounded-sm border border-tertiary/50 p-4"
                    >
                      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                        <SettingsSelect
                          testId={`artifactory-repo-${integration.id}-type`}
                          label={t(
                            I18nKey.SETTINGS$ARTIFACTORY_REPOSITORY_TYPE_LABEL,
                          )}
                          value={integration.repositoryType || ""}
                          onChange={(value) =>
                            handleArtifactoryTypeChange(integration.id, value)
                          }
                          options={availableOptions}
                          placeholder={t(
                            I18nKey.SETTINGS$ARTIFACTORY_REPOSITORY_TYPE_PLACEHOLDER,
                          )}
                          showOptionalTag
                          className="w-full"
                        />
                        <ArtifactoryRepositorySearchInput
                          testId={`artifactory-repo-${integration.id}-name`}
                          label={t(
                            I18nKey.SETTINGS$ARTIFACTORY_REPOSITORY_NAME_LABEL,
                          )}
                          placeholder={t(
                            I18nKey.SETTINGS$ARTIFACTORY_REPOSITORY_PLACEHOLDER,
                          )}
                          repositoryType={integration.repositoryType}
                          value={integration.repositoryKey}
                          disabled={!integration.repositoryType}
                          onChange={handleArtifactoryRepositoryChange(
                            integration.id,
                          )}
                          loadingText={t(
                            I18nKey.SETTINGS$ARTIFACTORY_REPOSITORY_LOADING,
                          )}
                          emptyText={t(
                            I18nKey.SETTINGS$ARTIFACTORY_REPOSITORY_EMPTY_RESULTS,
                          )}
                          className="w-full"
                        />
                      </div>
                      <div className="flex justify-end">
                        <BrandButton
                          variant="ghost-danger"
                          type="button"
                          onClick={() =>
                            handleRemoveArtifactoryIntegration(integration.id)
                          }
                          isDisabled={isPending}
                        >
                          {t(I18nKey.SETTINGS$ARTIFACTORY_REMOVE_REPOSITORY)}
                        </BrandButton>
                      </div>
                    </div>
                  );
                })}
                <BrandButton
                  variant="secondary"
                  type="button"
                  onClick={handleAddArtifactoryIntegration}
                  isDisabled={
                    isPending ||
                    repositoryTypes.length === 0 ||
                    artifactoryIntegrations.length >= repositoryTypes.length
                  }
                >
                  {t(I18nKey.SETTINGS$ARTIFACTORY_ADD_REPOSITORY)}
                </BrandButton>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="flex gap-6 p-6 justify-end border-t border-t-tertiary">
        <BrandButton
          testId="submit-button"
          variant="primary"
          type="submit"
          isDisabled={isPending || formIsClean}
        >
          {!isPending && t("SETTINGS$SAVE_CHANGES")}
          {isPending && t("SETTINGS$SAVING")}
        </BrandButton>
      </div>
    </form>
  );
}

export default AppSettingsScreen;
