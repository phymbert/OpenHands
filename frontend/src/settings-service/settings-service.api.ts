import { openHands } from "../api/open-hands-axios";
import { ApiSettings, PostApiSettings } from "./settings.types";

/**
 * Settings service for managing application settings
 */
class SettingsService {
  /**
   * Get the settings from the server or use the default settings if not found
   */
  static async getSettings(): Promise<ApiSettings> {
    const { data } = await openHands.get<ApiSettings>("/api/settings");
    return data;
  }

  static async getArtifactoryRepositoryTypes(): Promise<string[]> {
    const { data } = await openHands.get<string[]>(
      "/api/settings/artifactory/repository-types",
    );
    return data;
  }

  static async searchArtifactoryRepositories(
    query: string,
    repositoryType?: string,
    limit: number = 20,
  ): Promise<string[]> {
    const { data } = await openHands.get<string[]>(
      "/api/settings/artifactory/repositories/search",
      {
        params: {
          query,
          limit,
          ...(repositoryType ? { type: repositoryType } : {}),
        },
      },
    );
    return data;
  }

  /**
   * Save the settings to the server. Only valid settings are saved.
   * @param settings - the settings to save
   */
  static async saveSettings(
    settings: Partial<PostApiSettings>,
  ): Promise<boolean> {
    const data = await openHands.post("/api/settings", settings);
    return data.status === 200;
  }
}

export default SettingsService;
