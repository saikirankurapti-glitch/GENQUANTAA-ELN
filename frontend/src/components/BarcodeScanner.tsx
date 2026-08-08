import React, { useEffect, useRef, useState } from 'react';
import { BrowserMultiFormatReader, IScannerControls } from '@zxing/browser';
import { X, Camera, ScanLine } from 'lucide-react';

interface BarcodeScannerProps {
  onResult: (decodedText: string) => void;
  onClose: () => void;
}

export const BarcodeScanner: React.FC<BarcodeScannerProps> = ({ onResult, onClose }) => {
  const [error, setError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const controlsRef = useRef<IScannerControls | null>(null);
  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;
    const codeReader = new BrowserMultiFormatReader();
    let isDecoding = false;

    const startCamera = async () => {
      try {
        if (!videoRef.current) return;
        
        // This gives us complete, low-level control over the camera stream
        controlsRef.current = await codeReader.decodeFromVideoDevice(
          undefined, // undefined picks the default rear/environment camera
          videoRef.current,
          (result, error, controls) => {
            if (isMounted.current && result && !isDecoding) {
              isDecoding = true;
              // Stop the camera as soon as we have a valid result
              controls.stop();
              onResult(result.getText());
            }
          }
        );
      } catch (err) {
        if (isMounted.current) {
          console.error('Failed to start camera:', err);
          setError("Failed to access camera. Please allow permissions.");
        }
      }
    };

    startCamera();

    return () => {
      isMounted.current = false;
      if (controlsRef.current) {
        controlsRef.current.stop();
      }
    };
  }, [onResult]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
      <div className="bg-white rounded-2xl w-full max-w-md shadow-2xl overflow-hidden flex flex-col transform transition-all">
        
        {/* Header */}
        <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
          <div className="flex items-center gap-2 text-slate-800 font-bold tracking-tight">
            <ScanLine className="w-5 h-5 text-purple-600" />
            <span>Scanning Target...</span>
          </div>
          <button 
            onClick={() => {
              if (controlsRef.current) {
                controlsRef.current.stop();
              }
              onClose();
            }}
            className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-200 rounded-full transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        {/* Scanner Body */}
        <div className="p-6 flex flex-col items-center bg-slate-50">
          {error ? (
            <div className="text-center text-rose-500 font-medium py-8">{error}</div>
          ) : (
            <div className="w-full relative flex items-center justify-center bg-black rounded-xl overflow-hidden shadow-inner ring-4 ring-slate-900/5 aspect-[4/3]">
              
              {/* The raw video element (controlled purely by React) */}
              <video 
                ref={videoRef} 
                className="w-full h-full object-cover" 
                muted 
                playsInline
              />

              {/* Targeting Reticle overlay */}
              <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
                <div className="w-48 h-48 border-2 border-white/50 rounded-lg relative">
                  <div className="absolute top-0 left-0 w-4 h-4 border-t-4 border-l-4 border-purple-500 rounded-tl"></div>
                  <div className="absolute top-0 right-0 w-4 h-4 border-t-4 border-r-4 border-purple-500 rounded-tr"></div>
                  <div className="absolute bottom-0 left-0 w-4 h-4 border-b-4 border-l-4 border-purple-500 rounded-bl"></div>
                  <div className="absolute bottom-0 right-0 w-4 h-4 border-b-4 border-r-4 border-purple-500 rounded-br"></div>
                </div>
              </div>

              {/* Animated scan line */}
              <div className="absolute top-0 left-0 w-full h-1 bg-purple-500/80 shadow-[0_0_15px_rgba(168,85,247,1)] animate-[scan_2s_ease-in-out_infinite] z-10 pointer-events-none"></div>
              
              {/* Demo Fallback Button */}
              <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity z-20">
                <button 
                  onClick={() => {
                    if (controlsRef.current) controlsRef.current.stop();
                    onResult('SEQ-B90371EF');
                  }}
                  className="bg-white/20 hover:bg-white/30 backdrop-blur-md text-white font-semibold py-2.5 px-5 rounded-lg border border-white/30 transition-colors shadow-xl flex items-center gap-2"
                >
                  <Camera className="w-4 h-4" /> Override Scan
                </button>
              </div>
            </div>
          )}
          
          <div className="mt-5 text-center space-y-1">
            <p className="text-sm font-semibold text-slate-700">Point at a QR Code</p>
            <p className="text-xs text-slate-500 leading-relaxed font-medium px-4">
              Align the code inside the purple corners. Ensure there is a white border visible around the code.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
