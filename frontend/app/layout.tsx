import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Predictor Mundial 2026",
  description:
    "Predicción del Mundial 2026 desde octavos: Elo real + lesiones y cansancio, con simulación Monte Carlo y batallas animadas.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
