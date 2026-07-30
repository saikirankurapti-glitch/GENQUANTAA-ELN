import React from 'react';
import type { FileItem, ViewMode } from '../../types';
import { FileText, Image, FileSpreadsheet, Download, Upload } from 'lucide-react';

interface FileManagerViewProps {
  files: FileItem[];
  onSelectView: (view: ViewMode) => void;
}

export const FileManagerView: React.FC<FileManagerViewProps> = ({ files }) => {
  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
        <div>
          <h2 className="text-xl font-bold text-slate-800 tracking-tight">File Manager Repository</h2>
          <p className="text-xs text-slate-500">Central storage for raw instrument data, FASTQ, PDFs, and exported protocols</p>
        </div>

        <button className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-4 py-2 rounded-lg shadow-sm transition-colors cursor-pointer">
          <Upload className="w-4 h-4" />
          <span>Upload Raw Data File</span>
        </button>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">File Name</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Size</th>
                <th className="py-3 px-4">Owner</th>
                <th className="py-3 px-4">Modified Date</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {files.map((file) => (
                <tr key={file.id} className="hover:bg-slate-50 transition-colors">
                  <td className="py-3.5 px-4 font-bold text-slate-800 flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
                      {file.type === 'Image' && <Image className="w-4 h-4" />}
                      {file.type === 'FASTA' && <FileText className="w-4 h-4" />}
                      {file.type === 'PDF' && <FileText className="w-4 h-4 text-rose-600" />}
                      {file.type === 'CSV' && <FileSpreadsheet className="w-4 h-4 text-emerald-600" />}
                    </div>
                    <span>{file.name}</span>
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="bg-slate-100 text-slate-700 font-semibold px-2 py-0.5 rounded text-[10px]">
                      {file.type}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-slate-600 font-mono">{file.size}</td>
                  <td className="py-3.5 px-4 text-slate-700">{file.owner}</td>
                  <td className="py-3.5 px-4 text-slate-500">{file.modifiedDate}</td>
                  <td className="py-3.5 px-4 text-right">
                    <button className="text-xs font-semibold text-blue-600 hover:text-blue-700 p-1 cursor-pointer">
                      <Download className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
