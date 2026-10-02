"use client";

import React, { useState, useEffect } from "react";

export default function AdminDashboard() {
  const [activeTab, setActiveTab] = useState("simulation");
  const [simQuery, setSimQuery] = useState("Envoie 5000 francs à maman");
  const [simVulnerable, setSimVulnerable] = useState(false);
  const [simBattery, setSimBattery] = useState(85);
  const [simOffline, setSimOffline] = useState(false);
  const [simResult, setSimResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  // Simulated metrics (Section 45)
  const metrics = {
    intentAccuracy: "96.4%",
    falseActionRate: "0.0%",
    criticalBlocked: "14",
    activeDevices: "128",
  };

  const handleSimulate = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/v1/admin/simulation/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          simulated_query: simQuery,
          vulnerable_user: simVulnerable,
          battery_level: simBattery,
          is_offline: simOffline,
        }),
      });
      const data = await res.json();
      setSimResult(data);
    } catch (e) {
      setSimResult({ error: "Impossible de joindre le backend FastAPI sur http://127.0.0.1:8000" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="container">
      <header className="header-nav">
        <div>
          <h2>⚡ KORAS — Administration & Supervision</h2>
          <small>Version 1.0.0 • Architecture modulaire agentique</small>
        </div>
        <div>
          <button
            className={activeTab === "simulation" ? "primary" : "secondary"}
            onClick={() => setActiveTab("simulation")}
            style={{ marginRight: 8 }}
          >
            🧪 Sandbox Simulateur
          </button>
          <button
            className={activeTab === "audit" ? "primary" : "secondary"}
            onClick={() => setActiveTab("audit")}
            style={{ marginRight: 8 }}
          >
            📋 Logs d'Audit
          </button>
          <button
            className={activeTab === "devices" ? "primary" : "secondary"}
            onClick={() => setActiveTab("devices")}
          >
            📱 Appareils
          </button>
        </div>
      </header>

      {/* Métriques clés (Section 45) */}
      <section className="grid" style={{ marginBottom: "2rem" }}>
        <article>
          <small>Précision des Intentions</small>
          <h3>{metrics.intentAccuracy}</h3>
        </article>
        <article>
          <small>Taux d'Action Erronée (False Action)</small>
          <h3 style={{ color: "#22c55e" }}>{metrics.falseActionRate}</h3>
        </article>
        <article>
          <small>Actions Critiques Bloquées / Auditées</small>
          <h3 style={{ color: "#ef4444" }}>{metrics.criticalBlocked}</h3>
        </article>
        <article>
          <small>Appareils Certifiés</small>
          <h3>{metrics.activeDevices}</h3>
        </article>
      </section>

      {/* Onglet 1 : Sandbox Simulation (Section 69) */}
      {activeTab === "simulation" && (
        <article>
          <header>
            <h4>Simulateur d'Agent et Tests de Contraintes (Section 69)</h4>
            <p>
              Exécutez des intentions dans un bac à sable isolé sans impacter les comptes réels.
            </p>
          </header>

          <div className="grid">
            <div>
              <label>
                Commande vocale / texte à tester :
                <input
                  type="text"
                  value={simQuery}
                  onChange={(e) => setSimQuery(e.target.value)}
                  placeholder="ex: Envoie 10000 francs à Koffi"
                />
              </label>

              <div className="grid">
                <label>
                  Niveau Batterie ({simBattery}%) :
                  <input
                    type="range"
                    min="1"
                    max="100"
                    value={simBattery}
                    onChange={(e) => setSimBattery(Number(e.target.value))}
                  />
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={simOffline}
                    onChange={(e) => setSimOffline(e.target.checked)}
                  />
                  Simuler Mode Hors-ligne
                </label>
              </div>

              <label>
                <input
                  type="checkbox"
                  checked={simVulnerable}
                  onChange={(e) => setSimVulnerable(e.target.checked)}
                />
                Activer Mode Utilisateur Vulnérable (Section 62)
              </label>

              <button onClick={handleSimulate} disabled={loading} style={{ marginTop: 12 }}>
                {loading ? "Exécution de la simulation..." : "Lancer la simulation agentique"}
              </button>
            </div>

            <div>
              <h5>Sortie Runtime de l'Agent :</h5>
              {simResult ? (
                <pre style={{ background: "#0a0c12", padding: 16, borderRadius: 8, fontSize: 13 }}>
                  {JSON.stringify(simResult, null, 2)}
                </pre>
              ) : (
                <div style={{ padding: 24, textAlign: "center", color: "#64748b" }}>
                  Cliquez sur "Lancer la simulation" pour voir le plan et l'évaluation du risque.
                </div>
              )}
            </div>
          </div>
        </article>
      )}

      {/* Onglet 2 : Logs d'Audit (Section 68) */}
      {activeTab === "audit" && (
        <article>
          <h4>Journal d'Audit Immuable (Section 68)</h4>
          <table>
            <thead>
              <tr>
                <th>Horodatage</th>
                <th>Événement</th>
                <th>Acteur</th>
                <th>Ressource</th>
                <th>Niveau Risque</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>2026-09-29 02:18:15</td>
                <td><span className="badge badge-critical">TRANSFER_CONFIRMED</span></td>
                <td>User (phone: +225 07070707)</td>
                <td>Wave / 5 000 XOF</td>
                <td>Niveau 4 (Critique)</td>
              </tr>
              <tr>
                <td>2026-09-29 01:45:00</td>
                <td><span className="badge badge-warning">POLICY_DENIAL</span></td>
                <td>Agent (Device: Pixel 8)</td>
                <td>Transfert suspendu (Batterie 4%)</td>
                <td>Niveau 4 (Critique)</td>
              </tr>
              <tr>
                <td>2026-09-29 01:30:12</td>
                <td><span className="badge badge-success">ACTION_CALL_VERIFIED</span></td>
                <td>User (phone: +225 01010101)</td>
                <td>Appel Contact: Maman</td>
                <td>Niveau 2 (Externe)</td>
              </tr>
            </tbody>
          </table>
        </article>
      )}

      {/* Onglet 3 : Appareils & Sécurité (Section 71 & 73) */}
      {activeTab === "devices" && (
        <article>
          <h4>Gestion des Appareils & Révocations (Section 71 & 73)</h4>
          <table>
            <thead>
              <tr>
                <th>Appareil</th>
                <th>Utilisateur</th>
                <th>Version Android</th>
                <th>Statut de Confiance</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Samsung Galaxy A15 (dev_samsung_01)</td>
                <td>+225 07070707</td>
                <td>Android 14</td>
                <td><span className="badge badge-success">CERTIFIÉ</span></td>
                <td><button className="secondary" style={{ padding: "4px 8px", fontSize: 12 }}>Révoquer</button></td>
              </tr>
              <tr>
                <td>Infinix Hot 40 (dev_infinix_99)</td>
                <td>+225 05050505</td>
                <td>Android 13</td>
                <td><span className="badge badge-critical">RÉVOQUÉ</span></td>
                <td><span style={{ fontSize: 12, color: "#94a3b8" }}>Bloqué</span></td>
              </tr>
            </tbody>
          </table>
        </article>
      )}
    </main>
  );
}
