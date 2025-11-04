'use client';

import { useState } from 'react';
import { analysisAPI } from '@/lib/api';
import Link from 'next/link';

export default function AnalyzePage() {
  const [file, setFile] = useState<File | null>(null);
  const [projectName, setProjectName] = useState('');
  const [qualityMode, setQualityMode] = useState<'flash' | 'pro'>('flash');
  const [isUploading, setIsUploading] = useState(false);
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file');
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      const result = await analysisAPI.uploadDrawing(
        file,
        projectName || undefined,
        qualityMode
      );

      setAnalysisId(result.analysis_id);
    } catch (err: any) {
      setError(err.message || 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <header className="bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center space-x-4">
            <Link href="/" className="text-blue-600 hover:text-blue-700">
              ← Back to Dashboard
            </Link>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Analyze Drawing
            </h1>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {!analysisId ? (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-8">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
              Upload Technical Drawing
            </h2>

            {/* File Upload */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Drawing File (PDF)
              </label>
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileSelect}
                className="block w-full text-sm text-gray-900 dark:text-gray-100 border border-gray-300 dark:border-gray-600 rounded-lg cursor-pointer bg-gray-50 dark:bg-gray-700 focus:outline-none p-2"
              />
              {file && (
                <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                  Selected: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                </p>
              )}
            </div>

            {/* Project Name */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Project Name (Optional)
              </label>
              <input
                type="text"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                placeholder="e.g., Gen6 Housing"
                className="block w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* Quality Mode */}
            <div className="mb-8">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Quality Mode
              </label>
              <div className="grid grid-cols-2 gap-4">
                <button
                  onClick={() => setQualityMode('flash')}
                  className={`p-4 border-2 rounded-lg transition-all ${
                    qualityMode === 'flash'
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-300 dark:border-gray-600'
                  }`}
                >
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                    Flash (Recommended)
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-300">
                    Fast & accurate (~20s, $0.10)
                  </p>
                </button>
                <button
                  onClick={() => setQualityMode('pro')}
                  className={`p-4 border-2 rounded-lg transition-all ${
                    qualityMode === 'pro'
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-300 dark:border-gray-600'
                  }`}
                >
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                    Pro (High Precision)
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-300">
                    Maximum accuracy (~60s, $0.50)
                  </p>
                </button>
              </div>
            </div>

            {/* Error */}
            {error && (
              <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
              </div>
            )}

            {/* Upload Button */}
            <button
              onClick={handleUpload}
              disabled={!file || isUploading}
              className="w-full bg-gradient-to-r from-blue-500 to-indigo-600 text-white font-semibold py-3 px-6 rounded-lg hover:from-blue-600 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {isUploading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin h-5 w-5 mr-3" viewBox="0 0 24 24">
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Uploading & Analyzing...
                </span>
              ) : (
                'Start Analysis'
              )}
            </button>
          </div>
        ) : (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-8 text-center">
            <div className="w-16 h-16 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg className="w-8 h-8 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
              Analysis Started!
            </h2>
            <p className="text-gray-600 dark:text-gray-300 mb-8">
              Your drawing is being analyzed. This typically takes 20-60 seconds.
            </p>
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 mb-8">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Analysis ID:</p>
              <p className="font-mono text-lg text-gray-900 dark:text-white">{analysisId}</p>
            </div>
            <div className="space-y-3">
              <Link
                href={`/results?id=${analysisId}`}
                className="block w-full bg-gradient-to-r from-blue-500 to-indigo-600 text-white font-semibold py-3 px-6 rounded-lg hover:from-blue-600 hover:to-indigo-700 transition-all"
              >
                View Results
              </Link>
              <button
                onClick={() => {
                  setAnalysisId(null);
                  setFile(null);
                  setProjectName('');
                  setError(null);
                }}
                className="block w-full bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white font-semibold py-3 px-6 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-all"
              >
                Analyze Another Drawing
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
