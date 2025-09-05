import React from "react";

const collatorCs = new Intl.Collator('cs', { sensitivity: 'base', usage: 'sort' });

const CONTINENT_CZ_MAP = {
  'Europe': { cz: 'Evropa', order: 1 },
  'Asia': { cz: 'Asie', order: 2 },
  'North America': { cz: 'Severní Amerika', order: 3 },
  'South America': { cz: 'Jižní Amerika', order: 4 },
  'Africa': { cz: 'Afrika', order: 5 },
  'Oceania': { cz: 'Oceánie', order: 6 },
  'Antarctica': { cz: 'Antarktida', order: 7 },
};

function continentToCz(continent) {
  const key = (continent || '').trim();
  return CONTINENT_CZ_MAP[key] || { cz: key || 'Ostatní', order: 99 };
}

export default function Controls({
  countries = [],
  country,
  year,
  onChange,
  savedHS6Codes = [],
  selectedHS6 = null,
  onHS6Change,
  referenceData = { countryNames: {}, hs6Labels: {}, continents: {}, loading: false },
}) {
  const [fallbackCountries, setFallbackCountries] = React.useState([]);
  React.useEffect(() => {
    if (!countries || countries.length === 0) {
      fetch('/ref/countries.json')
        .then((r) => (r.ok ? r.json() : []))
        .then((data) => {
          if (Array.isArray(data)) setFallbackCountries(data);
        })
        .catch(() => {});
    }
  }, [countries]);

  // Use centralized reference data instead of loading independently
  const namesMap = referenceData.countryNames;
  const continentsMap = referenceData.continents;
  const hs6Labels = referenceData.hs6Labels;

  const [hs6Input, setHs6Input] = React.useState('');
  const [hs6Error, setHs6Error] = React.useState('');

  // Normalize any array values to {value,label,continentCz,continentOrder}
  const toOptions = (arr) => {
    if (!Array.isArray(arr)) return [];
    return arr
      .filter((item) => {
        // Filter out Czech Republic (203) - this tool is for Czech administration to analyze other countries
        const value = item && typeof item === 'object' ? 
          (item.value || item.code || '') : String(item);
        return String(value) !== '203' && String(value).toUpperCase() !== 'CZE';
      })
      .map((item) => {
      if (item && typeof item === 'object') {
        // Preferred shapes: {code, name, continent} or {value,label,continent}
        let value, label, continent;
        if ('value' in item || 'label' in item) {
          value = String(item.value ?? item.code ?? '');
          label = String(item.label ?? item.name ?? value);
          continent = item.continent || item.region || '';
        } else if ('code' in item || 'name' in item) {
          value = String(item.code ?? '');
          label = String(item.name ?? value);
          continent = item.continent || item.region || '';
        } else {
          const keys = Object.keys(item);
          const v = item[keys[0]];
          const l = item[keys[1]] ?? v;
          value = String(v);
          label = String(l);
          continent = item.continent || item.region || '';
        }
        if (!continent && continentsMap) {
          const codeGuess = String(value || label || '').toUpperCase();
          if (continentsMap[codeGuess]) {
            continent = continentsMap[codeGuess];
          }
        }
        // Optional ISO3->CZ name mapping
        let displayLabel = label;
        if (
          displayLabel &&
          displayLabel.toUpperCase() === displayLabel &&
          /^[A-Z]{3}$/.test(displayLabel) &&
          namesMap && namesMap[displayLabel]
        ) {
          displayLabel = namesMap[displayLabel];
        }
        const { cz, order } = continentToCz(continent);
        return { value, label: displayLabel, continentCz: cz, continentOrder: order };
      } else {
        const v = String(item);
        const up = v.toUpperCase();
        let lbl = v;
        if (/^[A-Z]{3}$/.test(up) && namesMap && namesMap[up]) {
          lbl = namesMap[up];
        }
        const cont = (continentsMap && continentsMap[up]) || '';
        const { cz, order } = continentToCz(cont);
        return { value: v, label: lbl, continentCz: cz, continentOrder: order };
      }
    });
  };

  const effectiveCountries = (countries && countries.length) ? countries : fallbackCountries;
  const countryOpts = toOptions(effectiveCountries);

  // Group by continent and sort by Czech locale
  const groupsMap = new Map();
  for (const o of countryOpts) {
    const key = `${o.continentOrder}__${o.continentCz}`;
    if (!groupsMap.has(key)) groupsMap.set(key, []);
    groupsMap.get(key).push(o);
  }
  const grouped = Array.from(groupsMap.entries())
    .sort((a, b) => {
      const [oa] = a[0].split('__');
      const [ob] = b[0].split('__');
      return Number(oa) - Number(ob);
    })
    .map(([key, arr]) => {
      const [, cz] = key.split('__');
      // Sort options by Czech name
      arr.sort((x, y) => collatorCs.compare(x.label, y.label));
      return { continentCz: cz, options: arr };
    });

  const handle = (patch) => {
    if (typeof onChange === "function") {
      onChange({
        country,
        year,
        ...patch,
      });
    }
  };

  const countryValue = country != null ? String(country) : "";
  const yearValue = year != null ? String(year) : "";

  // HS6 validation and handling
  function validateHS6(input) {
    const cleaned = String(input || '').replace(/\D/g, '');
    if (!cleaned) return { isValid: false, error: '' };
    if (cleaned.length !== 6) return { isValid: false, error: 'Kód musí mít 6 číslic' };
    
    if (hs6Labels && !hs6Labels[cleaned]) {
      return { isValid: false, error: 'Kód neplatný' };
    }
    
    return { isValid: true, error: '' };
  }

  function handleHS6Input(value) {
    setHs6Input(value);
    const { isValid, error } = validateHS6(value);
    setHs6Error(error);
  }

  function handleHS6Add() {
    const cleaned = hs6Input.replace(/\D/g, '');
    const { isValid } = validateHS6(cleaned);
    
    if (!isValid || !onHS6Change) return;
    
    const label = hs6Labels && hs6Labels[cleaned] ? hs6Labels[cleaned] : `HS6 ${cleaned}`;
    onHS6Change('add', { code: cleaned, label });
    setHs6Input('');
    setHs6Error('');
  }

  function handleHS6Select(hs6Code) {
    if (onHS6Change) {
      onHS6Change('select', hs6Code);
    }
  }

  function handleHS6Delete(hs6Code) {
    if (onHS6Change) {
      onHS6Change('delete', hs6Code);
    }
  }

  return (
    <div
      style={{
        display: "grid",
        gap: 12,
        padding: 12,
        border: "1px solid #eee",
        borderRadius: 6,
        background: "#fff",
      }}
    >
      <label htmlFor="country-select" style={{ fontFamily: "Montserrat", fontWeight: "bold", fontSize: 18, color: "#008C00" }}>Země</label>
      <select
        id="country-select"
        data-testid="country-select"
        aria-label="Country selector"
        value={countryValue}
        onChange={(e) => handle({ country: e.target.value })}
      >
        <option value="" disabled>
          — Vyberte zemi —
        </option>
        {grouped.map((g) => (
          <optgroup key={g.continentCz} label={g.continentCz}>
            {g.options.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </optgroup>
        ))}
      </select>

      {/* HS6 Input Section */}
      <div style={{ marginTop: 8 }}>
        <label style={{ fontFamily: "Montserrat", fontWeight: "bold", fontSize: 18, color: "#008C00", marginBottom: 8, display: "block" }}>
          Výběr HS6 (volitelné)
        </label>
        
        <div style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
          <div style={{ flex: 1 }}>
            <input
              type="text"
              value={hs6Input}
              onChange={(e) => handleHS6Input(e.target.value)}
              placeholder="Zadejte 6-místný HS6 kód"
              style={{
                width: "100%",
                padding: "8px 12px",
                border: hs6Error ? "1px solid #ff4444" : "1px solid #ddd",
                borderRadius: 4,
                fontSize: 14,
                boxSizing: "border-box"
              }}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleHS6Add();
                }
              }}
            />
            {hs6Error && (
              <div style={{ fontSize: 12, color: "#ff4444", marginTop: 4 }}>
                {hs6Error}
              </div>
            )}
          </div>
          
          <button
            onClick={handleHS6Add}
            disabled={!validateHS6(hs6Input).isValid || savedHS6Codes.length >= 5}
            style={{
              padding: "8px 16px",
              backgroundColor: validateHS6(hs6Input).isValid && savedHS6Codes.length < 5 ? "#008C00" : "#ccc",
              color: "white",
              border: "none",
              borderRadius: 4,
              cursor: validateHS6(hs6Input).isValid && savedHS6Codes.length < 5 ? "pointer" : "not-allowed",
              fontSize: 14,
              whiteSpace: "nowrap"
            }}
          >
            Analyzovat
          </button>
        </div>

        {/* Saved HS6 Codes */}
        {savedHS6Codes.length > 0 && (
          <div style={{ marginTop: 12 }}>
            <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 6, color: "#333" }}>
              Uložené kódy:
            </div>
            {savedHS6Codes.map((item) => (
              <div
                key={item.code}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  padding: "6px 8px",
                  marginBottom: 4,
                  backgroundColor: selectedHS6 === item.code ? "#f0f7ff" : "#f8f9fa",
                  border: selectedHS6 === item.code ? "1px solid #1677ff" : "1px solid #e9ecef",
                  borderRadius: 4,
                  fontSize: 13,
                  cursor: "pointer"
                }}
                onClick={() => handleHS6Select(item.code)}
              >
                <span style={{ flex: 1, fontWeight: selectedHS6 === item.code ? "600" : "normal" }}>
                  {item.code} - {item.label}
                </span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleHS6Delete(item.code);
                  }}
                  style={{
                    background: "none",
                    border: "none",
                    color: "#666",
                    cursor: "pointer",
                    fontSize: 16,
                    padding: "2px 4px"
                  }}
                  title="Smazat"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Add More Button */}
        {savedHS6Codes.length > 0 && savedHS6Codes.length < 5 && (
          <button
            onClick={() => {
              // Focus the input field
              const input = document.querySelector('input[placeholder="Zadejte 6-místný HS6 kód"]');
              if (input) input.focus();
            }}
            style={{
              marginTop: 8,
              padding: "6px 12px",
              backgroundColor: "transparent",
              color: "#008C00",
              border: "1px dashed #008C00",
              borderRadius: 4,
              cursor: "pointer",
              fontSize: 14,
              width: "100%"
            }}
          >
            + Přidat další HS6 kód
          </button>
        )}
      </div>

    </div>
  );
}