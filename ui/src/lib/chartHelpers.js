// Chart helper functions extracted from App.jsx

export function fmtHs6Dot(code) {
  const raw = String(code ?? "").trim();
  const digits = raw.replace(/\D/g, "");
  if (!digits) return "";
  const s = digits.padStart(6, "0");
  if (/^0{6}$/.test(s)) return "";
  return `${s.slice(0,4)}.${s.slice(4)}`;
}

export function barChartTitle(meta = {}, signalType = null) {
  const hs = fmtHs6Dot(meta.hs6);
  const y = Number(meta.year) || null;
  
  // Signal-specific titles
  if (signalType?.includes('Peer_gap')) {
    const groupType = signalType === 'Peer_gap_human' ? 'geografická' : 
                     signalType === 'Peer_gap_opportunity' ? 'příležitostní' : 'strukturální';
    return `Benchmark skupina (${groupType}) — HS6 ${hs || '—'}${y ? `, ${y}` : ''}`;
  } else if (signalType === 'YoY_export_change' || signalType === 'YoY_partner_share_change') {
    return `Top partneři českého exportu — HS6 ${hs || '—'}${y ? `, ${y}` : ''}`;
  }
  
  // Fallback based on metric
  if (meta.metric === 'cz_share_in_partner_import') {
    return `Top 10 partnerů podle českého exportu — HS6 ${hs || '—'}${y ? `, ${y}` : ''}`;
  }
  // default for YoY/export/import-change views
  return `Top 10 importérů — HS6 ${hs || '—'}${y ? `, ${y}` : ''}`;
}

export function barChartSubtitle(signalType = null, partnerCounts = {}) {
  const { totalPartners, peerGroupPartners } = partnerCounts;
  
  if (!totalPartners && !peerGroupPartners) {
    return "Celkový český export do jednotlivých zemí (seřazeno sestupně)\nHodnoty: objem exportu v USD";
  }
  
  if (signalType?.includes('Peer_gap')) {
    if (totalPartners && peerGroupPartners) {
      return `Ukazuje ${peerGroupPartners} exportních partnerů v peer group, z celkem ${totalPartners} exportních partnerů Česka celkem.\nHodnoty: objem českého exportu v USD`;
    } else if (peerGroupPartners) {
      return `Ukazuje ${peerGroupPartners} exportních partnerů v peer group.\nHodnoty: objem českého exportu v USD`;
    }
  } else if (signalType === 'YoY_export_change' || signalType === 'YoY_partner_share_change') {
    if (totalPartners && peerGroupPartners) {
      return `Ukazuje ${peerGroupPartners} největších exportních partnerů z celkem ${totalPartners} partnerů Česka.\nHodnoty: objem českého exportu v USD`;
    } else if (peerGroupPartners) {
      return `Ukazuje ${peerGroupPartners} největších exportních partnerů Česka.\nHodnoty: objem českého exportu v USD`;
    }
  }
  
  return "Celkový český export do jednotlivých zemí (seřazeno sestupně)\nHodnoty: objem exportu v USD";
}