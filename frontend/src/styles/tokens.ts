export const colors = {
  kioskBg: "#F7F9FC",
  primary: "#2D7D9A",
  primaryHover: "#256888",
  secondary: "#F0F4F8",
  yes: "#3D9A6A",
  no: "#E85D4A",
  textPrimary: "#1A2332",
  textSecondary: "#6B7280",
  border: "#E5E7EB",
  scale1: "#E85D4A",
  scale2: "#F0934E",
  scale3: "#F5C842",
  scale4: "#8BC34A",
  scale5: "#4CAF50",
  dashSidebar: "#1E2A3A",
  dashSidebarText: "#E8EDF2",
  dashBg: "#F8FAFC",
  dashCard: "#FFFFFF",
  dashAccent: "#2D7D9A",
} as const;

export const scaleColors: Record<number, string> = {
  1: colors.scale1,
  2: colors.scale2,
  3: colors.scale3,
  4: colors.scale4,
  5: colors.scale5,
};

export const scaleEmojis: Record<number, string> = {
  1: "😞",
  2: "😕",
  3: "😐",
  4: "🙂",
  5: "😄",
};

export const scaleLabels: Record<number, string> = {
  1: "Erittäin tyytymätön",
  2: "Tyytymätön",
  3: "Neutraali",
  4: "Tyytyväinen",
  5: "Erittäin tyytyväinen",
};
