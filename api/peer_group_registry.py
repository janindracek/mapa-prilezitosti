"""
Centralized Peer Group Registry

This module provides a unified registry for all peer group methodologies,
supporting signal generation, chart filtering, map filtering, and UI explanations.
"""

from typing import Dict, List, Set, Optional, Any
import os
import pandas as pd
from api.settings import settings


class PeerGroupRegistry:
    """
    Centralized registry for peer group configurations and operations.
    
    Supports all UI use cases:
    1. Signal generation (provide countries for median calculations)
    2. Chart filtering (subset countries for bar charts)
    3. Map filtering (subset countries for map display)
    4. Human-readable explanations (methodology descriptions)
    """
    
    # Centralized methodology configurations
    METHODOLOGIES = {
        "default": {
            "name": "Geographic/Regional Peers",
            "description": "Countries grouped by geographic proximity and economic development level. This traditional approach compares performance within regional context.",
            "explanation_template": "Geographic peer group includes countries from similar regions and development levels. Czech Republic is compared against {country_count} countries including {sample_countries}.",
            "data_source": "peer_groups_statistical.parquet",
            "supports_clustering": False
        },
        "trade_structure": {
            "name": "Trade Structure Groups", 
            "description": "Countries clustered by similarity of their import portfolios across HS2 categories using cosine similarity. This identifies economies with comparable trade structure patterns.",
            "explanation_template": "Země je zařazena do skupiny '{cluster_name}': {cluster_description} Skupina zahrnuje {country_count} zemí s podobnou obchodní strukturou včetně {sample_countries}.",
            "data_source": "peer_groups_hs2.parquet",
            "supports_clustering": True,
            "cluster_explanations": {
                0: {
                    "name": "Komoditně orientované a rozvíjející se importéři",
                    "description": "Země s velkou závislostí na surovinách a základním průmyslovém zboží; import orientován na komodity a nezbytnosti."
                },
                1: {
                    "name": "Malé ostrovní a servisně orientované ekonomiky", 
                    "description": "Omezená průmyslová základna, import dominují základní potřeby (potraviny, paliva) a reexporty; často servisní/turistické ekonomiky."
                },
                2: {
                    "name": "Exportéři surovin s úzkým importním profilem",
                    "description": "Exportéři uhlovodíků/primárních komodit, kteří importují především kapitálové zboží, strojírenské výrobky a rafinované spotřební produkty."
                },
                3: {
                    "name": "Velcí diverzifikovaní importéři",
                    "description": "Široký importní profil zahrnující technologie, strojírenství, spotřební zboží a suroviny; vysoká diverzifikace v kategoriích HS2."
                },
                4: {
                    "name": "Evropské jádro a pokročilá Asie",
                    "description": "Pokročilá výroba, silná poptávka po strojírenství, vozidlech, meziproduktách; diverzifikované a technologicky orientované."
                },
                5: {
                    "name": "Niche malé trhy",
                    "description": "Specifické importní potřeby, často geopoliticky ovlivněné importní struktury."
                },
                6: {
                    "name": "Středomořské a střední rozvíjející se",
                    "description": "Mix industrializovaných středních ekonomik a rychle rostoucích rozvíjejících se trhů; import vyrovnaný mezi kapitálovým a spotřebním zbožím."
                },
                7: {
                    "name": "Hraniční a nízkopříjmové",
                    "description": "Import koncentrovaný na potraviny, paliva a základní spotřební zboží; omezená průmyslová diverzifikace."
                },
                8: {
                    "name": "Ostrovní a vzdálené ekonomiky",
                    "description": "Geografická izolace; import dominují paliva, lodní vstupy, potraviny."
                },
                9: {
                    "name": "Čínský cluster / Severní cluster",
                    "description": "Silně ovlivněné čínskými dodavatelskými řetězci; import zahrnuje průmyslové vstupy, energii a strojírenství; zahrnuje některé severní/asijské huby."
                }
            }
        },
        "opportunity": {
            "name": "Export Opportunity Peers",
            "description": "Countries grouped by similar export opportunity profiles and market potential. This identifies economies with comparable market opportunities.",
            "explanation_template": "Země je zařazena do skupiny '{cluster_name}': {cluster_description} Skupina zahrnuje {country_count} zemí s podobnými exportními příležitostmi včetně {sample_countries}.",
            "data_source": "peer_groups_opportunity.parquet",
            "supports_clustering": True,
            "cluster_explanations": {
                0: {
                    "name": "Malé a transformující se ekonomiky",
                    "description": "Malé ekonomiky v transformaci nebo s omezenou průmyslovou základnou – Gruzie, Moldavsko, Arménie, Nepál, Albánie."
                },
                1: {
                    "name": "Izolované a autoritářské režimy", 
                    "description": "Ekonomiky s omezeným přístupem k světovým trhům nebo pod sankcemi – Bělorusko, Kuba, Venezuela, Turkmenistán."
                },
                2: {
                    "name": "Mikrostáty a ostrovní ekonomiky",
                    "description": "Velmi malé státy a závislá území s omezenou ekonomickou diverzifikací – mikrostáty, ostrovní státy, závislá území."
                },
                3: {
                    "name": "Rozvojové ekonomiky s exportním potenciálem",
                    "description": "Rozvojové země s rostoucím exportním potenciálem – Kambodža, Honduras, Ghana, Namibie, Panama."
                },
                4: {
                    "name": "Středně příjmové diverzifikované ekonomiky",
                    "description": "Diverzifikované ekonomiky se středním příjmem a stabilním exportním potenciálem – Kostarika, Ekvádor, Guatemala, Maroko."
                },
                5: {
                    "name": "Malé bohaté a surovině orientované ekonomiky",
                    "description": "Malé ekonomiky s vysokým příjmem nebo orientované na suroviny – Fidži, Jamajka, Gabon, Trinidad a Tobago."
                },
                6: {
                    "name": "Pokročilé výrobní a technologické ekonomiky",
                    "description": "Rozvinuté ekonomiky s pokročilou výrobou a vysokým technologickým potenciálem – Německo, Japonsko, Korea, Kanada, Austrálie, Čína."
                },
                7: {
                    "name": "Nejméně rozvinuté a konfliktní oblasti",
                    "description": "Nejméně rozvinuté země často zasažené konflikty – africké LDC, Afghánistán, Mali, Súdán."
                },
                8: {
                    "name": "Mikrostáty a specifická území",
                    "description": "Velmi malé státy, závislá území a specifické jurisdikce s úzkým exportním profilem – tichomořské ostrovy, závislá území."
                },
                9: {
                    "name": "Střední příjem s rostoucími příležitostmi",
                    "description": "Ekonomiky se středním příjmem a rostoucími exportními příležitostmi – Chile, Kolumbie, Chorvatsko, Izrael, Kazachstán."
                }
            }
        },
        "human": {
            "name": "Curated Regional Groups",
            "description": "Manually curated peer groups based on expert economic and geographic analysis. These groups reflect real-world economic relationships.",
            "explanation_template": "Expertně kurátorovaná skupina '{cluster_name}': {cluster_description} Země je seskupena s {country_count} zeměmi včetně {sample_countries}.",
            "data_source": "peer_groups_human.parquet", 
            "supports_clustering": True,
            "cluster_names": {
                0: "EU Core West", 1: "EU Nordics", 2: "Baltics",
                3: "Central Europe (V4+AT+SI)", 4: "Southern EU (Med EU)", 
                5: "UK & CH", 6: "Western Balkans", 7: "Eastern Partnership & Caucasus",
                8: "Russia & Central Asia", 9: "North America",
                10: "Central America & Caribbean", 11: "South America", 12: "GCC",
                13: "Levant & Iran/Iraq/Yemen", 14: "North Africa (Med non-EU)",
                15: "East Asia Advanced", 16: "China", 17: "Southeast Asia",
                18: "South Asia", 19: "Sub-Saharan Africa – West",
                20: "Sub-Saharan Africa – East & Horn", 21: "Sub-Saharan Africa – South",
                22: "Oceania & Pacific"
            },
            "cluster_explanations": {
                0: {
                    "name": "EU Core West",
                    "description": "Západní jádro EU s vysokou otevřeností a sofistikovanou poptávkou po průmyslových vstupech."
                },
                1: {
                    "name": "EU Nordics", 
                    "description": "Severské ekonomiky s vysokou přidanou hodnotou, silná orientace na technologie a služby."
                },
                2: {
                    "name": "Baltics",
                    "description": "Malé, velmi otevřené ekonomiky s rychlou integrací do EU hodnotových řetězců."
                },
                3: {
                    "name": "Central Europe (V4+AT+SI)",
                    "description": "Průmyslové jádro střední Evropy, vysoký podíl strojírenství a automobilového dodavatelského řetězce."
                },
                4: {
                    "name": "Southern EU (Med EU)",
                    "description": "Mediterránní členové EU – smíšený profil (spotřeba, průmysl, stavebnictví)."
                },
                5: {
                    "name": "UK & CH",
                    "description": "Velké finanční a obchodní huby s vyspělou poptávkou a vysokou kupní silou."
                },
                6: {
                    "name": "Western Balkans",
                    "description": "Přechodové ekonomiky s rostoucí poptávkou po investičním zboží a stavebních vstupech."
                },
                7: {
                    "name": "Eastern Partnership & Caucasus", 
                    "description": "Východní partnerství a Kavkaz – tranzitní poloha, heterogenní profil, časté regulační frikce."
                },
                8: {
                    "name": "Russia & Central Asia",
                    "description": "Rusko + Střední Asie – komoditní základna, importy strojírenských vstupů a spotřebního zboží."
                },
                9: {
                    "name": "North America", 
                    "description": "Velké, bohaté trhy s vysokou diverzifikací dovozu."
                },
                10: {
                    "name": "Central America & Caribbean",
                    "description": "Menší, často ostrovní ekonomiky, dovoz širokého spektra základních i spotřebních statků."
                },
                11: {
                    "name": "South America",
                    "description": "Středně velké až velké trhy, mix komoditních a průmyslových dovozů."
                },
                12: {
                    "name": "GCC",
                    "description": "Ropná jádra Perského zálivu – vysoká kupní síla, velká poptávka po stavebnictví a technologiích."
                },
                13: {
                    "name": "Levant & Iran/Iraq/Yemen",
                    "description": "Heterogenní, geopoliticky citlivý region, od high‑tech po základní statky."
                },
                14: {
                    "name": "North Africa (Med non‑EU)",
                    "description": "Severní Afrika mimo EU – mix průmyslu, spotřeby a energetiky, různé překážky přístupu."
                },
                15: {
                    "name": "East Asia Advanced",
                    "description": "Japonsko, Korea, Taiwan, Hongkong, Macao – vysoce technické hodnotové řetězce."
                },
                16: {
                    "name": "China",
                    "description": "Čína jako samostatný blok – obří a specifický importní profil."
                },
                17: {
                    "name": "Southeast Asia",
                    "description": "ASEAN – rychle rostoucí poptávka, silná výroba a diversifikace partnerů."
                },
                18: {
                    "name": "South Asia",
                    "description": "Jižní Asie – velké trhy, rostoucí průmysl a infrastruktura."
                },
                19: {
                    "name": "Sub‑Saharan Africa – West",
                    "description": "Západní Afrika – rostoucí spotřeba, infrastrukturní potřeby, vyšší logistická frikce."
                },
                20: {
                    "name": "Sub‑Saharan Africa – East & Horn",
                    "description": "Východní Afrika a Africký roh – růst populace a infrastruktury."
                },
                21: {
                    "name": "Sub‑Saharan Africa – South",
                    "description": "Jižní Afrika + sousedé – větší průmyslová základna a regionální huby."
                },
                22: {
                    "name": "Oceania & Pacific",
                    "description": "Austrálie, NZ a Pacifik – vysoce otevřené trhy (ANZ) a malé ostrovní ekonomiky."
                }
            }
        }
    }
    
    @classmethod
    def get_peer_countries_for_signals(cls, country_iso3: str, method: str, year: int, cluster_params: Optional[str] = None) -> Optional[Set[str]]:
        """
        Get peer countries for signal generation (median calculations).
        
        Args:
            country_iso3: Target country code
            method: Peer group methodology 
            year: Target year
            cluster_params: Optional cluster parameters (e.g., "10" for k=10)
            
        Returns:
            Set of peer country ISO3 codes, or None if not found
        """
        from api.data.loaders import resolve_peers
        
        # Format peer group parameter for legacy compatibility
        if cluster_params and method != "default":
            peer_group_param = f"{method}:{cluster_params}"
        else:
            peer_group_param = method
            
        return resolve_peers(country_iso3, year, peer_group_param)
    
    @classmethod
    def get_peer_countries_for_charts(cls, country_iso3: str, method: str, year: int, cluster_params: Optional[str] = None) -> List[str]:
        """
        Get peer countries for chart display (bar charts, comparisons).
        
        Returns:
            List of peer country ISO3 codes for chart display
        """
        peer_countries = cls.get_peer_countries_for_signals(country_iso3, method, year, cluster_params)
        return sorted(list(peer_countries)) if peer_countries else []
    
    @classmethod
    def get_peer_countries_for_map(cls, country_iso3: str, method: str, year: int, cluster_params: Optional[str] = None) -> List[str]:
        """
        Get peer countries for map filtering (future use).
        
        Returns:
            List of peer country ISO3 codes for map highlighting
        """
        return cls.get_peer_countries_for_charts(country_iso3, method, year, cluster_params)
    
    @classmethod
    def get_human_readable_explanation(cls, country_iso3: str, method: str, year: int, cluster_params: Optional[str] = None) -> Dict[str, Any]:
        """
        Get human-readable peer group explanation for UI display.
        
        Returns:
            {
                "methodology_name": "Export Structure Matching",
                "methodology_description": "Countries clustered by...",
                "peer_countries": ["DEU", "AUT", "POL", ...],
                "explanation_text": "Export structure peers are countries with...",
                "cluster_name": "Central Europe Cluster" (if applicable)
            }
        """
        methodology = cls.METHODOLOGIES.get(method, {})
        peer_countries = cls.get_peer_countries_for_charts(country_iso3, method, year, cluster_params)
        
        # Determine cluster info
        cluster_name = None
        cluster_description = None
        cluster_id = None
        
        # Get actual cluster ID from the data - all now use consistent alpha-3 format
        try:
            from api.data.loaders import load_peer_groups
            peer_data = load_peer_groups(method, year, country_iso3)
            if peer_data is not None and not peer_data.empty:
                country_row = peer_data[peer_data['iso3'] == country_iso3]
                if not country_row.empty:
                    cluster_id = country_row.iloc[0]['cluster']
            elif cluster_params:
                cluster_id = int(cluster_params)
        except Exception as e:
            print(f"Error determining cluster for {country_iso3} in method {method}: {e}")
        
        # Get cluster information
        if cluster_id is not None:
            cluster_explanations = methodology.get("cluster_explanations", {})
            if cluster_id in cluster_explanations:
                cluster_info = cluster_explanations[cluster_id]
                cluster_name = cluster_info.get("name")
                cluster_description = cluster_info.get("description")
            elif method == "human":
                cluster_name = methodology.get("cluster_names", {}).get(cluster_id)
        
        # Generate explanation text
        country_count = len(peer_countries)
        sample_countries = ", ".join(peer_countries[:3]) if peer_countries else "none found"
        
        explanation_template = methodology.get("explanation_template", "Peer group includes {country_count} countries including {sample_countries}.")
        explanation_text = explanation_template.format(
            country_count=country_count,
            sample_countries=sample_countries,
            cluster_name=cluster_name or f"Cluster {cluster_id or cluster_params or 'default'}",
            cluster_description=cluster_description or ""
        )
        
        return {
            "methodology_name": methodology.get("name", method.title()),
            "methodology_description": methodology.get("description", "Peer group methodology."),
            "peer_countries": peer_countries,
            "explanation_text": explanation_text,
            "cluster_name": cluster_name,
            "cluster_description": cluster_description,
            "country_count": country_count
        }
    
    @classmethod
    def get_available_methods(cls) -> List[Dict[str, Any]]:
        """Get list of all available peer group methodologies."""
        return [
            {
                "method": method,
                "name": config["name"],
                "description": config["description"],
                "supports_clustering": config.get("supports_clustering", False)
            }
            for method, config in cls.METHODOLOGIES.items()
        ]
    
    @classmethod
    def register_new_methodology(cls, method: str, config: Dict[str, Any]) -> None:
        """Register a new peer group methodology (for future extension)."""
        cls.METHODOLOGIES[method] = config
    
    @classmethod
    def get_methodology_config(cls, method: str) -> Dict[str, Any]:
        """Get configuration for a specific methodology."""
        return cls.METHODOLOGIES.get(method, {})


# Convenience functions for common operations
def get_peer_explanation_for_signal(signal_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get peer group explanation for a specific signal.
    
    Args:
        signal_data: Signal object with method, hs6, partner_iso3, etc.
        
    Returns:
        Human-readable explanation dict
    """
    method = signal_data.get("method", "default")
    year = signal_data.get("year", 2023)
    
    # For signals, we want to explain Czech Republic's peer group
    return PeerGroupRegistry.get_human_readable_explanation("CZE", method, year)


def get_peer_countries_for_bar_chart(signal_data: Dict[str, Any]) -> List[str]:
    """
    Get peer countries to display in bar chart for a signal.
    
    Args:
        signal_data: Signal object with method info
        
    Returns:
        List of country codes for bar chart
    """
    method = signal_data.get("method", "default") 
    year = signal_data.get("year", 2023)
    
    return PeerGroupRegistry.get_peer_countries_for_charts("CZE", method, year)