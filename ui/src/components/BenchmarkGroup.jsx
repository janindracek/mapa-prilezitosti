import React, { useState, useEffect } from "react";


function getBenchmarkTypeDescription(signalType) {
  if (!signalType?.includes('Peer_gap')) {
    return null;
  }
  
  if (signalType === 'Peer_gap_human') {
    return {
      type: 'Geografická',
      description: 'Skupina zemí ze stejného geografického regionu s podobnou ekonomickou úrovní a obchodními vzorci.'
    };
  } else if (signalType === 'Peer_gap_opportunity') {
    return {
      type: 'Příležitostní', 
      description: 'Země s podobnými obchodními příležitostmi a exportním potenciálem pro daný produkt.'
    };
  } else if (signalType === 'Peer_gap_matching') {
    return {
      type: 'Strukturální',
      description: 'Země s podobnou obchodní strukturou a exportními profily identifikované algoritmicky.'
    };
  }
  
  return null;
}

function continentToCz(continent) {
  const key = (continent || '').trim();
  const mapping = {
    'Europe': { cz: 'Evropa', order: 1 },
    'Asia': { cz: 'Asie', order: 2 }, 
    'North America': { cz: 'Severní Amerika', order: 3 },
    'South America': { cz: 'Jižní Amerika', order: 4 },
    'Africa': { cz: 'Afrika', order: 5 },
    'Oceania': { cz: 'Oceánie', order: 6 },
  };
  return mapping[key] || { cz: key || 'Ostatní', order: 99 };
}

export default function BenchmarkGroup({ 
  signal = null, 
  productData = [], 
  country = null 
}) {
  const [continentsMap, setContinentsMap] = useState(null);
  const [peerGroupName, setPeerGroupName] = useState(null);
  const [allPeerCountries, setAllPeerCountries] = useState([]);
  
  // Load continent data
  useEffect(() => {
    fetch('/ref/country_continents.json')
      .then((r) => (r.ok ? r.json() : {}))
      .then((data) => {
        if (data && typeof data === 'object') setContinentsMap(data);
      })
      .catch(() => {});
  }, []);

  // Load complete peer group information
  useEffect(() => {
    if (signal?.type?.includes('Peer_gap') && (signal?.partner_iso3 || country) && signal?.hs6) {
      const countryCode = signal?.partner_iso3 || country;
      const hs6Code = signal?.hs6;
      const year = signal?.year || 2023;
      
      // Determine peer group type
      let peerGroupType = 'default';
      if (signal.type === 'Peer_gap_human') {
        peerGroupType = 'human';
      } else if (signal.type === 'Peer_gap_opportunity') {
        peerGroupType = 'opportunity'; 
      } else if (signal.type === 'Peer_gap_matching') {
        peerGroupType = 'matching';
      }
      
      // Get complete peer group data (all countries, regardless of trade volume)
      const fetchCompleteData = async () => {
        try {
          // Get complete peer group information from new endpoint
          const completeResponse = await fetch(`/peer_groups/complete?country=${countryCode}&peer_group=${peerGroupType}&year=${year}`);
          if (completeResponse.ok) {
            const completeData = await completeResponse.json();
            if (!completeData.error) {
              setAllPeerCountries(completeData.peer_countries || []);
              setPeerGroupName(completeData.cluster_name);
            }
          }
        } catch (error) {
          console.warn('Failed to load complete peer group data:', error);
        }
      };
      
      fetchCompleteData();
    } else {
      setAllPeerCountries([]);
      setPeerGroupName(null);
    }
  }, [signal, country]);

  // Only show for benchmark signals
  const benchmarkInfo = getBenchmarkTypeDescription(signal?.type);
  if (!benchmarkInfo) {
    return null;
  }

  // Get countries that have trade data for this specific product
  const countriesWithTradeData = new Set(
    Array.isArray(productData) ? productData.map(item => item.id || item.name).filter(Boolean) : []
  );
  
  // Use all peer countries (complete cluster) for display
  const displayCountries = allPeerCountries.length > 0 ? allPeerCountries : [];
  
  // Group all peer countries by continent (not just those with trade data)
  const countriesByContinent = {};
  if (continentsMap && displayCountries.length > 0) {
    displayCountries.forEach(countryCode => {
      const continent = continentsMap[countryCode] || 'Unknown';
      const { cz: continentCz, order } = continentToCz(continent);
      
      if (!countriesByContinent[continentCz]) {
        countriesByContinent[continentCz] = { countries: [], order };
      }
      
      // Store country with its trade data status
      countriesByContinent[continentCz].countries.push({
        code: countryCode,
        hasTradeData: countriesWithTradeData.has(countryCode)
      });
    });
  }

  // Sort continents by order and countries alphabetically
  const sortedContinents = Object.entries(countriesByContinent)
    .sort(([,a], [,b]) => a.order - b.order)
    .map(([continent, data]) => ({
      continent,
      countries: Array.isArray(data?.countries) ? data.countries.sort((a, b) => a.code.localeCompare(b.code)) : []
    }));

  return (
    <div style={{ border: "1px solid #eee", borderRadius: 6, padding: 12, background: "#fff", marginBottom: 12 }}>
      <h2 style={{ fontFamily: "Montserrat", fontWeight: "bold", marginBottom: 8, fontSize: 18, color: "#008C00" }}>
        Benchmarková skupina
      </h2>
      
      {/* Benchmark type and description */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ 
          fontSize: 14, 
          fontWeight: "600", 
          color: "#333",
          marginBottom: 4
        }}>
          Typ: {benchmarkInfo.type}
        </div>
        
        {/* Show peer group name if available */}
        {peerGroupName && (
          <div style={{ 
            fontSize: 14, 
            fontWeight: "600", 
            color: "#008C00",
            marginBottom: 6
          }}>
            Skupina: {peerGroupName}
          </div>
        )}
        
        <div style={{ 
          fontSize: 13, 
          color: "#666",
          lineHeight: 1.4,
          marginBottom: 12
        }}>
          {benchmarkInfo.description}
        </div>
      </div>

      {/* Countries grouped by continent */}
      {sortedContinents.length > 0 && (
        <div>
          <div style={{ 
            fontSize: 14, 
            fontWeight: "600", 
            color: "#333",
            marginBottom: 8
          }}>
            Země ve skupině ({displayCountries.length}):
          </div>
          <div style={{ fontSize: 12, lineHeight: 1.8 }}>
            {sortedContinents.map(({ continent, countries }) => (
              <div key={continent} style={{ marginBottom: 8 }}>
                <span style={{ fontWeight: "600", color: "#008C00" }}>
                  {continent}:
                </span>{' '}
                <span>
                  {countries.map((country, index) => (
                    <span key={country.code}>
                      {index > 0 && ', '}
                      <span style={{ 
                        color: country.hasTradeData ? "#000" : "#999",
                        fontWeight: country.hasTradeData ? "600" : "normal"
                      }}>
                        {country.code}
                      </span>
                    </span>
                  ))}
                </span>
              </div>
            ))}
          </div>
          
          {/* Legend */}
          <div style={{ 
            fontSize: 11, 
            color: "#666", 
            marginTop: 12,
            paddingTop: 8,
            borderTop: "1px solid #eee"
          }}>
            <span style={{ fontWeight: "600", color: "#000" }}>Černě</span> = mají obchod v tomto produktu, {' '}
            <span style={{ color: "#999" }}>šedě</span> = nemají obchod v tomto produktu
          </div>
        </div>
      )}

      {/* Show message if no peer countries available */}
      {displayCountries.length === 0 && (
        <div style={{ 
          fontSize: 13, 
          color: "#666", 
          fontStyle: "italic" 
        }}>
          Seznam zemí se načítá...
        </div>
      )}
    </div>
  );
}