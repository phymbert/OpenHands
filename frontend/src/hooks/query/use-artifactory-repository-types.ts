import { useQuery } from "@tanstack/react-query";

import { useIsOnTosPage } from "#/hooks/use-is-on-tos-page";
import SettingsService from "#/settings-service/settings-service.api";
import {
  ArtifactoryRepositoryType,
  ArtifactoryRepositoryTypes,
} from "#/types/settings";

import { useIsAuthed } from "./use-is-authed";

const SUPPORTED_TYPES = Object.values(
  ArtifactoryRepositoryTypes,
) as ArtifactoryRepositoryType[];

const normalizeRepositoryTypes = (
  repositoryTypes: string[],
): ArtifactoryRepositoryType[] => {
  const supported = new Set<string>(SUPPORTED_TYPES);

  const normalized = repositoryTypes
    .map((type) => type.trim().toLowerCase())
    .filter((type): type is ArtifactoryRepositoryType => supported.has(type));

  const unique = Array.from(new Set(normalized));
  return unique.length > 0 ? unique : SUPPORTED_TYPES;
};

export const useArtifactoryRepositoryTypes = () => {
  const isOnTosPage = useIsOnTosPage();
  const { data: userIsAuthenticated } = useIsAuthed();

  return useQuery({
    queryKey: ["settings", "artifactory", "repository-types"],
    queryFn: async () => {
      const types = await SettingsService.getArtifactoryRepositoryTypes();
      return normalizeRepositoryTypes(types);
    },
    staleTime: 1000 * 60 * 5,
    gcTime: 1000 * 60 * 15,
    enabled: !isOnTosPage && !!userIsAuthenticated,
    meta: {
      disableToast: true,
    },
  });
};
