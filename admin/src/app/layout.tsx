import React from "react";

export const metadata = {
  title: "KORAS — Super-Admin & Observability Portal",
  description: "Portail d'administration KORAS : Audit, Appareils, Politiques et Simulation Sandbox",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr">
      <head>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css" />
        <style>{`
          :root {
            --pico-primary: #6c63ff;
            --pico-background-color: #0f111a;
            --pico-card-background-color: #171926;
            --pico-color: #e2e8f0;
          }
          body { padding: 20px; font-family: system-ui, -apple-system, sans-serif; }
          .badge { padding: 4px 8px; border-radius: 6px; font-size: 12px; font-weight: bold; }
          .badge-critical { background: #ef4444; color: white; }
          .badge-success { background: #22c55e; color: white; }
          .badge-warning { background: #f59e0b; color: white; }
          .header-nav { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; border-bottom: 1px solid #2d3748; padding-bottom: 1rem; }
        `}</style>
      </head>
      <body>{children}</body>
    </html>
  );
}
