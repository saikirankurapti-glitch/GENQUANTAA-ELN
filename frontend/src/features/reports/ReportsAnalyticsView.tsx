import React from 'react';
import { 
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, PieChart, Pie, Cell, BarChart, Bar 
} from 'recharts';
import { Download } from 'lucide-react';

import { useAuth } from '../../providers/AuthProvider';
import { canExportExperiment } from '../../utils/permissions';

export const ReportsAnalyticsView: React.FC = () => {
  const { user } = useAuth();
  const allowExport = canExportExperiment(user);

  const lineData = [
    { month: 'Jan', experiments: 8, completed: 6 },
    { month: 'Feb', experiments: 12, completed: 9 },
    { month: 'Mar', experiments: 16, completed: 14 },
    { month: 'Apr', experiments: 20, completed: 17 },
    { month: 'May', experiments: 23, completed: 18 }
  ];

  const pieData = [
    { name: 'Completed', value: 12, color: '#10B981' },
    { name: 'In Progress', value: 6, color: '#2563EB' },
    { name: 'Under Review', value: 3, color: '#F59E0B' },
    { name: 'Draft', value: 2, color: '#64748B' }
  ];

  const barData = [
    { name: 'Cell Lines', count: 124 },
    { name: 'Plasmids', count: 88 },
    { name: 'Reagents', count: 65 },
    { name: 'Proteins', count: 45 },
    { name: 'Tissues', count: 20 }
  ];

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
        <div>
          <h2 className="text-xl font-bold text-slate-800 tracking-tight">Reports & Laboratory Analytics</h2>
          <p className="text-xs text-slate-500">Real-time telemetry on research throughput, protocol success rates, and sample usage</p>
        </div>

        {allowExport && (
          <button 
            onClick={() => window.print()}
            className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-4 py-2 rounded-lg shadow-sm transition-colors self-start sm:self-auto cursor-pointer"
          >
            <Download className="w-4 h-4" />
            <span>Export PDF Report</span>
          </button>
        )}
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Total Experiments</p>
          <p className="text-2xl font-bold text-slate-800 mt-1">23</p>
          <span className="text-xs font-semibold text-emerald-600 mt-1 inline-block">↑ 14% vs last month</span>
        </div>
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Completed Protocols</p>
          <p className="text-2xl font-bold text-emerald-600 mt-1">12</p>
          <span className="text-xs font-semibold text-emerald-600 mt-1 inline-block">84.2% Avg Efficiency</span>
        </div>
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Sample Inventory</p>
          <p className="text-2xl font-bold text-blue-600 mt-1">342</p>
          <span className="text-xs font-semibold text-slate-500 mt-1 inline-block">Across 4 Cryo Freezers</span>
        </div>
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Active Researchers</p>
          <p className="text-2xl font-bold text-indigo-600 mt-1">156</p>
          <span className="text-xs font-semibold text-indigo-600 mt-1 inline-block">Across 8 Lab Teams</span>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <h3 className="font-bold text-slate-800 text-sm">Experiments Output Over Time</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={lineData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="month" stroke="#94a3b8" fontSize={12} />
                <YAxis stroke="#94a3b8" fontSize={12} />
                <Tooltip />
                <Line type="monotone" dataKey="experiments" stroke="#2563eb" strokeWidth={3} name="Total Initiated" />
                <Line type="monotone" dataKey="completed" stroke="#10b981" strokeWidth={3} name="Completed" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <h3 className="font-bold text-slate-800 text-sm">Experiments by Status</h3>
          <div className="h-64 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center gap-4 text-xs font-medium">
            {pieData.map((item, idx) => (
              <div key={idx} className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }}></span>
                <span className="text-slate-700">{item.name} ({item.value})</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <h3 className="font-bold text-slate-800 text-sm">Sample Registry Inventory Distribution</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
              <YAxis stroke="#94a3b8" fontSize={12} />
              <Tooltip />
              <Bar dataKey="count" fill="#14b8a6" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
