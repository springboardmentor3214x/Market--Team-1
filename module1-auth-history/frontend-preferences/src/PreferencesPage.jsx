import { useEffect, useState } from "react";
import { getPreferences, savePreferences, resetPreferences } from "./api";

const MARKETS = [
  { value: "NSE", label: "NSE – National Stock Exchange of India (INR)" },
  { value: "BSE", label: "BSE – Bombay Stock Exchange (INR)" },
  { value: "NYSE", label: "NYSE – New York Stock Exchange (USD)" },
  { value: "NASDAQ", label: "Nasdaq (USD)" },
];

const PERIODS = [
  { value: "1M", label: "1 Month" },
  { value: "3M", label: "3 Months" },
  { value: "6M", label: "6 Months" },
  { value: "1Y", label: "1 Year" },
  { value: "3Y", label: "3 Years" },
  { value: "5Y", label: "5 Years" },
];

export default function PreferencesPage() {
  const [market, setMarket] = useState("");
  const [period, setPeriod] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null); // { type: "success" | "error", text }

  // Load saved preferences (or defaults) when the page opens
  useEffect(() => {
    getPreferences()
      .then((p) => {
        setMarket(p.preferred_market);
        setPeriod(p.analysis_period);
      })
      .catch((e) => setMessage({ type: "error", text: e.message }))
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    setMessage(null);
    if (!market || !period) {
      setMessage({ type: "error", text: "Please select both a market and an analysis period." });
      return;
    }
    setSaving(true);
    try {
      await savePreferences({ preferred_market: market, analysis_period: period });
      setMessage({ type: "success", text: "Preferences saved." });
    } catch (err) {
      setMessage({ type: "error", text: err.message });
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    setMessage(null);
    try {
      await resetPreferences();
      const p = await getPreferences();
      setMarket(p.preferred_market);
      setPeriod(p.analysis_period);
      setMessage({ type: "success", text: "Preferences reset to defaults." });
    } catch (err) {
      setMessage({ type: "error", text: err.message });
    }
  };

  if (loading) return <p>Loading preferences…</p>;

  return (
    <div style={{ maxWidth: 480, margin: "40px auto", fontFamily: "sans-serif" }}>
      <h2>Research Preferences</h2>
      <p style={{ color: "#555" }}>
        These choices are used as defaults whenever you start a new stock research.
      </p>

      <form onSubmit={handleSave}>
        <label htmlFor="market">Preferred stock market</label>
        <select
          id="market"
          value={market}
          onChange={(e) => setMarket(e.target.value)}
          style={{ display: "block", width: "100%", padding: 8, margin: "6px 0 16px" }}
        >
          <option value="" disabled>Select a market</option>
          {MARKETS.map((m) => (
            <option key={m.value} value={m.value}>{m.label}</option>
          ))}
        </select>

        <label htmlFor="period">Analysis period</label>
        <select
          id="period"
          value={period}
          onChange={(e) => setPeriod(e.target.value)}
          style={{ display: "block", width: "100%", padding: 8, margin: "6px 0 16px" }}
        >
          <option value="" disabled>Select a period</option>
          {PERIODS.map((p) => (
            <option key={p.value} value={p.value}>{p.label}</option>
          ))}
        </select>

        <button type="submit" disabled={saving} style={{ padding: "8px 16px" }}>
          {saving ? "Saving…" : "Save preferences"}
        </button>
        <button type="button" onClick={handleReset} style={{ padding: "8px 16px", marginLeft: 8 }}>
          Reset to defaults
        </button>
      </form>

      {message && (
        <p style={{ marginTop: 16, color: message.type === "success" ? "green" : "crimson" }}>
          {message.text}
        </p>
      )}
    </div>
  );
}
