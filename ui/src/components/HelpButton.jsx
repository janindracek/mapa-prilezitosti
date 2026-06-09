import React, { useEffect, useState } from "react";
import { helpTitle, helpText } from "../lib/labels.js";

// Modal chrome (click-outside + Escape to close).
export function HelpModal({ open, onClose, title, children }) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e) => e.key === "Escape" && onClose && onClose();
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)",
        display: "flex", alignItems: "center", justifyContent: "center",
        zIndex: 1000, padding: 20,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: "#fff", borderRadius: 8, padding: 24, maxWidth: 640,
          maxHeight: "80vh", overflow: "auto", position: "relative",
          boxShadow: "0 4px 20px rgba(0,0,0,0.15)",
        }}
      >
        <button
          onClick={onClose}
          aria-label="Zavřít"
          style={{
            position: "absolute", top: 12, right: 12, background: "none",
            border: "none", fontSize: 22, cursor: "pointer", color: "#666",
            width: 30, height: 30, borderRadius: 4,
          }}
        >
          ×
        </button>
        {title && (
          <h2 style={{ fontFamily: "Montserrat", fontWeight: "bold", marginBottom: 14, fontSize: 19, color: "#008C00", paddingRight: 40 }}>
            {title}
          </h2>
        )}
        <div style={{ fontSize: 14, lineHeight: 1.55, color: "#444" }}>{children}</div>
      </div>
    </div>
  );
}

// A small "?" button that opens a popup with the explanation for a registry
// concept `id` (or an explicit title/text). `extra` renders extra nodes below
// the text (e.g. a live peer-group panel). Drop it anywhere a label needs help.
export default function HelpButton({ id, title, text, extra = null, size = 18, label = "Vysvětlení" }) {
  const [open, setOpen] = useState(false);
  const t = title || (id ? helpTitle(id) : "");
  const body = text != null ? text : (id ? helpText(id) : "");
  return (
    <>
      <button
        type="button"
        onClick={(e) => { e.stopPropagation(); setOpen(true); }}
        title={label}
        aria-label={label}
        style={{
          width: size, height: size, minWidth: size, borderRadius: "50%",
          border: "1px solid #008C00", background: "transparent", color: "#008C00",
          fontSize: Math.round(size * 0.62), fontWeight: "bold", cursor: "pointer",
          display: "inline-flex", alignItems: "center", justifyContent: "center",
          padding: 0, lineHeight: 1, verticalAlign: "middle",
        }}
      >
        ?
      </button>
      <HelpModal open={open} onClose={() => setOpen(false)} title={t}>
        {body && <p style={{ margin: "0 0 8px" }}>{body}</p>}
        {extra}
      </HelpModal>
    </>
  );
}
