import React from "react";
import { formatCzechUSD, formatPct1, formatSignedPct } from "../lib/format.js";

// Key numbers rendered bold + brand green.
function Num({ children }) {
  return <strong style={{ color: "#008C00" }}>{children}</strong>;
}

const num = (x) => (Number.isFinite(Number(x)) ? Number(x) : null);

/**
 * One-sentence summary of the selected opportunity, computed client-side from
 * the selected signal + the already-fetched /insights_data (panelVM.keyData).
 * Renders nothing when no signal is selected or the inputs are insufficient.
 */
export default function OpportunityHeadline({
  signal = null,
  keyData = null,
  referenceData = { countryNames: {}, hs6Labels: {} },
}) {
  if (!signal) return null;

  const type = signal.type || "";
  const isSynthetic = !!signal.synthetic;
  const isPeer = !isSynthetic && type.includes("Peer_gap");
  const isYoY =
    isSynthetic ||
    type === "YoY_export_change" ||
    type === "YoY_partner_share_change";

  const countryName =
    referenceData?.countryNames?.[signal.partner_iso3] ||
    signal.partner_name ||
    signal.partner_iso3 ||
    "";
  const hs6Name =
    referenceData?.hs6Labels?.[String(signal.hs6 || "")] ||
    signal.hs6_name ||
    "produktu";

  let content = null;

  if (isPeer) {
    // Prefer the fetched insights_data; fall back to the signal's own fields
    // (value IS the CZ share decimal on peer rows) when keyData lags behind.
    const share = num(keyData?.cz_share_in_c) ?? num(signal.value);
    const median = num(keyData?.median_peer_share) ?? num(signal.peer_median);
    const importTotal = num(keyData?.c_import_total);
    if (share == null || median == null) return null;

    if (median < 0.001) {
      content = (
        <>Srovnatelné trhy tento produkt téměř nedovážejí — benchmark není vypovídající.</>
      );
    } else if (share >= median) {
      content = (
        <>
          ČR je s podílem <Num>{formatPct1(share)}</Num> NAD mediánem
          srovnatelných trhů (<Num>{formatPct1(median)}</Num>).
        </>
      );
    } else {
      const gapUsd = importTotal != null ? (median - share) * importTotal : null;
      content = (
        <>
          ČR dodává <Num>{formatPct1(share)}</Num> importu {hs6Name} do země{" "}
          {countryName} (medián srovnatelných trhů{" "}
          <Num>{formatPct1(median)}</Num>)
          {gapUsd != null ? (
            <>
              {" "}— dorovnání mediánu ≈ <Num>+{formatCzechUSD(gapUsd)}</Num>{" "}
              ročně.
            </>
          ) : (
            <>.</>
          )}
        </>
      );
    }
  } else if (isYoY) {
    const cur = num(keyData?.cz_to_c);
    // yoy in percent units (815.7 = +815.7 %); a synthetic placeholder 0 means unknown
    const yoy =
      num(keyData?.cz_delta_pct) ??
      (num(signal.yoy) !== null && Number(signal.yoy) !== 0
        ? Number(signal.yoy)
        : null);
    let prev = num(keyData?.cz_to_c_prev);
    if (prev == null && cur != null && yoy != null && yoy !== -100) {
      prev = cur / (1 + yoy / 100); // derive previous-year value from YoY
    }
    if (cur == null && yoy == null) return null;

    const verb =
      yoy != null
        ? yoy >= 0
          ? "vzrostl"
          : "klesl"
        : prev != null && cur != null
          ? cur >= prev
            ? "vzrostl"
            : "klesl"
          : "dosáhl"; // no direction known — neutral phrasing

    content = (
      <>
        {isSynthetic ? "Vlastní analýza: " : ""}Český export do země{" "}
        {countryName} {verb}
        {prev != null && <> z <Num>{formatCzechUSD(prev)}</Num></>}
        {cur != null && <> na <Num>{formatCzechUSD(cur)}</Num></>}
        {yoy != null && (
          <> (<Num>{formatSignedPct(yoy)}</Num> meziročně)</>
        )}
        .
      </>
    );
  }

  if (!content) return null;

  return (
    <div
      style={{
        border: "1px solid #eee",
        borderRadius: 6,
        padding: "12px 14px",
        background: "#fff",
        fontSize: 16.5,
        lineHeight: 1.5,
      }}
    >
      {content}
    </div>
  );
}
