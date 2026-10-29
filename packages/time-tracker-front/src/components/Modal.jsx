import { useEffect } from "react";
import { IconX } from "./Icons.jsx";

// Dialogo simples: fecha com Esc ou clique fora.
export default function Modal({ title, tone, onClose, children }) {
  useEffect(() => {
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className={`modal ${tone || ""}`} role="dialog" aria-modal="true" aria-label={title}>
        <div className="modal-head">
          <h3>{title}</h3>
          <button className="icon-btn" onClick={onClose} aria-label="Fechar">
            <IconX size={18} />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
