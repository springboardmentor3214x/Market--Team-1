import { useEffect, useState } from "react";
import createPlotlyComponent from "react-plotly.js/factory";
import Plotly from "plotly.js-dist-min";
import { searchCompanies, getOverview, getSavedPreferences } from "./api.js";

const Plot = createPlotlyComponent(Plotly);

const MARKETS = ["", "NSE", "BSE", "NYSE", "NASDAQ"];
const PERIODS = ["1M", "3M", "6M", "1Y", "3Y", "5Y"];

const fmt = (n, d = 2) =>
  n === null || n === undefined ? "—" : Number(n).toLocaleString(undefined, { maximumFractionDigits: d });
const fmtDate = (iso) => (iso ? new Date(iso).toLocaleString() : "—");

const styles = {
  page: { maxWidth: 1100, margin: "24px auto", padding: "0 16px", fontFamily: "system-ui, sans-serif", color: "#1f2937" },
  card: { border: "1px solid #e5e7eb", borderRadius: 8, padding: 16, margin: "16px 0", background: "#fff" },
  input: { padding: 8, border: "1px solid #cbd5e1", borderRadius: 6 },
  btn: { padding: "8px 16px", border: "none", borderRadius: 6, background: "#2563eb", color: "#fff", cursor: "pointer" },
  th: { textAlign: "right", padding: "4px 8px", borderBottom: "1px solid #e5e7eb", whiteSpace: "nowrap" },
  td: { textAlign: "right", padding: "4px 8px", borderBottom: "1px solid #f1f5f9" },
  muted: { color: "#64748b", fontSize: 13 },
  err: { color: "#b91c1c", background: "#fef2f2", padding: 10, borderRadius: 6 },
  warn: { color: "#92400e", background: "#fffbeb", padding: 10, borderRadius: 6, margin: "8px 0" },
};

export default function StockSearchPage() {
  const [query, setQuery] = useState("");
  const [market, setMarket] = useState("");
  const [period, setPeriod] = useState("1Y");
  const [results, setResults] = useState([]);
  const [searchWarnings, setSearchWarnings] = useState([]);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [tab, setTab] = useState("income_statement");

  // Pre-fill market + period from the user's Module 1 preferences (if logged in)
  useEffect(() => {
    getSavedPreferences().then((p) => {
      if (p && !p.is_default) {
        setMarket(p.preferred_market);
        setPeriod(p.analysis_period);
      }
    });
  }, []);

  const doSearch = async (e) => {
    e?.preventDefault();
    setError(""); setResults([]); setData(null); setSearchWarnings([]);
    if (!query.trim()) return setError("Enter a company name or ticker symbol.");
    setLoading(true);
    try {
      const r = await searchCompanies(query.trim(), market);
      setResults(r.results);
      setSearchWarnings(r.warnings || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadStock = async (symbol, mkt) => {
    setError(""); setData(null); setLoading(true);
    try {
      setData(await getOverview(symbol, period, mkt));
      setTab("income_statement");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.page}>
      <h1>Stock Search &amp; Market Data</h1>
      <form onSubmit={doSearch} style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <input style={{ ...styles.input, flex: 1, minWidth: 220 }} value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Company name or ticker, e.g. Infosys, INFY, Apple, MSFT" />
        <select style={styles.input} value={market} onChange={(e) => setMarket(e.target.value)}>
          {MARKETS.map((m) => <option key={m} value={m}>{m || "All markets"}</option>)}
        </select>
        <select style={styles.input} value={period} onChange={(e) => setPeriod(e.target.value)}>
          {PERIODS.map((p) => <option key={p} value={p}>{p}</option>)}
        </select>
        <button style={styles.btn} disabled={loading}>{loading ? "Loading…" : "Search"}</button>
      </form>

      {error && <p style={styles.err}>{error}</p>}
      {searchWarnings.map((w, i) => <p key={i} style={styles.warn}>{w}</p>)}

      {results.length > 0 && !data && (
        <div style={styles.card}>
          <h3>Select a company</h3>
          {results.map((r) => (
            <div key={r.symbol} onClick={() => loadStock(r.symbol, r.market)}
              style={{ padding: 8, borderBottom: "1px solid #f1f5f9", cursor: "pointer" }}>
              <b>{r.symbol}</b> — {r.name}{" "}
              <span style={styles.muted}>({r.market}, {r.currency})</span>
            </div>
          ))}
        </div>
      )}

      {data && <StockDetails data={data} tab={tab} setTab={setTab} onBack={() => setData(null)} />}
    </div>
  );
}

function StockDetails({ data, tab, setTab, onBack }) {
  const { company, profile, history, financials, warnings } = data;
  const rows = history.rows;
  const v = history.validation;

  return (
    <>
      <button onClick={onBack} style={{ ...styles.btn, background: "#64748b" }}>← Back to results</button>

      <div style={styles.card}>
        <h2 style={{ margin: 0 }}>{company.name || company.symbol} <span style={styles.muted}>({company.symbol})</span></h2>
        <p style={styles.muted}>
          {company.exchange || "—"} · {company.market || "—"} · Currency: <b>{company.currency || "—"}</b>
          {company.sector && <> · {company.sector}</>}{company.industry && <> / {company.industry}</>}
        </p>
        {profile.data?.description && <p style={{ fontSize: 14 }}>{profile.data.description.slice(0, 450)}…</p>}
        {!profile.available && <p style={styles.warn}>{profile.message}</p>}
      </div>

      {warnings.map((w, i) => <p key={i} style={styles.warn}>⚠ {w}</p>)}

      <div style={styles.card}>
        <h3>Price history ({history.period}) — {history.row_count} trading days</h3>
        {rows.length === 0 ? <p>No usable price data.</p> : (
          <Plot
            data={[
              { type: "candlestick", x: rows.map((r) => r.date), open: rows.map((r) => r.open),
                high: rows.map((r) => r.high), low: rows.map((r) => r.low), close: rows.map((r) => r.close),
                name: "OHLC" },
              { type: "bar", x: rows.map((r) => r.date), y: rows.map((r) => r.volume), name: "Volume",
                yaxis: "y2", marker: { color: "#cbd5e1" } },
            ]}
            layout={{ height: 420, margin: { t: 20, l: 50, r: 50 }, xaxis: { rangeslider: { visible: false } },
              yaxis: { title: `Price (${company.currency || ""})` },
              yaxis2: { overlaying: "y", side: "right", showgrid: false, title: "Volume" }, showlegend: false }}
            config={{ responsive: true }} style={{ width: "100%" }} useResizeHandler />
        )}
        <p style={styles.muted}>
          Prices from {history.first_trading_date} to {history.last_trading_date}. {history.price_basis}.
        </p>
        <details>
          <summary>Latest 15 OHLCV rows</summary>
          <div style={{ overflowX: "auto" }}>
            <table style={{ borderCollapse: "collapse", width: "100%" }}>
              <thead><tr>{["Date", "Open", "High", "Low", "Close", "Volume"].map((h) => <th key={h} style={styles.th}>{h}</th>)}</tr></thead>
              <tbody>
                {rows.slice(-15).reverse().map((r) => (
                  <tr key={r.date}>
                    <td style={styles.td}>{r.date}</td><td style={styles.td}>{fmt(r.open)}</td>
                    <td style={styles.td}>{fmt(r.high)}</td><td style={styles.td}>{fmt(r.low)}</td>
                    <td style={styles.td}>{fmt(r.close)}</td><td style={styles.td}>{fmt(r.volume, 0)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      </div>

      <div style={styles.card}>
        <h3>Data quality: <span style={{ color: v.status === "clean" ? "#15803d" : v.status === "cleaned" ? "#b45309" : "#b91c1c" }}>{v.status.toUpperCase()}</span></h3>
        <p>Received {v.rows_received} rows · valid {v.rows_valid} · removed {v.rows_removed}</p>
        {v.issues.length === 0 ? <p>No problems found in the {v.checks_performed.length} checks performed.</p> : (
          <ul>
            {v.issues.map((i, k) => (
              <li key={k}><b>{i.type.replace(/_/g, " ")}</b> ({i.count}) — {i.description}. <i>{i.action}.</i>
                {i.sample_dates.length > 0 && <span style={styles.muted}> e.g. {i.sample_dates.slice(0, 3).join(", ")}</span>}
              </li>
            ))}
          </ul>
        )}
        <details><summary>Checks performed</summary>
          <ul>{v.checks_performed.map((c) => <li key={c}>{c}</li>)}</ul></details>
      </div>

      <div style={styles.card}>
        <h3>Financial statements</h3>
        <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
          {Object.entries(financials.statements).map(([key, s]) => (
            <button key={key} onClick={() => setTab(key)}
              style={{ ...styles.btn, background: tab === key ? "#2563eb" : "#94a3b8" }}>{s.label}</button>
          ))}
        </div>
        <Statement s={financials.statements[tab]} />
        <p style={styles.muted}>{financials.metadata.frequency}</p>
      </div>

      <div style={styles.card}>
        <h3>Data sources &amp; retrieval time</h3>
        <table style={{ borderCollapse: "collapse" }}>
          <tbody>
            {[["Company profile", profile.metadata], ["Price history", history.metadata], ["Financial statements", financials.metadata]].map(([label, m]) => (
              <tr key={label}>
                <td style={{ padding: "4px 12px 4px 0" }}><b>{label}</b></td>
                <td style={{ padding: "4px 12px" }}>{m.source}</td>
                <td style={{ padding: "4px 12px" }}>Retrieved: {fmtDate(m.retrieved_at)}</td>
                <td style={{ padding: "4px 12px" }}><a href={m.source_url} target="_blank" rel="noreferrer">source link</a></td>
              </tr>
            ))}
          </tbody>
        </table>
        <p style={styles.muted}>Retrieval time is when we downloaded the data; each price row's date is its trading day.</p>
      </div>
    </>
  );
}

function Statement({ s }) {
  if (!s?.available) return <p style={styles.warn}>{s?.message || "Not available."}</p>;
  const periods = s.periods.slice(0, 4);
  return (
    <div style={{ overflowX: "auto", maxHeight: 360, overflowY: "auto" }}>
      <table style={{ borderCollapse: "collapse", width: "100%" }}>
        <thead>
          <tr><th style={{ ...styles.th, textAlign: "left" }}>Item</th>{periods.map((p) => <th key={p} style={styles.th}>{p}</th>)}</tr>
        </thead>
        <tbody>
          {Object.entries(s.items).map(([name, vals]) => (
            <tr key={name}>
              <td style={{ ...styles.td, textAlign: "left" }}>{name}</td>
              {periods.map((p) => <td key={p} style={styles.td}>{fmt(vals[p], 0)}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
