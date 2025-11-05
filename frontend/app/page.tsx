'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Send,
  Paperclip,
  FileText,
  Upload,
  Brain,
  MessageCircle,
  Database,
  Menu,
  Settings,
  Sparkles,
  Sun,
  Moon,
  Loader2,
  X,
  Check
} from 'lucide-react';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  type: 'text' | 'pdf_analysis' | 'error';
  sources?: Array<{ title: string; uri?: string; type?: string }>;
  attachments?: Array<{
    name: string;
    size: number;
    type: string;
  }>;
}

interface UploadingFile {
  file: File;
  progress: number;
  status: 'uploading' | 'processing' | 'analyzing' | 'completed' | 'error';
}

export default function UnifiedChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([]);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [inputValue]);

  useEffect(() => {
    if (messages.length === 0) {
      const welcomeMessage: ChatMessage = {
        id: 'welcome',
        role: 'assistant',
        content: `¡Hola! 👋 Soy tu experto en moldeo por inyección con IA.

**Puedo ayudarte con:**

📄 **Análisis de planos técnicos** - Sube PDFs y analizo dimensiones, tolerancias y viabilidad basándome en mejores prácticas

💡 **Preguntas sobre diseño** - Resuelvo dudas sobre geometría, materiales y procesos

🎯 **Recomendaciones técnicas** - Fundamentadas en nuestra base de conocimiento especializada

**¿En qué puedo ayudarte hoy?** Puedes subir un plano técnico o hacerme cualquier pregunta sobre moldeo por inyección.`,
        timestamp: new Date(),
        type: 'text'
      };
      setMessages([welcomeMessage]);
    }
  }, []);

  const handleFileUpload = async (files: FileList) => {
    const file = files[0];

    if (!file || file.type !== 'application/pdf') {
      alert('Por favor, selecciona un archivo PDF válido.');
      return;
    }

    const uploadingFile: UploadingFile = {
      file,
      progress: 0,
      status: 'uploading'
    };
    setUploadingFiles(prev => [...prev, uploadingFile]);

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: inputValue || `Analiza este plano: ${file.name}`,
      timestamp: new Date(),
      type: 'text',
      attachments: [{
        name: file.name,
        size: file.size,
        type: file.type
      }]
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');

    await processFileInChat(file, uploadingFile);
  };

  const processFileInChat = async (file: File, uploadingFile: UploadingFile) => {
    try {
      setUploadingFiles(prev =>
        prev.map(f => f === uploadingFile ? { ...f, status: 'processing', progress: 30 } : f)
      );

      const formData = new FormData();
      formData.append('file', file);
      formData.append('message', 'Analiza este plano técnico en detalle');
      formData.append('chat_history', JSON.stringify(messages.slice(-10)));

      setIsTyping(true);

      const response = await fetch(`${API_BASE_URL}/analysis/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Error en el análisis');
      }

      setUploadingFiles(prev =>
        prev.map(f => f === uploadingFile ? { ...f, status: 'analyzing', progress: 70 } : f)
      );

      const result = await response.json();

      console.log('✅ Backend response:', result);

      setUploadingFiles(prev =>
        prev.map(f => f === uploadingFile ? { ...f, status: 'completed', progress: 100 } : f)
      );

      const aiMessage: ChatMessage = {
        id: `ai-${Date.now()}`,
        role: 'assistant',
        content: result.message || result.response || 'No response from AI',
        timestamp: new Date(),
        type: 'pdf_analysis',
        sources: result.sources || []
      };

      setMessages(prev => [...prev, aiMessage]);

      setTimeout(() => {
        setUploadingFiles(prev => prev.filter(f => f !== uploadingFile));
      }, 2000);

    } catch (error) {
      console.error('Upload error:', error);

      setUploadingFiles(prev =>
        prev.map(f => f === uploadingFile ? { ...f, status: 'error', progress: 0 } : f)
      );

      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'Lo siento, hubo un error al analizar el archivo. Por favor, intenta de nuevo.',
        timestamp: new Date(),
        type: 'error'
      };

      setMessages(prev => [...prev, errorMessage]);

      setTimeout(() => {
        setUploadingFiles(prev => prev.filter(f => f !== uploadingFile));
      }, 3000);
    } finally {
      setIsTyping(false);
    }
  };

  const sendTextMessage = async () => {
    if (!inputValue.trim() || isTyping) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: inputValue,
      timestamp: new Date(),
      type: 'text'
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    try {
      const response = await fetch(`${API_BASE_URL}/analysis/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputValue,
          chat_history: messages.slice(-10).map(msg => ({
            role: msg.role,
            content: msg.content
          }))
        }),
      });

      if (!response.ok) {
        throw new Error('Error en el chat');
      }

      const result = await response.json();

      console.log('✅ Text chat response:', result);

      const aiMessage: ChatMessage = {
        id: `ai-${Date.now()}`,
        role: 'assistant',
        content: result.message || result.response || 'No response from AI',
        timestamp: new Date(),
        type: 'text',
        sources: result.sources || []
      };

      setMessages(prev => [...prev, aiMessage]);

    } catch (error) {
      console.error('Chat error:', error);

      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'Lo siento, hubo un error al procesar tu mensaje. Por favor, intenta de nuevo.',
        timestamp: new Date(),
        type: 'error'
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendTextMessage();
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileUpload(files);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className={`h-screen flex overflow-hidden ${isDarkMode ? 'dark' : ''}`}>
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} fixed inset-y-0 left-0 z-50 w-80 bg-white/70 dark:bg-gray-900/70 backdrop-blur-xl border-r border-gray-200/50 dark:border-gray-700/50 shadow-2xl transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0`}>
        {/* Sidebar Header */}
        <div className="flex items-center justify-between h-16 px-6 border-b border-gray-200/50 dark:border-gray-700/50">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <h2 className="text-lg font-semibold bg-gradient-to-r from-gray-900 to-gray-600 dark:from-white dark:to-gray-300 bg-clip-text text-transparent">
              SME AI
            </h2>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-4 space-y-4 overflow-y-auto h-[calc(100vh-4rem)]">
          {/* Navigation Links */}
          <div className="space-y-2">
            <Link
              href="/"
              className="flex items-center space-x-3 p-3 rounded-xl bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-200/50 dark:border-blue-800/50 text-blue-700 dark:text-blue-300"
            >
              <MessageCircle className="w-5 h-5" />
              <span className="font-medium">Chat AI</span>
              <Sparkles className="w-4 h-4 ml-auto" />
            </Link>

            <Link
              href="/knowledge-base"
              className="flex items-center space-x-3 p-3 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 transition-all"
            >
              <Database className="w-5 h-5" />
              <span className="font-medium">Base de Conocimiento</span>
            </Link>

            <Link
              href="/config"
              className="flex items-center space-x-3 p-3 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 transition-all"
            >
              <Settings className="w-5 h-5" />
              <span className="font-medium">Configuración</span>
            </Link>
          </div>

          {/* Quick Actions */}
          <div className="border-t border-gray-200/50 dark:border-gray-700/50 pt-4">
            <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-3 px-2">
              Acciones Rápidas
            </h3>
            <div className="space-y-2">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="w-full flex items-center space-x-3 p-3 rounded-xl hover:bg-gradient-to-r hover:from-green-50 hover:to-emerald-50 dark:hover:from-green-900/20 dark:hover:to-emerald-900/20 text-gray-700 dark:text-gray-300 transition-all group"
              >
                <Upload className="w-5 h-5 text-green-500 group-hover:scale-110 transition-transform" />
                <span className="font-medium">Subir Plano</span>
              </button>

              <button
                onClick={() => {
                  setMessages([]);
                  setTimeout(() => {
                    const welcomeMessage: ChatMessage = {
                      id: 'welcome',
                      role: 'assistant',
                      content: `¡Hola! 👋 Soy tu experto en moldeo por inyección con IA.\n\n¿En qué puedo ayudarte hoy?`,
                      timestamp: new Date(),
                      type: 'text'
                    };
                    setMessages([welcomeMessage]);
                  }, 100);
                }}
                className="w-full flex items-center space-x-3 p-3 rounded-xl hover:bg-gradient-to-r hover:from-blue-50 hover:to-cyan-50 dark:hover:from-blue-900/20 dark:hover:to-cyan-900/20 text-gray-700 dark:text-gray-300 transition-all group"
              >
                <MessageCircle className="w-5 h-5 text-blue-500 group-hover:scale-110 transition-transform" />
                <span className="font-medium">Nuevo Chat</span>
              </button>
            </div>
          </div>

          {/* Chat Stats */}
          <div className="border-t border-gray-200/50 dark:border-gray-700/50 pt-4">
            <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-3 px-2">
              Estado del Chat
            </h3>
            <div className="bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-900 rounded-xl p-4 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">Mensajes</span>
                <span className="font-semibold text-gray-900 dark:text-white">{messages.length}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">Subidas activas</span>
                <span className="font-semibold text-gray-900 dark:text-white">{uploadingFiles.length}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 bg-gradient-to-br from-gray-50 via-blue-50/20 to-purple-50/20 dark:from-gray-900 dark:via-blue-900/10 dark:to-purple-900/10">
        {/* Header */}
        <header className="h-16 bg-white/70 dark:bg-gray-900/70 backdrop-blur-xl border-b border-gray-200/50 dark:border-gray-700/50 flex items-center justify-between px-6 flex-shrink-0">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            >
              <Menu className="w-5 h-5" />
            </button>

            <div className="flex items-center space-x-3">
              <div className="p-2 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 shadow-lg">
                <Brain className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 dark:from-white dark:to-gray-300 bg-clip-text text-transparent">
                  SME AI Chat
                </h1>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Experto en Moldeo por Inyección
                </p>
              </div>
            </div>
          </div>

          <button
            onClick={() => setIsDarkMode(!isDarkMode)}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            title="Cambiar tema"
          >
            {isDarkMode ? (
              <Sun className="w-5 h-5 text-yellow-500" />
            ) : (
              <Moon className="w-5 h-5 text-gray-600" />
            )}
          </button>
        </header>

        {/* Messages Area */}
        <div
          className="flex-1 overflow-y-auto p-4"
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
        >
          {dragActive && (
            <div className="fixed inset-0 z-40 bg-blue-500/20 dark:bg-blue-500/30 backdrop-blur-sm flex items-center justify-center">
              <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-2xl border-2 border-dashed border-blue-500">
                <Upload className="w-16 h-16 text-blue-500 mx-auto mb-4" />
                <p className="text-xl font-semibold text-gray-900 dark:text-white">
                  Suelta el PDF aquí
                </p>
              </div>
            </div>
          )}

          <div className="max-w-4xl mx-auto space-y-6">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-4 duration-500`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-6 py-4 ${
                    message.role === 'user'
                      ? 'bg-gradient-to-br from-blue-500 to-purple-600 text-white shadow-lg'
                      : message.type === 'error'
                      ? 'bg-red-50 dark:bg-red-900/20 text-red-900 dark:text-red-100 border border-red-200 dark:border-red-800'
                      : 'bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl text-gray-900 dark:text-white border border-gray-200/50 dark:border-gray-700/50 shadow-lg'
                  }`}
                >
                  {/* Attachments */}
                  {message.attachments && message.attachments.length > 0 && (
                    <div className="mb-3 space-y-2">
                      {message.attachments.map((file, index) => (
                        <div
                          key={index}
                          className="flex items-center space-x-2 text-sm bg-white/20 dark:bg-black/20 rounded-lg p-2 backdrop-blur-sm"
                        >
                          <FileText className="w-4 h-4 flex-shrink-0" />
                          <span className="font-medium truncate">{file.name}</span>
                          <span className="text-xs opacity-75">({formatFileSize(file.size)})</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Content */}
                  <div className="prose prose-sm dark:prose-invert max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {message.content}
                    </ReactMarkdown>
                  </div>

                  {/* Sources */}
                  {message.sources && message.sources.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-gray-200/30 dark:border-gray-600/30">
                      <p className="text-xs font-semibold opacity-75 mb-2">📚 Fuentes:</p>
                      <div className="space-y-1">
                        {message.sources.map((source, index) => (
                          <div
                            key={index}
                            className="text-xs bg-white/20 dark:bg-black/20 rounded-lg px-3 py-2 backdrop-blur-sm flex items-center space-x-2"
                          >
                            {source.type === 'uploaded_pdf' ? (
                              <FileText className="w-3 h-3 flex-shrink-0" />
                            ) : (
                              <Brain className="w-3 h-3 flex-shrink-0" />
                            )}
                            <span className="truncate">{source.title}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Timestamp */}
                  <div className="text-xs opacity-60 mt-3">
                    {message.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}

            {/* Typing Indicator */}
            {isTyping && (
              <div className="flex justify-start animate-in fade-in slide-in-from-bottom-4">
                <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl border border-gray-200/50 dark:border-gray-700/50 rounded-2xl px-6 py-4 shadow-lg">
                  <div className="flex items-center space-x-3">
                    <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
                    <span className="text-sm text-gray-600 dark:text-gray-300">
                      Analizando...
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Uploading Files */}
            {uploadingFiles.map((uploadingFile, index) => (
              <div key={index} className="flex justify-start animate-in fade-in slide-in-from-bottom-4">
                <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl border border-gray-200/50 dark:border-gray-700/50 rounded-2xl px-6 py-4 w-full max-w-md shadow-lg">
                  <div className="flex items-center space-x-3 mb-3">
                    {uploadingFile.status === 'completed' ? (
                      <Check className="w-5 h-5 text-green-500" />
                    ) : (
                      <Upload className="w-5 h-5 text-blue-500 animate-pulse" />
                    )}
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {uploadingFile.file.name}
                    </p>
                  </div>

                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-2 rounded-full transition-all duration-300 ${
                        uploadingFile.status === 'error'
                          ? 'bg-red-500'
                          : 'bg-gradient-to-r from-blue-500 to-purple-600'
                      }`}
                      style={{ width: `${uploadingFile.progress}%` }}
                    ></div>
                  </div>

                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                    {uploadingFile.status === 'uploading' && '📤 Subiendo...'}
                    {uploadingFile.status === 'processing' && '⚙️ Procesando...'}
                    {uploadingFile.status === 'analyzing' && '🧠 Analizando con IA...'}
                    {uploadingFile.status === 'completed' && '✅ Completado'}
                    {uploadingFile.status === 'error' && '❌ Error'}
                  </p>
                </div>
              </div>
            ))}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-200/50 dark:border-gray-700/50 p-4 bg-white/50 dark:bg-gray-900/50 backdrop-blur-xl flex-shrink-0">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-end space-x-3 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-2xl p-4 shadow-lg focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500 transition-all">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="p-2 text-gray-500 hover:text-blue-500 dark:text-gray-400 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-all"
                title="Adjuntar archivo"
              >
                <Paperclip className="w-5 h-5" />
              </button>

              <textarea
                ref={textareaRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Escribe tu mensaje... (arrastra PDFs aquí)"
                className="flex-1 bg-transparent border-none resize-none focus:outline-none text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 max-h-32"
                rows={1}
              />

              <button
                onClick={sendTextMessage}
                disabled={!inputValue.trim() || isTyping}
                className="p-2 text-blue-500 hover:text-blue-600 disabled:text-gray-400 disabled:cursor-not-allowed hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-all disabled:hover:bg-transparent"
                title="Enviar mensaje"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>

            <div className="mt-2 text-xs text-gray-500 dark:text-gray-400 text-center">
              <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded">Enter</kbd> para enviar •{' '}
              <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded">Shift+Enter</kbd> para nueva línea •
              Arrastra PDFs para análisis
            </div>
          </div>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files)}
        />
      </div>

      {/* Mobile Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
}
