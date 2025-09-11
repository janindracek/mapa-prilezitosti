import React, { useMemo } from "react";
import ReactECharts from "echarts-for-react";
import * as echarts from "echarts";

// Use Natural Earth data which has better antimeridian handling
// This is a cleaner GeoJSON source without the geometry issues
let worldMapRegistered = false;

async function loadCleanWorldMap() {
  if (worldMapRegistered) return;
  
  try {
    // Use alternative GeoJSON source that renders correctly
    const response = await fetch('https://raw.githubusercontent.com/holtzy/D3-graph-gallery/master/DATA/world.geojson');
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
    console.log('Clean world map registered with alternative GeoJSON');
  } catch (error) {
    console.warn('Failed to load clean world map:', error);
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
    
  } catch (_) {}
  
  __NAME_BY = { byIso3, byNumeric, nameSet };
  console.log('[WorldMap] Built mappings - numeric entries:', byNumeric.size, 'known names:', nameSet.size);
  return __NAME_BY;
}

export default function WorldMap({ data = [], metric = "value", nameMap = null, nameField = 'name', meta = {}, onCountryClick = null }) {
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
    return `World — ${metric}`;
  }

  // Debug: treat these metrics as shares - but API already returns percentages (0.5029 = 50.29%)
  const isShareMetric =
    metric === "cz_share_in_partner_import" ||
    metric === "partner_share_in_cz_exports";

  // Defensive: normalize data to an array of {name, value:number} using robust resolution
  const safeData = Array.isArray(data)
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
        return { name: String(resolved || ''), value: valueNum };
      })
    : [];

  if (process.env.NODE_ENV !== 'production') {
    const known = safeData.filter(d => __NAME_BY.nameSet.has(d.name)).length;
    const unknown = safeData.filter(d => !__NAME_BY.nameSet.has(d.name));
    console.debug('[WorldMap] rows:', safeData.length, 'mapped-to-known-names:', known);
    console.debug('[WorldMap] metric:', metric, 'isShareMetric:', isShareMetric);
    if (unknown.length) {
      console.warn('[WorldMap] Unknown region names (first 5):', unknown.slice(0, 5));
      // Extra debug for numeric-ID resolution
      try {
        const numericKeysSample = Array.from(__NAME_BY.byNumeric.keys()).slice(0, 10);
        console.debug('[WorldMap] byNumeric size:', __NAME_BY.byNumeric.size, 'sample keys:', numericKeysSample);
        unknown.slice(0, 5).forEach((u) => {
          const k = String(u.name);
          console.debug('[WorldMap] numeric lookup for', k, 'exists?', __NAME_BY.byNumeric.has(k), '→', __NAME_BY.byNumeric.get(k));
        });
      } catch (_) {}
    }
    // Log a small sample of the data coming into the map
    if (safeData.length) {
      console.debug('[WorldMap] sample:', safeData.slice(0, 3));
      console.debug('[WorldMap] raw sample:', Array.isArray(data) ? data.slice(0, 3) : data);
    }
    // Debug value ranges for all metrics
    const values = safeData
      .map(d => (Number.isFinite(Number(d.value)) ? Number(d.value) : null))
      .filter(v => v != null);
    if (values.length) {
      const minVal = Math.min(...values);
      const maxVal = Math.max(...values);
      if (isShareMetric) {
        console.debug(`[WorldMap] Share metric range: ${minVal.toFixed(4)} to ${maxVal.toFixed(4)} (API returns percentages as decimals)`);
      } else {
        console.debug(`[WorldMap] Non-share metric range: ${minVal.toFixed(2)} to ${maxVal.toFixed(2)} (absolute values)`);
        if (maxVal > 100) {
          console.warn(`[WorldMap] Large values detected - ensure not applying percentage formatting to non-share metric`);
        }
      }
    }
  }


  // Map option: choropleth over the registered "world" map
  const option = useMemo(() => {
    const seriesData = safeData.map((d) => ({ name: d.name, value: d.value }));

    // Metric semantics
    const isShare =
      metric === "cz_share_in_partner_import" ||
      metric === "partner_share_in_cz_exports";
    const values = seriesData
      .map(d => (Number.isFinite(Number(d.value)) ? Number(d.value) : null))
      .filter(v => v !== null);

    // Scale & colors
    let vmin, vmax, colors, tooltipFmt;
    if (isShare) {
      const rawMax = values.length ? Math.max(...values) : 0;
      vmin = 0;
      vmax = Math.max(rawMax, 0.01); // API returns percentages as decimals (0.5029 = 50.29%)
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
    } else {
      const minV = values.length ? Math.min(...values) : 0;
      const maxV = values.length ? Math.max(...values) : 0;
      const maxAbs = values.length ? Math.max(Math.abs(minV), Math.abs(maxV)) : 1;
      vmin = -Math.max(maxAbs, 1e-9);
      vmax =  Math.max(maxAbs, 1e-9);
      colors = ["#dc2626", "#fef2f2", "#16a34a"]; // red → light → green (intuitive: negative/positive)
      const nf = new Intl.NumberFormat("cs-CZ", { maximumFractionDigits: 0 });
      
      if (metric === 'export_value_usd') {
        // export_value_usd: API returns values already in USD, no additional scaling needed
        tooltipFmt = (v) => v == null ? 'n/a' : `${nf.format(v)} USD`;
      } else {
        // For other metrics: values are already in USD, no scaling needed
        tooltipFmt = (v) => v == null ? 'n/a' : `${nf.format(v)} USD`;
      }
    }

    return {
      tooltip: {
        trigger: "item",
        backgroundColor: "rgba(50,50,50,0.9)",
        borderColor: "#777",
        borderWidth: 1,
        textStyle: { color: "#fff" },
        formatter: (p) => `<b>${p.name}</b><br/>${tooltipFmt(Number.isFinite(Number(p.value)) ? Number(p.value) : null)}`,
      },
      visualMap: {
        show: false, // Hide the color slider
        min: vmin,
        max: vmax,
        calculable: false,
        inRange: {
          color: colors
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
          projection: {
            type: 'mercator',
            center: [20, 30], // Center on Europe/Middle East
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
  }, [safeData, metric, meta]);



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

  // ECharts event handlers
  const onEvents = onCountryClick ? {
    'click': (params) => {
      if (params.componentType === 'series' && params.seriesType === 'map') {
        const countryName = params.name;
        const iso3 = nameToIso3.get(countryName);
        
        if (iso3) {
          console.log('[WorldMap] Country clicked:', countryName, '→', iso3);
          onCountryClick(iso3, countryName);
        } else {
          console.warn('[WorldMap] Could not find ISO3 code for country:', countryName);
        }
      }
    }
  } : undefined;

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
          <ReactECharts 
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