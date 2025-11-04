'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { Upload, Database, Trash2, FileText, Calendar, HardDrive, Search, Filter, AlertCircle, CheckCircle, Clock, BookOpen, Eye } from 'lucide-react';
import { knowledgeBaseAPI, type KnowledgeBaseDocument } from '@/lib/api';

export default function KnowledgeBasePage() {
  // State management
  const [documents, setDocuments] = useState<KnowledgeBaseDocument[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [file, setFile] = useState<File | null>(null);
  const [documentType, setDocumentType] = useState('manual');
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [showStats, setShowStats] = useState(false);
  const [stats, setStats] = useState<any>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);

  // Refs
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropZoneRef = useRef<HTMLDivElement>(null);

  // Constants
  const DOCUMENT_TYPES = [
    { value: 'manual', label: 'Manual', icon: BookOpen, color: 'blue' },
    { value: 'specification', label: 'Especificación', icon: FileText, color: 'green' },
    { value: 'quality_manual', label: 'Manual de Calidad', icon: CheckCircle, color: 'purple' }
  ];

  // Load documents on mount
  useEffect(() => {
    loadDocuments();
    loadStats();
  }, []);

  // Load documents
  const loadDocuments = async () => {
    try {
      setIsLoading(true);
      const docs = await knowledgeBaseAPI.listDocuments();
      setDocuments(docs);
      setError(null);
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Error al cargar documentos';
      console.error('Failed to load documents:', errorMsg);
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  // Load statistics
  const loadStats = async () => {
    try {
      const statsData = await knowledgeBaseAPI.getStats();
      setStats(statsData);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  // File upload handlers
  const handleFileSelect = (file: File) => {
    if (file.type === 'application/pdf') {
      setFile(file);
    } else {
      setError('Por favor, sube solo archivos PDF.');
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  // Upload document
  const handleUpload = async () => {
    if (!file) return;
    
    setIsUploading(true);
    setError(null);
    setSuccess(null);

    try {
      await knowledgeBaseAPI.uploadDocument(file, documentType);
      setFile(null);
      setSuccess(`Documento "${file.name}" subido exitosamente`);
      await loadDocuments();
      await loadStats();
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Error al subir documento';
      console.error('Upload failed:', errorMsg);
      setError(errorMsg);
    } finally {
      setIsUploading(false);
    }
  };

  // Delete document
  const handleDelete = async (docId: string, filename: string) => {
    if (!confirm(`¿Estás seguro de que quieres eliminar "${filename}"?`)) return;
    
    setError(null);
    setSuccess(null);

    try {
      await knowledgeBaseAPI.deleteDocument(docId);
      setSuccess(`Documento "${filename}" eliminado exitosamente`);
      await loadDocuments();
      await loadStats();
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Error al eliminar documento';
      console.error('Delete failed:', errorMsg);
      setError(errorMsg);
    }
  };

  // Filter documents
  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = doc.filename.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterType === 'all' || doc.document_type === filterType;
    return matchesSearch && matchesFilter;
  });

  // Get document type info
  const getDocumentTypeInfo = (type: string) => {
    return DOCUMENT_TYPES.find(dt => dt.value === type) || DOCUMENT_TYPES[0];
  };

  // Format file size
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className={`h-screen flex ${isDarkMode ? 'dark' : ''}`}>
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} fixed inset-y-0 left-0 z-50 w-80 bg-white dark:bg-gray-900 shadow-xl transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0`}>
        <div className="flex items-center justify-between h-16 px-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Gestión KB</h2>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-2 rounded-md text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            ✕
          </button>
        </div>
        <div className="p-4 space-y-4">
          {/* Navigation Links */}
          <div className="space-y-2">
            <Link href="/" className="flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300">
              <Upload className="w-5 h-5" />
              <span className="font-medium">Análisis de Dibujos</span>
            </Link>
            <Link href="/knowledge-base" className="flex items-center space-x-3 p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300">
              <Database className="w-5 h-5" />
              <span className="font-medium">Base de Conocimiento</span>
            </Link>
          </div>
          
          {/* Statistics */}
          {stats && (
            <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
              <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-3">Estadísticas</h3>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-400">Total documentos</span>
                  <span className="font-medium text-gray-900 dark:text-white">{stats.total_documents}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-400">Páginas indexadas</span>
                  <span className="font-medium text-gray-900 dark:text-white">{stats.total_pages_indexed || 0}</span>
                </div>
              </div>
            </div>
          )}
          
          {/* Document Types */}
          <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
            <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-3">Tipos de Documentos</h3>
            <div className="space-y-2">
              {DOCUMENT_TYPES.map((type) => {
                const IconComponent = type.icon;
                const count = stats?.documents_by_type?.[type.value] || 0;
                return (
                  <div key={type.value} className="flex items-center justify-between text-sm">
                    <div className="flex items-center space-x-2">
                      <IconComponent className={`w-4 h-4 text-${type.color}-500`} />
                      <span className="text-gray-600 dark:text-gray-400">{type.label}</span>
                    </div>
                    <span className="font-medium text-gray-900 dark:text-white">{count}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="h-16 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-6">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 rounded-md text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              <Database className="w-5 h-5" />
            </button>
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-green-500 to-blue-600 rounded-lg flex items-center justify-center">
                <Database className="w-4 h-4 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-white">Knowledge Base</h1>
                <p className="text-xs text-gray-500 dark:text-gray-400">Gestión de Documentos Técnicos</p>
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowStats(!showStats)}
              className="p-2 rounded-md text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              <Eye className="w-5 h-5" />
            </button>
            <button
              onClick={() => setIsDarkMode(!isDarkMode)}
              className="p-2 rounded-md text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              <Filter className="w-5 h-5" />
            </button>
          </div>
        </header>

        {/* Content */}
        <div className="flex-1 overflow-hidden bg-gray-50 dark:bg-gray-800">
          <div className="h-full overflow-y-auto p-6">
            <div className="max-w-7xl mx-auto space-y-6">
              
              {/* Notifications */}
              {error && (
                <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 px-4 py-3 rounded-lg animate-fade-in">
                  <div className="flex items-center space-x-2">
                    <AlertCircle className="w-5 h-5" />
                    <strong>Error:</strong> {error}
                  </div>
                </div>
              )}
              
              {success && (
                <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-300 px-4 py-3 rounded-lg animate-fade-in">
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="w-5 h-5" />
                    <strong>Éxito:</strong> {success}
                  </div>
                </div>
              )}

              {/* Upload Section */}
              <div className="bg-white dark:bg-gray-900 rounded-xl shadow-md p-6">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center space-x-2">
                  <Upload className="w-5 h-5 text-blue-500" />
                  <span>Subir Documento</span>
                </h2>
                
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                  <div className="lg:col-span-2">
                    <div
                      ref={dropZoneRef}
                      className="upload-area cursor-pointer"
                      onDrop={handleDrop}
                      onDragOver={handleDragOver}
                      onClick={() => fileInputRef.current?.click()}
                    >
                      <div className="flex flex-col items-center space-y-3">
                        <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                          <Upload className="w-6 h-6 text-white" />
                        </div>
                        <div className="text-center">
                          <p className="text-sm font-medium text-gray-900 dark:text-white">
                            {file ? file.name : 'Arrastra y suelta tu PDF aquí'}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            o haz clic para seleccionar archivo
                          </p>
                        </div>
                      </div>
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept=".pdf"
                        className="hidden"
                        onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
                      />
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Tipo de Documento
                      </label>
                      <select
                        value={documentType}
                        onChange={(e) => setDocumentType(e.target.value)}
                        className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-800 dark:text-white"
                      >
                        {DOCUMENT_TYPES.map((type) => (
                          <option key={type.value} value={type.value}>
                            {type.label}
                          </option>
                        ))}
                      </select>
                    </div>
                    
                    <button
                      onClick={handleUpload}
                      disabled={!file || isUploading}
                      className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isUploading ? (
                        <>
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                          Subiendo...
                        </>
                      ) : (
                        <>
                          <Upload className="w-4 h-4 mr-2" />
                          Subir Documento
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>

              {/* Filters and Search */}
              <div className="bg-white dark:bg-gray-900 rounded-xl shadow-md p-6">
                <div className="flex flex-col sm:flex-row gap-4">
                  <div className="flex-1">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                      <input
                        type="text"
                        placeholder="Buscar documentos..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-800 dark:text-white"
                      />
                    </div>
                  </div>
                  
                  <div className="sm:w-48">
                    <select
                      value={filterType}
                      onChange={(e) => setFilterType(e.target.value)}
                      className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-800 dark:text-white"
                    >
                      <option value="all">Todos los tipos</option>
                      {DOCUMENT_TYPES.map((type) => (
                        <option key={type.value} value={type.value}>
                          {type.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              {/* Documents List */}
              <div className="bg-white dark:bg-gray-900 rounded-xl shadow-md p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center space-x-2">
                    <Database className="w-5 h-5 text-blue-500" />
                    <span>Documentos ({filteredDocuments.length})</span>
                  </h2>
                  <button
                    onClick={loadDocuments}
                    disabled={isLoading}
                    className="btn-secondary"
                  >
                    <Database className="w-4 h-4 mr-2" />
                    Actualizar
                  </button>
                </div>
                
                {isLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                    <span className="ml-3 text-gray-600 dark:text-gray-400">Cargando documentos...</span>
                  </div>
                ) : filteredDocuments.length === 0 ? (
                  <div className="text-center py-12">
                    <Database className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                      {searchTerm || filterType !== 'all' ? 'No se encontraron documentos' : 'No hay documentos'}
                    </h3>
                    <p className="text-gray-500 dark:text-gray-400">
                      {searchTerm || filterType !== 'all' 
                        ? 'Intenta ajustar los filtros de búsqueda' 
                        : '¡Sube tu primer documento para empezar!'
                      }
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {filteredDocuments.map((doc) => {
                      const typeInfo = getDocumentTypeInfo(doc.document_type);
                      const IconComponent = typeInfo.icon;
                      
                      return (
                        <div
                          key={doc.document_id}
                          className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:shadow-md transition-shadow animate-fade-in"
                        >
                          <div className="flex items-center space-x-4">
                            <div className={`w-10 h-10 bg-${typeInfo.color}-100 dark:bg-${typeInfo.color}-900/20 rounded-lg flex items-center justify-center`}>
                              <IconComponent className={`w-5 h-5 text-${typeInfo.color}-600 dark:text-${typeInfo.color}-400`} />
                            </div>
                            
                            <div>
                              <h3 className="font-semibold text-gray-900 dark:text-white">
                                {doc.filename}
                              </h3>
                              <div className="flex items-center space-x-4 text-sm text-gray-500 dark:text-gray-400">
                                <span className="flex items-center space-x-1">
                                  <FileText className="w-4 h-4" />
                                  <span>{typeInfo.label}</span>
                                </span>
                                <span className="flex items-center space-x-1">
                                  <HardDrive className="w-4 h-4" />
                                  <span>{formatFileSize(doc.file_size)}</span>
                                </span>
                                <span className="flex items-center space-x-1">
                                  <Calendar className="w-4 h-4" />
                                  <span>{new Date(doc.upload_date).toLocaleDateString()}</span>
                                </span>
                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                  doc.status === 'indexed' 
                                    ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                                    : doc.status === 'processing'
                                    ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400'
                                    : 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
                                }`}>
                                  {doc.status === 'indexed' ? 'Indexado' : 
                                   doc.status === 'processing' ? 'Procesando' : 'Error'}
                                </span>
                              </div>
                            </div>
                          </div>
                          
                          <button
                            onClick={() => handleDelete(doc.document_id, doc.filename)}
                            className="p-2 text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                            title="Eliminar documento"
                          >
                            <Trash2 className="w-5 h-5" />
                          </button>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Overlay for mobile sidebar */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
}
