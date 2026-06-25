import { useState } from 'react';
import { IconX } from './Icons';

// Icono inline para no depender de otros archivos
const ExcelIcon = ({ size = 16 }) => (
  <svg width={size} height={size} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
);

export default function ExportModal({ isOpen, onClose }) {
  const [exportMode, setExportMode] = useState('all'); // 'all' o 'single'
  const [targetIp, setTargetIp] = useState('');
  const [isExporting, setIsExporting] = useState(false);

  if (!isOpen) return null;

  const handleExport = async () => {
    try {
      if (window.pywebview && window.pywebview.api) {
        const ipParam = exportMode === 'single' ? targetIp : null;
        const success = await window.pywebview.api.save_excel(ipParam);
        if (!success) {
          // Si el usuario canceló el diálogo o hubo error, no hacemos nada más
        }
      } else {
        const apiUrl = import.meta.env.VITE_API_URL || (window.location.protocol + '//' + window.location.host + '/api');
        const url = exportMode === 'single' ? `${apiUrl}/export/excel?ip=${targetIp}` : `${apiUrl}/export/excel`;
        // Regla de Oro 8: Descargas: window.location.href, NO <a download>
        window.location.href = url;
      }
      
      setTimeout(() => {
        setIsExporting(false);
        onClose();
      }, 1000);
    } catch (err) {
      alert("Error exportando excel: " + err.message);
      setIsExporting(false);
      onClose();
    }
  };

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal modal-sm" style={{ maxWidth: 450 }}>
        <div className="modal-head">
          <div className="modal-head-title">
            <ExcelIcon size={15} />
            Exportar Reporte Excel
          </div>
          <button className="btn btn-ghost" onClick={onClose} disabled={isExporting}>
            <IconX size={14} />
          </button>
        </div>

        <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <label className="scan-row" style={{ cursor: 'pointer', alignItems: 'flex-start', padding: '12px' }}>
            <input 
              type="radio" 
              name="exportMode" 
              value="all" 
              checked={exportMode === 'all'} 
              onChange={() => setExportMode('all')}
              style={{ marginTop: 4, cursor: 'pointer' }}
            />
            <div style={{ marginLeft: 10, flex: 1 }}>
              <div style={{ fontWeight: 600, color: 'var(--tx-1)' }}>Toda la Flota</div>
              <div style={{ fontSize: 12, color: 'var(--tx-4)', marginTop: 4 }}>Exporta las métricas y estado de todas las computadoras registradas en el sistema.</div>
            </div>
          </label>

          <label className="scan-row" style={{ cursor: 'pointer', alignItems: 'flex-start', padding: '12px', flexWrap: 'wrap' }}>
            <input 
              type="radio" 
              name="exportMode" 
              value="single" 
              checked={exportMode === 'single'} 
              onChange={() => setExportMode('single')}
              style={{ marginTop: 4, cursor: 'pointer' }}
            />
            <div style={{ marginLeft: 10, flex: 1 }}>
              <div style={{ fontWeight: 600, color: 'var(--tx-1)' }}>Una PC Específica</div>
              <div style={{ fontSize: 12, color: 'var(--tx-4)', marginTop: 4, marginBottom: 12 }}>Exporta los datos detallados de una sola máquina indicando su IP.</div>
              {exportMode === 'single' && (
                <input 
                  type="text" 
                  className="form-input"
                  value={targetIp}
                  onChange={(e) => setTargetIp(e.target.value)}
                  placeholder="Ej: 192.168.0.10"
                  style={{ width: '100%' }}
                  autoFocus
                />
              )}
            </div>
          </label>
        </div>

        <div className="modal-foot">
          <button className="btn" onClick={onClose} disabled={isExporting}>
            Cancelar
          </button>
          <button 
            className="btn btn-primary" 
            onClick={handleExport}
            disabled={isExporting || (exportMode === 'single' && !targetIp.trim())}
            style={{ marginLeft: 'auto' }}
          >
            {isExporting ? <><div className="spinner" style={{ width: 13, height: 13, borderWidth: 2 }} /> Exportando</> : 'Generar Excel'}
          </button>
        </div>
      </div>
    </div>
  );
}
