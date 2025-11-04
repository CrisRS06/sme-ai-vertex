'use client';

import { useState, useEffect } from 'react';
import { analysisAPI, type AnalysisInfo } from '@/lib/api';
import Link from 'next/link';

export default function ResultsPage() {
  const [analyses, setAnalyses] = useState<AnalysisInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadAnalyses();
  }, []);

  const loadAnalyses = async () => {
    try {
      const data = await analysisAPI.listAnalyses();
      setAnalyses(data);
    } catch (error) {
      console.error('Failed to load analyses:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <header className="bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center space-x-4">
            <Link href="/" className="text-blue-600 hover:text-blue-700">← Back</Link>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Analysis Results</h1>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-8">
          <h2 className="text-xl font-bold mb-6">All Analyses ({analyses.length})</h2>
          {isLoading ? (
            <p>Loading...</p>
          ) : analyses.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500 mb-4">No analyses yet. Upload your first drawing!</p>
              <Link href="/analyze" className="inline-block bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700">
                Start Analysis
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {analyses.map((analysis) => (
                <div key={analysis.analysis_id} className="border dark:border-gray-700 rounded-lg p-6 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-semibold text-lg text-gray-900 dark:text-white mb-2">
                        {analysis.drawing_filename}
                      </h3>
                      {analysis.project_name && (
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                          Project: {analysis.project_name}
                        </p>
                      )}
                      <div className="flex items-center space-x-4 text-sm text-gray-500">
                        <span className={`px-2 py-1 rounded ${
                          analysis.status === 'completed' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' :
                          analysis.status === 'processing' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' :
                          'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                        }`}>
                          {analysis.status}
                        </span>
                        <span>{analysis.quality_mode}</span>
                        {analysis.exception_count !== undefined && (
                          <span className="font-semibold text-red-600 dark:text-red-400">
                            {analysis.exception_count} exceptions
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="text-right text-sm text-gray-500">
                      <p>{new Date(analysis.created_at).toLocaleDateString()}</p>
                      <p>{new Date(analysis.created_at).toLocaleTimeString()}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
