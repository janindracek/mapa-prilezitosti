console.log("[main] loaded");

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import ErrorBoundary from './ErrorBoundary.jsx'
import App from './App.jsx'

console.log("[main] before render");
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </StrictMode>
);


// --- TEMP API SMOKE TEST (remove after validation) ---
(async () => {
  const BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";
  console.log("[API BASE]", BASE);
  try {
    const res = await fetch(`${BASE}/controls`, { credentials: "omit" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    console.log("[/controls]", data);
  } catch (err) {
    console.error("[API test failed]", err);
  }
})();