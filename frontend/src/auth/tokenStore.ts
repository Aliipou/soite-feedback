let accessToken: string | null = null;

export const setAccessToken = (token: string): void => {
  accessToken = token;
};

export const getAccessToken = (): string | null => accessToken;

export const clearAccessToken = (): void => {
  accessToken = null;
};

export const hasAccessToken = (): boolean => accessToken !== null;
