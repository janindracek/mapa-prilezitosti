// Chart calculation functions extracted from App.jsx

export function calcSupplierShareByPartner({ czExportsByPartner = {}, importTotalsByPartner = {}, focusCountry }) {
  const entries = Object.keys(importTotalsByPartner).map(iso3 => {
    const imp = importTotalsByPartner[iso3] ?? 0;
    const cz = czExportsByPartner[iso3] ?? 0;
    const share = imp > 0 ? cz / imp : null;
    return { iso3, name: iso3, value: share };
  }).filter(d => d.value !== null);

  entries.sort((a, b) => (b.value ?? 0) - (a.value ?? 0));

  const barData = entries.slice(0, 10).map(d => ({
    id: d.iso3, name: d.name, value: d.value, aux: czExportsByPartner[d.iso3] ?? 0
  }));

  const keyData = focusCountry ? {
    cz_to_c: czExportsByPartner[focusCountry] ?? 0,
    c_import_total: importTotalsByPartner[focusCountry] ?? 0,
    cz_share_in_c: (importTotalsByPartner[focusCountry] ?? 0) > 0
      ? (czExportsByPartner[focusCountry] ?? 0) / (importTotalsByPartner[focusCountry] ?? 1)
      : null
  } : null;

  const mapData = entries.map(({ iso3, name, value }) => ({ iso3, name, value }));
  return { mapData, barData, keyData };
}

export function calcDeltaExportByPartner({ czExportsCurr = {}, czExportsPrev = {}, focusCountry }) {
  const isos = new Set([...Object.keys(czExportsCurr), ...Object.keys(czExportsPrev)]);
  const entries = Array.from(isos).map(iso3 => {
    const curr = Number(czExportsCurr[iso3] ?? 0);
    const prev = Number(czExportsPrev[iso3] ?? 0);
    const delta = curr - prev;
    return { iso3, name: iso3, value: delta, curr, prev };
  });

  entries.sort((a, b) => (b.value ?? 0) - (a.value ?? 0));

  const barData = entries.slice(0, 10).map(d => ({
    id: d.iso3, name: d.name, value: d.value, aux: d.curr
  }));

  let keyData = null;
  if (focusCountry) {
    const row = entries.find(e => e.iso3 === focusCountry) || { curr: 0, prev: 0, value: 0 };
    const pct = row.prev > 0 ? (row.curr / row.prev - 1) : (row.curr > 0 ? 1 : 0);
    keyData = { cz_curr: row.curr, cz_prev: row.prev, cz_delta_abs: row.value, cz_delta_pct: pct };
  }

  const mapData = entries.map(({ iso3, name, value }) => ({ iso3, name, value }));
  return { mapData, barData, keyData };
}

export function calcShareInCzExportsByPartner({
  czExportsCurrByPartner = {},
  czExportsPrevByPartner = {},
  czWorldCurr = 0,
  czWorldPrev = 0,
  focusCountry
}) {
  const isos = new Set([...Object.keys(czExportsCurrByPartner), ...Object.keys(czExportsPrevByPartner)]);
  const entries = Array.from(isos).map(iso3 => {
    const curr = Number(czExportsCurrByPartner[iso3] ?? 0);
    const prev = Number(czExportsPrevByPartner[iso3] ?? 0);
    const shareCurr = czWorldCurr > 0 ? curr / czWorldCurr : null;
    const sharePrev = czWorldPrev > 0 ? prev / czWorldPrev : null;
    const deltaShare = (shareCurr !== null && sharePrev !== null) ? (shareCurr - sharePrev) : null;
    return { iso3, name: iso3, value: shareCurr, aux: curr, deltaShare };
  }).filter(d => d.value !== null);

  entries.sort((a, b) => (b.value ?? 0) - (a.value ?? 0));

  const barData = entries.slice(0, 10).map(d => ({ id: d.iso3, name: d.name, value: d.value, aux: d.aux }));

  let keyData = null;
  if (focusCountry) {
    const row = entries.find(e => e.iso3 === focusCountry) || null;
    if (row) {
      const rank = entries.findIndex(e => e.iso3 === focusCountry) + 1;
      keyData = {
        share_in_cz: row.value,                 // fraction 0..1
        share_delta_pp: row.deltaShare !== null ? (row.deltaShare * 100) : null, // percentage points
        rank_in_cz_exports: rank,
        cz_to_c: Number(czExportsCurrByPartner[focusCountry] ?? 0),
        cz_world_total: Number(czWorldCurr ?? 0)
      };
    }
  }

  const mapData = entries.map(({ iso3, name, value }) => ({ iso3, name, value }));
  return { mapData, barData, keyData };
}