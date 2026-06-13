import React, { useMemo, useRef, useEffect } from "react";
import ReactEChartsCore from "echarts-for-react/lib/core";
import echarts from "../lib/echarts.js";

// World geometry is bundled in ui/public/world.json (served at /world.json) so the
// map works on restricted/offline networks — no live raw.githubusercontent.com call.
let worldMapRegistered = false;

async function loadCleanWorldMap() {
  if (worldMapRegistered) return;

  try {
    const response = await fetch(`${import.meta.env.BASE_URL || "/"}world.json`);
    const geoData = await response.json();

    // Clean up problematic geometries
    geoData.features = geoData.features.filter(f => {
      const props = f.properties || {};
      const name = props.NAME || props.name;
      // Skip problematic features that cause rendering issues
      return name && name !== "Antarctica";
    });

    echarts.registerMap("world", geoData);
    buildNameMappings(geoData); // Build the country name mappings
    worldMapRegistered = true;
  } catch (error) {
    console.warn("Failed to load bundled world map:", error);
  }
}

// Load the map data
loadCleanWorldMap();

// Build lookups: ISO3 -> English name, numeric id -> English name, and a set of valid names
// This will be populated once the map data loads
let __NAME_BY = { byIso3: new Map(), byNumeric: new Map(), nameSet: new Set() };

function buildNameMappings(geoData) {
  const byIso3 = new Map();
  const byNumeric = new Map();
  const nameSet = new Set();
  
  // Manual mapping of numeric ISO3 codes to country names used in the GeoJSON
  // This GeoJSON source only has 'name' property, no ISO codes
  const numericToName = {
    '4': 'Afghanistan', '8': 'Albania', '12': 'Algeria', '16': 'American Samoa', '20': 'Andorra', '24': 'Angola',
    '28': 'Antigua and Barbuda', '31': 'Azerbaijan', '32': 'Argentina', '36': 'Australia', '40': 'Austria', '44': 'Bahamas',
    '48': 'Bahrain', '50': 'Bangladesh', '51': 'Armenia', '52': 'Barbados', '56': 'Belgium', '60': 'Bermuda',
    '64': 'Bhutan', '68': 'Bolivia', '70': 'Bosnia and Herzegovina', '72': 'Botswana', '76': 'Brazil', '84': 'Belize',
    '90': 'Solomon Islands', '96': 'Brunei', '100': 'Bulgaria', '104': 'Myanmar', '108': 'Burundi', '112': 'Belarus',
    '116': 'Cambodia', '120': 'Cameroon', '124': 'Canada', '132': 'Cape Verde', '136': 'Cayman Islands', '140': 'Central African Republic',
    '144': 'Sri Lanka', '148': 'Chad', '152': 'Chile', '156': 'China', '170': 'Colombia', '174': 'Comoros',
    '178': 'Republic of the Congo', '180': 'Democratic Republic of the Congo', '184': 'Cook Islands', '188': 'Costa Rica', '191': 'Croatia', '192': 'Cuba',
    '196': 'Cyprus', '203': 'Czech Republic', '208': 'Denmark', '214': 'Dominican Republic', '218': 'Ecuador', '222': 'El Salvador',
    '226': 'Equatorial Guinea', '231': 'Ethiopia', '232': 'Eritrea', '233': 'Estonia', '238': 'Falkland Islands', '242': 'Fiji',
    '246': 'Finland', '250': 'France', '254': 'French Guiana', '258': 'French Polynesia', '260': 'French Southern and Antarctic Lands',
    '262': 'Djibouti', '266': 'Gabon', '268': 'Georgia', '270': 'Gambia', '275': 'Palestinian Territory', '276': 'Germany',
    '288': 'Ghana', '292': 'Gibraltar', '296': 'Kiribati', '300': 'Greece', '304': 'Greenland', '308': 'Grenada',
    '312': 'Guadeloupe', '316': 'Guam', '320': 'Guatemala', '324': 'Guinea', '328': 'Guyana', '332': 'Haiti',
    '336': 'Vatican', '340': 'Honduras', '344': 'Hong Kong S.A.R.', '348': 'Hungary', '352': 'Iceland', '356': 'India',
    '360': 'Indonesia', '364': 'Iran', '368': 'Iraq', '372': 'Ireland', '376': 'Israel', '380': 'Italy',
    '384': "Côte d'Ivoire", '388': 'Jamaica', '392': 'Japan', '398': 'Kazakhstan', '400': 'Jordan', '404': 'Kenya',
    '408': 'North Korea', '410': 'South Korea', '414': 'Kuwait', '417': 'Kyrgyzstan', '418': 'Laos', '422': 'Lebanon',
    '426': 'Lesotho', '428': 'Latvia', '430': 'Liberia', '434': 'Libya', '438': 'Liechtenstein', '440': 'Lithuania',
    '442': 'Luxembourg', '446': 'Macao S.A.R', '450': 'Madagascar', '454': 'Malawi', '458': 'Malaysia', '462': 'Maldives',
    '466': 'Mali', '470': 'Malta', '474': 'Martinique', '478': 'Mauritania', '480': 'Mauritius', '484': 'Mexico',
    '492': 'Monaco', '496': 'Mongolia', '498': 'Moldova', '499': 'Montenegro', '500': 'Montserrat', '504': 'Morocco',
    '508': 'Mozambique', '512': 'Oman', '516': 'Namibia', '520': 'Nauru', '524': 'Nepal', '528': 'Netherlands',
    '540': 'New Caledonia', '548': 'Vanuatu', '554': 'New Zealand', '558': 'Nicaragua', '562': 'Niger', '566': 'Nigeria',
    '570': 'Niue', '574': 'Norfolk Island', '578': 'Norway', '580': 'Northern Mariana Islands', '583': 'Micronesia', '584': 'Marshall Islands',
    '585': 'Palau', '586': 'Pakistan', '591': 'Panama', '598': 'Papua New Guinea', '600': 'Paraguay', '604': 'Peru',
    '608': 'Philippines', '612': 'Pitcairn Islands', '616': 'Poland', '620': 'Portugal', '624': 'Guinea-Bissau', '626': 'East Timor',
    '630': 'Puerto Rico', '634': 'Qatar', '638': 'Réunion', '642': 'Romania', '643': 'Russia', '646': 'Rwanda',
    '654': 'Saint Helena', '659': 'Saint Kitts and Nevis', '660': 'Anguilla', '662': 'Saint Lucia', '666': 'Saint Pierre and Miquelon',
    '670': 'Saint Vincent and the Grenadines', '674': 'San Marino', '678': 'São Tomé and Príncipe', '682': 'Saudi Arabia', '686': 'Senegal',
    '688': 'Serbia', '690': 'Seychelles', '694': 'Sierra Leone', '702': 'Singapore', '703': 'Slovakia', '704': 'Vietnam',
    '705': 'Slovenia', '706': 'Somalia', '710': 'South Africa', '716': 'Zimbabwe', '724': 'Spain', '732': 'Western Sahara',
    '740': 'Suriname', '748': 'Swaziland', '752': 'Sweden', '756': 'Switzerland', '760': 'Syria', '762': 'Tajikistan',
    '764': 'Thailand', '768': 'Togo', '772': 'Tokelau', '776': 'Tonga', '780': 'Trinidad and Tobago', '784': 'United Arab Emirates',
    '788': 'Tunisia', '792': 'Turkey', '795': 'Turkmenistan', '796': 'Turks and Caicos Islands', '798': 'Tuvalu', '800': 'Uganda',
    '804': 'Ukraine', '807': 'Macedonia', '818': 'Egypt', '826': 'United Kingdom', '834': 'Tanzania', '840': 'United States of America',
    '842': 'United States of America', '850': 'United States Virgin Islands', '854': 'Burkina Faso', '858': 'Uruguay', '860': 'Uzbekistan',
    '862': 'Venezuela', '876': 'Wallis and Futuna', '882': 'Samoa', '887': 'Yemen', '894': 'Zambia'
  };
  
  try {
    const features = geoData.features || [];
    for (const f of features) {
      const props = f?.properties || {};
      const nm = props?.name || "";
      if (!nm) continue;
      nameSet.add(nm);
    }

    // Add numeric mappings
    for (const [numericCode, countryName] of Object.entries(numericToName)) {
      if (nameSet.has(countryName)) {
        byNumeric.set(numericCode, countryName);
      }
    }

    // ISO3 mappings — the path the API data (iso3 + Czech display name)
    // actually resolves through.
    for (const [iso3, countryName] of Object.entries(ISO3_TO_GEOJSON_NAME)) {
      if (nameSet.has(countryName)) {
        byIso3.set(iso3, countryName);
      }
    }

  } catch (_) {}

  __NAME_BY = { byIso3, byNumeric, nameSet };
  return __NAME_BY;
}

// ISO3 → region name AS SPELLED IN ui/public/world.json. Generated from the
// curated numeric table via pycountry + manual fixes for this geojson's
// non-standard names (USA, England, Republic of Serbia, Ivory Coast, ...).
// Module scope so the render path (selected/peer highlights) can resolve
// region names even for countries absent from the current data rows.
const ISO3_TO_GEOJSON_NAME = {
    AFG: "Afghanistan", AGO: "Angola", ALB: "Albania", ARE: "United Arab Emirates",
    ARG: "Argentina", ARM: "Armenia", ATF: "French Southern and Antarctic Lands", AUS: "Australia",
    AUT: "Austria", AZE: "Azerbaijan", BDI: "Burundi", BEL: "Belgium",
    BEN: "Benin", BFA: "Burkina Faso", BGD: "Bangladesh", BGR: "Bulgaria",
    BHS: "The Bahamas", BIH: "Bosnia and Herzegovina", BLR: "Belarus", BLZ: "Belize",
    BOL: "Bolivia", BRA: "Brazil", BRN: "Brunei", BTN: "Bhutan",
    BWA: "Botswana", CAF: "Central African Republic", CAN: "Canada", CHE: "Switzerland",
    CHL: "Chile", CHN: "China", CIV: "Ivory Coast", CMR: "Cameroon",
    COD: "Democratic Republic of the Congo", COG: "Republic of the Congo", COL: "Colombia", CRI: "Costa Rica",
    CUB: "Cuba", CYP: "Cyprus", CZE: "Czech Republic", DEU: "Germany",
    DJI: "Djibouti", DNK: "Denmark", DOM: "Dominican Republic", DZA: "Algeria",
    ECU: "Ecuador", EGY: "Egypt", ERI: "Eritrea", ESH: "Western Sahara",
    ESP: "Spain", EST: "Estonia", ETH: "Ethiopia", FIN: "Finland",
    FJI: "Fiji", FLK: "Falkland Islands", FRA: "France", GAB: "Gabon",
    GBR: "England", GEO: "Georgia", GHA: "Ghana", GIN: "Guinea",
    GMB: "Gambia", GNB: "Guinea Bissau", GNQ: "Equatorial Guinea", GRC: "Greece",
    GRL: "Greenland", GTM: "Guatemala", GUY: "Guyana", HND: "Honduras",
    HRV: "Croatia", HTI: "Haiti", HUN: "Hungary", IDN: "Indonesia",
    IND: "India", IRL: "Ireland", IRN: "Iran", IRQ: "Iraq",
    ISL: "Iceland", ISR: "Israel", ITA: "Italy", JAM: "Jamaica",
    JOR: "Jordan", JPN: "Japan", KAZ: "Kazakhstan", KEN: "Kenya",
    KGZ: "Kyrgyzstan", KHM: "Cambodia", KOR: "South Korea", KWT: "Kuwait",
    LAO: "Laos", LBN: "Lebanon", LBR: "Liberia", LBY: "Libya",
    LKA: "Sri Lanka", LSO: "Lesotho", LTU: "Lithuania", LUX: "Luxembourg",
    LVA: "Latvia", MAR: "Morocco", MDA: "Moldova", MDG: "Madagascar",
    MEX: "Mexico", MKD: "Macedonia", MLI: "Mali", MMR: "Myanmar",
    MNE: "Montenegro", MNG: "Mongolia", MOZ: "Mozambique", MRT: "Mauritania",
    MWI: "Malawi", MYS: "Malaysia", NAM: "Namibia", NCL: "New Caledonia",
    NER: "Niger", NGA: "Nigeria", NIC: "Nicaragua", NLD: "Netherlands",
    NOR: "Norway", NPL: "Nepal", NZL: "New Zealand", OMN: "Oman",
    PAK: "Pakistan", PAN: "Panama", PER: "Peru", PHL: "Philippines",
    PNG: "Papua New Guinea", POL: "Poland", PRI: "Puerto Rico", PRK: "North Korea",
    PRT: "Portugal", PRY: "Paraguay", PSE: "West Bank", QAT: "Qatar",
    ROU: "Romania", RUS: "Russia", RWA: "Rwanda", SAU: "Saudi Arabia",
    SDN: "Sudan", SEN: "Senegal", SLB: "Solomon Islands", SLE: "Sierra Leone",
    SLV: "El Salvador", SOM: "Somalia", SRB: "Republic of Serbia", SSD: "South Sudan",
    SUR: "Suriname", SVK: "Slovakia", SVN: "Slovenia", SWE: "Sweden",
    SWZ: "Swaziland", SYR: "Syria", TCD: "Chad", TGO: "Togo",
    THA: "Thailand", TJK: "Tajikistan", TKM: "Turkmenistan", TLS: "East Timor",
    TTO: "Trinidad and Tobago", TUN: "Tunisia", TUR: "Turkey", TWN: "Taiwan",
    TZA: "United Republic of Tanzania", UGA: "Uganda", UKR: "Ukraine", URY: "Uruguay",
    USA: "USA", UZB: "Uzbekistan", VEN: "Venezuela", VNM: "Vietnam",
    VUT: "Vanuatu", YEM: "Yemen", ZAF: "South Africa", ZMB: "Zambia",
    ZWE: "Zimbabwe",
};

// Region name for an iso3 — prefers the geojson-validated map (populated once
// world.json loads), falls back to the static table above.
function regionNameForIso3(iso3) {
  if (!iso3) return null;
  return __NAME_BY.byIso3.get(iso3) || ISO3_TO_GEOJSON_NAME[iso3] || null;
}

export default function WorldMap({ data = [], metric = "value", nameMap = null, czechNames = null, nameField = 'name', meta = {}, onCountryClick = null, selectedIso3 = null, peerIso3 = [] }) {
  function formatHs6Dot(code) {
    const raw = String(code ?? '').trim();
    const digits = raw.replace(/\D/g, '');
    if (!digits) return '';
    const s = digits.padStart(6, '0');
    if (/^0{6}$/.test(s)) return '';
    return `${s.slice(0,4)}.${s.slice(4)}`;
  }

  function buildTitle(metric, meta) {
    const y = Number(meta?.year) || null;
    const hs = formatHs6Dot(meta?.hs6);
    if (metric === 'cz_share_in_partner_import') {
      return `Český podíl na importu HS6 ${hs || '—'}${y ? `, ${y}` : ''}, v %`;
    }
    if (metric === 'delta_export_abs') {
      const y0 = y ? (y - 1) : null;
      return `Růst českého exportu HS6 ${hs || '—'}${y ? `, ${y0}–${y}` : ''}, v USD`;
    }
    if (metric === 'partner_share_in_cz_exports') {
      return `Podíl partnera na českém exportu HS6 ${hs || '—'}${y ? `, ${y}` : ''}, v %`;
    }
    if (metric === 'export_value_usd') {
      return `Celková hodnota českého exportu HS6 ${hs || '—'}${y ? `, ${y}` : ''}, v USD`;
    }
    if (metric === 'import_value_usd') {
      return `Celkový import HS6 ${hs || '—'} do země${y ? `, ${y}` : ''}, v USD`;
    }
    return `World — ${metric}`;
  }

  // Defensive: normalize data to an array of {name, value:number} using robust resolution.
  // Memoized — a fresh array identity per render cascaded into a fresh option
  // object, forcing ECharts to redraw (and re-animate) on every parent render.
  const safeData = useMemo(() => Array.isArray(data)
    ? data.map((item) => {
        const rawField = item?.[nameField];
        const iso3Field = item?.iso3 != null ? String(item.iso3) : null; // may be 'DEU' or '276'
        let candidate = rawField ?? item?.name ?? iso3Field ?? "";
        let resolved = candidate;
        // 1) explicit mapping
        if (nameMap && candidate && Object.prototype.hasOwnProperty.call(nameMap, candidate)) {
          resolved = nameMap[candidate];
        } else {
          // 2) already an English name present in the map
          if (!__NAME_BY.nameSet.has(resolved)) {
            // 3) ISO3 code
            const iso3 = (iso3Field || candidate || "").toUpperCase();
            if (/^[A-Z]{3}$/.test(iso3) && __NAME_BY.byIso3.has(iso3)) {
              resolved = __NAME_BY.byIso3.get(iso3);
            } else {
              // 4) numeric id (M49) → English name
              const numKey = String(iso3Field || candidate || "");
              if (/^\d+$/.test(numKey) && __NAME_BY.byNumeric.has(numKey)) {
                resolved = __NAME_BY.byNumeric.get(numKey);
              }
            }
          }
        }
        const num = Number(item?.value);
        const valueNum = Number.isFinite(num) ? num : null; // keep nulls → map leaves region uncolored
        const iso3 = (iso3Field || candidate || "").toUpperCase();
        const iso3Code = /^[A-Z]{3}$/.test(iso3) ? iso3 : null;
        return { name: String(resolved || ''), value: valueNum, iso3: iso3Code };
      })
    : [], [data, nameMap, nameField]);

  // English region name → Czech name, so tooltips read in Czech on the Czech UI.
  const nameToCzech = useMemo(() => {
    const m = new Map();
    // From current data rows (uses the same resolution as the series → covers e.g. "USA").
    safeData.forEach((d) => {
      if (d.name && d.iso3 && czechNames && czechNames[d.iso3]) m.set(d.name, czechNames[d.iso3]);
    });
    // Fallback for every country via nameMap (iso3→English) + czechNames (iso3→Czech).
    if (nameMap && czechNames) {
      Object.entries(nameMap).forEach(([iso3, eng]) => {
        if (!m.has(eng) && czechNames[iso3]) m.set(eng, czechNames[iso3]);
      });
    }
    return m;
  }, [safeData, nameMap, czechNames]);

  // Map option: choropleth over the registered "world" map
  const option = useMemo(() => {
    const selectedRegion = regionNameForIso3(selectedIso3);
    const peerRegions = new Set(
      (Array.isArray(peerIso3) ? peerIso3 : [])
        .map(regionNameForIso3)
        .filter(Boolean)
    );
    const highlightStyle = (regionName) => {
      if (selectedRegion && regionName === selectedRegion) {
        return { borderColor: "#111827", borderWidth: 2 };
      }
      if (peerRegions.has(regionName)) {
        return { borderColor: "#7c3aed", borderWidth: 1.5 };
      }
      return null;
    };

    const seriesData = safeData.map((d) => {
      const hl = highlightStyle(d.name);
      return hl ? { name: d.name, value: d.value, itemStyle: hl } : { name: d.name, value: d.value };
    });
    // Selected/peer countries absent from the data rows still deserve their
    // outline (value stays null → region keeps the no-data fill).
    const present = new Set(seriesData.map((d) => d.name));
    [selectedRegion, ...peerRegions].forEach((regionName) => {
      if (regionName && !present.has(regionName)) {
        seriesData.push({ name: regionName, value: null, itemStyle: highlightStyle(regionName) });
      }
    });

    // Metric semantics
    const isShare =
      metric === "cz_share_in_partner_import" ||
      metric === "partner_share_in_cz_exports";
    const values = safeData
      .map(d => (Number.isFinite(Number(d.value)) ? Number(d.value) : null))
      .filter(v => v !== null);

    // Robust scale ceiling: 95th percentile of POSITIVE values, so a single
    // outlier (e.g. a 99.9% share micro-market) cannot wash out the rest of
    // the map. Values above the ceiling clamp to the top color.
    const positives = values.filter((v) => v > 0).sort((a, b) => a - b);
    const p95 = positives.length
      ? positives[Math.min(positives.length - 1, Math.floor(0.95 * (positives.length - 1)))]
      : 0;

    // Scale & colors
    let vmin, vmax, colors, tooltipFmt, legendFmt;
    if (isShare) {
      vmin = 0;
      vmax = Math.max(p95, 0.01); // API returns shares as decimals (0.5029 = 50.29%)
      colors = ["#fef3c7", "#f59e0b", "#92400e"];  // warm yellow to brown gradient
      tooltipFmt = (v) => {
        if (v == null) return 'n/a';
        const percentage = v * 100;
        // For very small shares, show 3 decimal places for better precision
        if (percentage < 0.1) {
          return `${percentage.toFixed(3)}%`;
        }
        return `${percentage.toFixed(1)}%`;
      }; // Multiply by 100 for display with better precision for small values
      legendFmt = (v) => `${(v * 100).toLocaleString("cs-CZ", { maximumFractionDigits: 1 })} %`;
    } else {
      const minV = values.length ? Math.min(...values) : 0;
      const usdCompact = (v) => {
        const a = Math.abs(v);
        if (a >= 1e9) return `${(v / 1e9).toLocaleString("cs-CZ", { maximumFractionDigits: 1 })} mld.`;
        if (a >= 1e6) return `${(v / 1e6).toLocaleString("cs-CZ", { maximumFractionDigits: 0 })} mil.`;
        return Math.round(v).toLocaleString("cs-CZ");
      };
      if (minV < 0) {
        // Diverging scale only when the metric can actually be negative
        // (e.g. a YoY delta): red → light → green centered on 0.
        const maxAbs = Math.max(Math.abs(minV), Math.abs(values.length ? Math.max(...values) : 0), 1e-9);
        vmin = -maxAbs;
        vmax = maxAbs;
        colors = ["#dc2626", "#fef2f2", "#16a34a"];
      } else {
        // Export values are never negative. The old diverging scale put the
        // many zero-export countries at its midpoint (near-white) and wasted
        // half the range, so the map looked empty even with real data.
        vmin = 0;
        vmax = Math.max(p95, 1e-9);
        colors = metric === "import_value_usd"
          ? ["#eff6ff", "#60a5fa", "#1d4ed8"]  // market size: blue, distinct from CZ-export green
          : ["#f0fdf4", "#4ade80", "#15803d"]; // light → rich green
      }
      const nf = new Intl.NumberFormat("cs-CZ", { maximumFractionDigits: 0 });
      // Values are already in USD, no scaling needed
      tooltipFmt = (v) => v == null ? 'n/a' : `${nf.format(v)} USD`;
      legendFmt = (v) => usdCompact(v);
    }

    return {
      tooltip: {
        trigger: "item",
        backgroundColor: "rgba(50,50,50,0.9)",
        borderColor: "#777",
        borderWidth: 1,
        textStyle: { color: "#fff" },
        formatter: (p) => {
          const label = nameToCzech.get(p.name) || p.name;
          return `<b>${label}</b><br/>${tooltipFmt(Number.isFinite(Number(p.value)) ? Number(p.value) : null)}`;
        },
      },
      visualMap: {
        show: true, // legend: without a scale the choropleth can't be read
        type: "continuous",
        min: vmin,
        max: vmax,
        calculable: false,
        orient: "horizontal",
        left: 10,
        bottom: 0,
        itemWidth: 12,
        itemHeight: 110,
        // text order for horizontal continuous visualMap: [max, min]
        text: [`${legendFmt(vmax)}+`, legendFmt(vmin)],
        textStyle: { fontSize: 11, color: "#666" },
        inRange: {
          color: colors
        },
        // values above the p95 ceiling clamp to the top color instead of the
        // default out-of-range gray
        outOfRange: {
          color: colors[colors.length - 1]
        }
      },
      series: [
        {
          type: "map",
          map: "world",
          roam: true,
          scaleLimit: {
            min: 0.7,
            max: 8
          },
          zoom: 1.2,
          left: 10,
          right: 10,
          top: 10,
          bottom: 50,
          aspectScale: 0.85, // Slightly compress vertically
          emphasis: {
            label: { show: false },
            itemStyle: {
              areaColor: "#e5e7eb",
              borderColor: "#374151",
              borderWidth: 2,
              shadowBlur: 5,
              shadowColor: "rgba(0,0,0,0.3)"
            }
          },
          select: {
            itemStyle: {
              areaColor: "#3b82f6",
              borderColor: "#1d4ed8",
              borderWidth: 2
            }
          },
          itemStyle: {
            borderColor: "#d1d5db",
            borderWidth: 0.8,
            areaColor: "#f9fafb"  // light gray for countries with no data
          },
          data: seriesData,
        },
      ],
    };
  }, [safeData, metric, nameToCzech, selectedIso3, peerIso3]);



  const title = buildTitle(metric, meta);

  // Create reverse mapping from country names back to ISO3 codes
  const nameToIso3 = useMemo(() => {
    const mapping = new Map();
    
    // Add data mappings (from current data)
    safeData.forEach(item => {
      if (item.name && data && Array.isArray(data)) {
        const originalItem = data.find(d => d && (d.name === item.name || d.iso3 === item.name));
        if (originalItem?.iso3) {
          mapping.set(item.name, originalItem.iso3);
        }
      }
    });
    
    // Add built-in mappings 
    if (nameMap) {
      Object.entries(nameMap).forEach(([iso3, name]) => {
        mapping.set(name, iso3);
      });
    }
    
    // Add mappings from world map data
    __NAME_BY.byIso3.forEach((name, iso3) => {
      mapping.set(name, iso3);
    });
    
    return mapping;
  }, [safeData, data, nameMap]);

  // ECharts event handlers. echarts-for-react dispose()s and rebuilds the whole
  // chart whenever onEvents fails its deep-equal check, and functions only
  // compare by reference — so the object must keep ONE identity for the chart's
  // lifetime. nameToIso3/onCountryClick change with data, so the stable handler
  // reads them through a ref instead of closing over them ("latest ref").
  const clickCtxRef = useRef({ onCountryClick, nameToIso3 });
  useEffect(() => {
    clickCtxRef.current = { onCountryClick, nameToIso3 };
  });
  const onEvents = useMemo(() => ({
    'click': (params) => {
      const { onCountryClick: cb, nameToIso3: lookup } = clickCtxRef.current;
      if (cb && params.componentType === 'series' && params.seriesType === 'map') {
        const countryName = params.name;
        const iso3 = lookup.get(countryName);

        if (iso3) {
          cb(iso3, countryName);
        }
      }
    }
  }), []);

  return (
    <div data-testid="worldmap" style={{ border: "1px solid #eee", borderRadius: 6, padding: 12, background: "#fff" }}>
      {/* Green title at top */}
      <div style={{ 
        fontFamily: "Montserrat",
        fontWeight: "bold", 
        fontSize: 16, 
        color: "#008C00",
        marginBottom: 8,
        paddingLeft: 4
      }}>
        {title}
      </div>
      
      {safeData.length === 0 ? (
        <div style={{ height: "400px", display: "flex", alignItems: "center", justifyContent: "center", color: "#666" }}>
          Vyberte signál pro zobrazení detailů
        </div>
      ) : (
        <div>
          <ReactEChartsCore
            echarts={echarts}
            data-testid="echart"
            option={option}
            style={{ height: "400px", width: "100%" }}
            onEvents={onEvents}
          />
        </div>
      )}
    </div>
  );
}