import { useState } from 'react';

// Iconos inline para no depender de otros archivos
const ExcelIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
);

export default function ExportModal({ isOpen, onClose }) {
  const [exportMode, setExportMode] = useState('all'); // 'all' o 'single'
  const [targetIp, setTargetIp] = useState('');
  const [isExporting, setIsExporting] = useState(false);

  if (!isOpen) return null;

  const handleExport = async () => {
    setIsExporting(true);
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
      if (window.pywebview) {
        // En desktop app
        await window.pywebview.api.export_excel_dialog(exportMode === 'single' ? targetIp : null);
      } else {
        // En navegador (dev mode)
        const url = exportMode === 'single' ? `${apiUrl}/export/excel?ip=${targetIp}` : `${apiUrl}/export/excel`;
        const res = await fetch(url);
        if (res.ok) {
          const blob = await res.blob();
          const downloadUrl = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = downloadUrl;
          a.download = `codere_export_${new Date().getTime()}.xlsx`;
          document.body.appendChild(a);
          a.click();
          a.remove();
        }
      }
    } catch (err) {
      console.error("Error exportando excel:", err);
    } finally {
      setIsExporting(false);
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-codere-dark border border-gray-700 rounded-xl p-6 w-full max-w-md shadow-2xl relative">
        <button 
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-white"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <div className="flex items-center gap-3 mb-6 border-b border-gray-700 pb-4">
          <div className="bg-codere-green/20 p-2 rounded-lg text-codere-green">
            <ExcelIcon />
          </div>
          <h2 className="text-xl font-bold text-white">Exportar Reporte</h2>
        </div>

        <div className="space-y-4 mb-6">
          <label className="flex items-start gap-3 p-3 rounded-lg border border-gray-700 hover:border-codere-green cursor-pointer bg-gray-800/50 transition-colors">
            <input 
              type="radio" 
              name="exportMode" 
              value="all" 
              checked={exportMode === 'all'} 
              onChange={() => setExportMode('all')}
              className="mt-1 accent-codere-green"
            />
            <div>
              <p className="font-bold text-white">Toda la Flota</p>
              <p className="text-sm text-gray-400">Exporta las métricas de todas las computadoras registradas.</p>
            </div>
          </label>

          <label className="flex items-start gap-3 p-3 rounded-lg border border-gray-700 hover:border-codere-green cursor-pointer bg-gray-800/50 transition-colors">
            <input 
              type="radio" 
              name="exportMode" 
              value="single" 
              checked={exportMode === 'single'} 
              onChange={() => setExportMode('single')}
              className="mt-1 accent-codere-green"
            />
            <div className="w-full">
              <p className="font-bold text-white">Una PC Específica</p>
              <p className="text-sm text-gray-400 mb-2">Exporta los datos de una sola máquina por su IP.</p>
              {exportMode === 'single' && (
                <input 
                  type="text" 
                  value={targetIp}
                  onChange={(e) => setTargetIp(e.target.value)}
                  placeholder="Ej: 192.168.0.10"
                  className="w-full bg-codere-dark border border-gray-600 rounded p-2 text-white focus:border-codere-green focus:outline-none"
                  autoFocus
                />
              )}
            </div>
          </label>
        </div>

        <div className="flex justify-end gap-3">
          <button 
            onClick={onClose}
            className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
          >
            Cancelar
          </button>
          <button 
            onClick={handleExport}
            disabled={exportMode === 'single' && !targetIp.trim()}
            className="flex items-center gap-2 bg-codere-green text-codere-dark px-6 py-2 rounded font-bold hover:bg-[#6CA022] transition-colors shadow-[0_0_15px_rgba(126,187,40,0.3)] disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isExporting ? "Exportando..." : "Generar Excel"}
          </button>
        </div>
      </div>
    </div>
  );
}
