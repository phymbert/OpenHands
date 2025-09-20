import { useQuery } from "@tanstack/react-query";
import SettingsService from "#/settings-service/settings-service.api";
import type { ArtifactoryRepositoryType } from "#/types/settings";

export function useArtifactoryRepositorySearch(
  query: string,
  repositoryType?: ArtifactoryRepositoryType | "",
  disabled?: boolean,
  limit: number = 20,
) {
  return useQuery({
    queryKey: [
      "artifactory",
      "repositories",
      "search",
      repositoryType || null,
      query,
      limit,
    ],
    queryFn: () =>
      SettingsService.searchArtifactoryRepositories(
        query,
        repositoryType || undefined,
        limit,
      ),
    enabled: !!query.trim() && !disabled,
    staleTime: 1000 * 60 * 5,
    gcTime: 1000 * 60 * 15,
  });
}
