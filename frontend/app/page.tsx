'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Send, Paperclip, X, FileText, Upload, Brain, MessageCircle, Database, Menu } from 'lucide-react';

// Types para el nuevo chat unificado
interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  type: 'text' | 'pdf_analysis' | 'error';
  sources?: Array<{ title: string; uri?: string }>;
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
  // State management
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([]);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Router para navegación
  const router = useRouter();

  // Constants
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [inputValue]);

  // Welcome message
  useEffect(() => {
    if (messages.length === 0) {
      const welcomeMessage: ChatMessage = {
        id: 'welcome',
        role: 'assistant',
        content: `¡Hola! Soy tu experto en moldeo por inyección con IA.

Puedo ayudarte con:
• **Análisis de planos técnicos** - Sube PDFs y analizo dimensiones, tolerancias y viabilidad
• **Preguntas sobre diseño** - Resuelvo dudas sobre geometría, materiales y procesos  
• **Recomendaciones técnicas** - Basadas en mejores prácticas de moldeo
• **Grounding con conocimiento** - Acceso a nuestra base de conocimiento especializada

**¿En qué puedo ayudarte hoy?** Puedes subir un plano técnico o hacerme cualquier pregunta sobre moldeo por inyección.`,
        timestamp: new Date(),
        type: 'text'
      };
      setMessages([welcomeMessage]);
    }
  }, []);

  // Handle file upload
  const handleFileUpload = async (files: FileList) => {
    const file = files[0];
    
    if (!file || file.type !== 'application/pdf') {
      alert('Por favor, selecciona un archivo PDF válido.');
      return;
    }

    // Add to uploading files
    const uploadingFile: UploadingFile = {
      file,
      progress: 0,
      status: 'uploading'
    };
    setUploadingFiles(prev => [...prev, uploadingFile]);

    // Add user message with file attachment
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

    // Upload and analyze in unified chat endpoint
    await processFileInChat(file, uploadingFile);
  };

  // Process file in unified chat endpoint
  const processFileInChat = async (file: File, uploadingFile: UploadingFile) => {
    try {
      // Update status
      setUploadingFiles(prev => 
        prev.map(f => f === uploadingFile ? { ...f, status: 'processing', progress: 30 } : f)
      );

      // Create FormData
      const formData = new FormData();
      formData.append('file', file);
      formData.append('message', 'Analiza este plano técnico y respóndeme en el contexto de nuestra conversación');
      formData.append('chat_history', JSON.stringify(messages.slice(-10))); // Last 10 messages for context

      setIsTyping(true);

      // Call unified chat endpoint - CORREGIDO: usar /analysis/upload para archivos con FormData
      const response = await fetch(`${API_BASE_URL}/analysis/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Error en el análisis');
      }

      // Update status
      setUploadingFiles(prev => 
        prev.map(f => f === uploadingFile ? { ...f, status: 'analyzing', progress: 70 } : f)
      );

      const result = await response.json();
      
      // Update status to completed
      setUploadingFiles(prev => 
        prev.map(f => f === uploadingFile ? { ...f, status: 'completed', progress: 100 } : f)
      );

      // Add AI response
      const aiMessage: ChatMessage = {
        id: `ai-${Date.now()}`,
        role: 'assistant',
        content: result.message,  // CORREGIDO: usar 'message' en lugar de 'response'
        timestamp: new Date(),
        type: 'pdf_analysis',
        sources: result.sources || []
      };

      setMessages(prev => [...prev, aiMessage]);

      // Remove from uploading files after delay
      setTimeout(() => {
        setUploadingFiles(prev => prev.filter(f => f !== uploadingFile));
      }, 2000);

    } catch (error) {
      console.error('Upload error:', error);
      
      // Update status to error
      setUploadingFiles(prev => 
        prev.map(f => f === uploadingFile ? { ...f, status: 'error', progress: 0 } : f)
      );

      // Add error message
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'Lo siento, hubo un error al analizar el archivo. Por favor, intenta de nuevo.',
        timestamp: new Date(),
        type: 'error'
      };

      setMessages(prev => [...prev, errorMessage]);

      // Remove from uploading files
      setTimeout(() => {
        setUploadingFiles(prev => prev.filter(f => f !== uploadingFile));
      }, 3000);
    } finally {
      setIsTyping(false);
    }
  };

  // Send text message
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
      // Call unified chat endpoint for text only - CORREGIDO: usar /analysis/ para mensajes JSON
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
      
      const aiMessage: ChatMessage = {
        id: `ai-${Date.now()}`,
        role: 'assistant',
        content: result.message,  // CORREGIDO: usar 'message' en lugar de 'response'
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

  // Handle key press
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendTextMessage();
    }
  };

  // Handle drop
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileUpload(files);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
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
      {/* Sidebar - PATRÓN UNIFICADO */}
      <div className={`${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} fixed inset-y-0 left-0 z-50 w-80 bg-white dark:bg-gray-900 shadow-xl transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0`}>
        <div className="flex items-center justify-between h-16 px-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">SME AI</h2>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-2 rounded-md text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            ✕
          </button>
        </div>
        <div className="p-4 space-y-4">
          {/* Navigation Links - PATRÓN UNIFICADO */}
          <div className="space-y-2">
            <Link href="/" className="flex items-center space-x-3 p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300">
              <Brain className="w-5 h-5" />
              <span className="font-medium">Chat AI</span>
            </Link>
            <Link href="/knowledge-base" className="flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300">
              <Database className="w-5 h-5" />
              <span className="font-medium">Base de Conocimiento</span>
            </Link>
          </div>
          
          {/* Quick Actions */}
          <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
            <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-3">Acciones Rápidas</h3>
            <div className="space-y-2">
              <button 
                onClick={() => fileInputRef.current?.click()}
                className="w-full flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300"
              >
                <Upload className="w-5 h-5 text-green-500" />
                <span className="font-medium">Subir Plano</span>
              </button>
              <button className="w-full flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300">
                <MessageCircle className="w-5 h-5 text-blue-500" />
                <span className="font-medium">Limpiar Chat</span>
              </button>
            </div>
          </div>
          
          {/* Chat Status */}
          <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
            <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-3">Estado del Chat</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Mensajes</span>
                <span className="font-medium text-gray-900 dark:text-white">{messages.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Subidas activas</span>
                <span className="font-medium text-gray-900 dark:text-white">{uploadingFiles.length}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {/* Header - PATRÓN UNIFICADO */}
        <header className="h-16 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-6">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 rounded-md text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Brain className="w-4 h-4 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-white">SME AI Chat</h1>
                <p className="text-xs text-gray-500 dark:text-gray-400">Experto en Moldeo por Inyección</p>
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setIsDarkMode(!isDarkMode)}
              className="p-2 rounded-md text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              title="Cambiar tema"
            >
              <MessageCircle className="w-5 h-5" />
            </button>
          </div>
        </header>

        {/* Messages Area */}
        <div className="flex-1 overflow-hidden bg-gray-50 dark:bg-gray-800">
          <div className="h-full overflow-y-auto p-4">
            <div className="max-w-4xl mx-auto space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg px-4 py-3 ${
                      message.role === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-white dark:bg-gray-900 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-700'
                    }`}
                  >
                    {/* Message attachments */}
                    {message.attachments && message.attachments.length > 0 && (
                      <div className="mb-2 space-y-1">
                        {message.attachments.map((file, index) => (
                          <div key={index} className="flex items-center space-x-2 text-sm bg-gray-100 dark:bg-gray-800 rounded p-2">
                            <FileText className="w-4 h-4" />
                            <span className="font-medium">{file.name}</span>
                            <span className="text-gray-500">({formatFileSize(file.size)})</span>
                          </div>
                        ))}
                      </div>
                    )}
                    
                    {/* Message content */}
                    <div className="whitespace-pre-wrap text-sm">
                      {message.content}
                    </div>
                    
                    {/* Sources */}
                    {message.sources && message.sources.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600">
                        <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Fuentes:</p>
                        {message.sources.map((source, index) => (
                          <div key={index} className="text-xs text-blue-600 dark:text-blue-400">
                            📖 {source.title}
                          </div>
                        ))}
                      </div>
                    )}
                    
                    <div className="text-xs opacity-70 mt-2">
                      {message.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}
              
              {/* Typing indicator */}
              {isTyping && (
                <div className="flex justify-start">
                  <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg px-4 py-3">
                    <div className="flex items-center space-x-2">
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      </div>
                      <span className="text-sm text-gray-500">Analizando...</span>
                    </div>
                  </div>
                </div>
              )}
              
              {/* Uploading files */}
              {uploadingFiles.map((uploadingFile, index) => (
                <div key={index} className="flex justify-start">
                  <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg px-4 py-3 w-full max-w-md">
                    <div className="flex items-center space-x-3">
                      <Upload className="w-5 h-5 text-blue-500 animate-pulse" />
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900 dark:text-white">
                          {uploadingFile.file.name}
                        </p>
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mt-2">
                          <div 
                            className={`h-2 rounded-full transition-all duration-300 ${
                              uploadingFile.status === 'error' ? 'bg-red-500' : 'bg-blue-500'
                            }`}
                            style={{ width: `${uploadingFile.progress}%` }}
                          ></div>
                        </div>
                        <p className="text-xs text-gray-500 mt-1">
                          {uploadingFile.status === 'uploading' && 'Subiendo...'}
                          {uploadingFile.status === 'processing' && 'Procesando...'}
                          {uploadingFile.status === 'analyzing' && 'Analizando con IA...'}
                          {uploadingFile.status === 'completed' && 'Completado'}
                          {uploadingFile.status === 'error' && 'Error'}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
              
              <div ref={messagesEndRef} />
            </div>
          </div>
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-200 dark:border-gray-700 p-4">
          <div className="max-w-4xl mx-auto">
            <div 
              className="flex items-end space-x-3 bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg p-3"
              onDrop={handleDrop}
              onDragOver={handleDragOver}
            >
              <button
                onClick={() => fileInputRef.current?.click()}
                className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                title="Adjuntar archivo"
              >
                <Paperclip className="w-5 h-5" />
              </button>
              
              <textarea
                ref={textareaRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Escribe tu mensaje... (sube PDFs arrastrando o con el clip)"
                className="flex-1 bg-transparent border-none resize-none focus:outline-none text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
                rows={1}
              />
              
              <button
                onClick={sendTextMessage}
                disabled={!inputValue.trim() || isTyping}
                className="p-2 text-blue-500 hover:text-blue-600 disabled:text-gray-400 disabled:cursor-not-allowed"
                title="Enviar mensaje"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
            
            <div className="mt-2 text-xs text-gray-500 dark:text-gray-400 text-center">
              Presiona Enter para enviar • Shift+Enter para nueva línea • Arrastra PDFs aquí
            </div>
          </div>
        </div>

        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          className="hidden"
          onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files)}
        />
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
