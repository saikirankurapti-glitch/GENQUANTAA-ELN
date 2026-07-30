import React from 'react';
import type { IntegrationService, ViewMode } from '../../types';
import { Cloud, MessageSquare, Database, Cpu, Plus } from 'lucide-react';

interface IntegrationsViewProps {
  integrations: IntegrationService[];
  onToggleConnect: (id: string) => void;
  onSelectView: (view: ViewMode) => void;
}

export const IntegrationsView: React.FC<IntegrationsViewProps> = ({
  integrations,
  onToggleConnect
}) => {
  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
        <div>
          <h2 className="text-xl font-bold text-slate-800 tracking-tight">External Lab & Cloud Integrations</h2>
          <p className="text-xs text-slate-500">Connect third-party databases, cloud storage, communication tools, and lab hardware</p>
        </div>

        <button className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-4 py-2 rounded-lg shadow-sm transition-colors cursor-pointer">
          <Plus className="w-4 h-4" />
          <span>Add Custom API Webhook</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {integrations.map((item) => (
          <div key={item.id} className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm space-y-4 flex flex-col justify-between">
            <div>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
                    {item.icon === 'Cloud' && <Cloud className="w-5 h-5" />}
                    {item.icon === 'MessageSquare' && <MessageSquare className="w-5 h-5" />}
                    {item.icon === 'Database' && <Database className="w-5 h-5" />}
                    {item.icon === 'Cpu' && <Cpu className="w-5 h-5" />}
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-800 text-sm">{item.name}</h3>
                    <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">{item.category}</span>
                  </div>
                </div>

                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                  item.connected ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'
                }`}>
                  {item.connected ? 'Connected' : 'Disconnected'}
                </span>
              </div>

              <p className="text-xs text-slate-600 leading-relaxed mt-3">{item.description}</p>
            </div>

            <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
              <span className="text-xs text-slate-400 font-mono">API Status: Healthy</span>
              <button
                onClick={() => onToggleConnect(item.id)}
                className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
                  item.connected
                    ? 'bg-rose-50 text-rose-600 hover:bg-rose-100'
                    : 'bg-blue-600 text-white hover:bg-blue-700 shadow-sm'
                }`}
              >
                {item.connected ? 'Disconnect' : 'Connect API'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
