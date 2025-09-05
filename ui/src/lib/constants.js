// Constants extracted from App.jsx

export const API_BASE = import.meta?.env?.VITE_API_BASE || (import.meta?.env?.DEV ? 'http://127.0.0.1:8000' : '');

export const SHOW_SKELETON = true; // Step 1: visualize empty layout

export const ISO3_TO_NAME = {
  DEU: "Germany",
  POL: "Poland", 
  CZE: "Czech Republic",
  FRA: "France",
  USA: "United States of America"
};