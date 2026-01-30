'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Bot, User, Sparkles, ChevronRight, Copy, Check } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  mcp?: string;
  sources?: string[];
  suggestedQuestions?: string[];
  confidence?: number;
  metadata?: any;
  timestamp: Date;
}

interface ChatProProps {
  activeMCP: string | null;
}

// Sample starter questions - Data-driven and answerable from Eaton's actual data
const SAMPLE_QUESTIONS = {
  'Product Intelligence (MARKET MCP)': [
    'Analyze FRCDM-40 vs competitors (ABB, Siemens, Schneider)',
    'What is the market pricing for 40A circuit breakers?',
    'Find competitor alternatives to our FRCDM product line',
    'Analyze our market positioning in industrial protection',
  ],
  'Content Generation (PUBLISH MCP)': [
    'Generate Amazon Business listing for FRCDM-40',
    'Create LinkedIn post announcing our circuit breaker line',
    'Generate professional datasheet for FRCDM-40/4/03-G/B+',
    'Export BMEcat feed for our product catalog',
  ],
  'Technical Specifications': [
    'What are the complete specs of the FRCDM-40/4/03-G/B+ circuit breaker?',
    'List all circuit breaker models in our ECLASS data',
    'What contactor models (DILM series) do we manufacture?',
    'Show technical details and compliance for our UPS products',
  ],
  'Standards & Compliance': [
    'What ECLASS and ETIM standards are used in our product data?',
    'Which products comply with IEC 61008 standards?',
    'Explain our BMEcat catalog structure and ETIM guidelines',
    'List all compliance certifications referenced in our data',
  ],
};

export default function ChatPro({ activeMCP }: ChatProProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showSamples, setShowSamples] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (messageText?: string) => {
    const text = messageText || input;
    if (!text.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setShowSamples(false);

    try {
      const token = localStorage.getItem('0711_token');
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4010';
      const headers: HeadersInit = { 'Content-Type': 'application/json' };

      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${apiUrl}/api/chat`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          message: text,
          mcp: activeMCP,
          history: messages.slice(-6).map((m) => ({
            role: m.role,
            content: m.content,
          })),
        }),
      });

      const data = await response.json();

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.answer,
        mcp: data.mcp_used,
        sources: data.sources || [],
        suggestedQuestions: data.suggested_questions || [],
        confidence: data.confidence,
        metadata: data.metadata || {},
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, there was an error processing your request. Please try again.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleSampleQuestion = (question: string) => {
    setInput(question);
    sendMessage(question);
  };

  return (
    <div className="flex h-full bg-gray-50">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-orange-500" />
                AI Assistant
              </h2>
              <p className="text-sm text-gray-500 mt-1">
                Powered by Claude Sonnet 4.5 • Analyzing your product data
              </p>
            </div>
            {activeMCP && (
              <div className="px-3 py-1 bg-blue-50 text-blue-700 rounded-lg text-sm font-medium">
                {activeMCP.toUpperCase()} MCP
              </div>
            )}
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          {messages.length === 0 && showSamples && (
            <div className="max-w-4xl mx-auto">
              {/* Welcome Message */}
              <div className="text-center mb-12">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-orange-500 to-orange-600 rounded-2xl mb-4 shadow-lg">
                  <Sparkles className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-2xl font-semibold text-gray-900 mb-2">
                  Welcome to your AI Product Assistant
                </h3>
                <p className="text-gray-600 max-w-2xl mx-auto">
                  Ask me anything about your products, market data, compliance, or business intelligence.
                  I'll provide detailed analysis with sources and actionable recommendations.
                </p>
              </div>

              {/* Sample Questions */}
              <div className="space-y-6">
                {Object.entries(SAMPLE_QUESTIONS).map(([category, questions]) => (
                  <div key={category}>
                    <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                      <ChevronRight className="w-4 h-4 text-orange-500" />
                      {category}
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {questions.map((question, idx) => (
                        <button
                          key={idx}
                          onClick={() => handleSampleQuestion(question)}
                          className="text-left p-4 bg-white border border-gray-200 rounded-xl hover:border-orange-300 hover:shadow-md transition-all group"
                        >
                          <p className="text-sm text-gray-700 group-hover:text-gray-900">
                            {question}
                          </p>
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Message List */}
          {messages.map((message) => (
            <MessageBubble
              key={message.id}
              message={message}
              onQuestionClick={handleSampleQuestion}
            />
          ))}

          {/* Loading Indicator */}
          {isLoading && (
            <div className="flex gap-4 mb-6 max-w-4xl">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-orange-500 to-orange-600 flex items-center justify-center flex-shrink-0 shadow-lg">
                <Bot className="w-6 h-6 text-white" />
              </div>
              <div className="bg-white rounded-2xl px-6 py-4 shadow-sm border border-gray-100">
                <div className="flex items-center gap-2">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-orange-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                    <span className="w-2 h-2 bg-orange-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                    <span className="w-2 h-2 bg-orange-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                  </div>
                  <span className="text-sm text-gray-500 ml-2">Analyzing your data...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="bg-white border-t border-gray-200 px-6 py-4">
          <div className="max-w-4xl mx-auto">
            <div className="flex gap-3">
              <div className="flex-1 relative">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask about products, market trends, compliance..."
                  rows={1}
                  className="w-full resize-none rounded-xl border border-gray-300 px-4 py-3 pr-12 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent text-gray-900 placeholder-gray-400"
                  style={{ minHeight: '48px', maxHeight: '120px' }}
                />
              </div>
              <button
                onClick={() => sendMessage()}
                disabled={!input.trim() || isLoading}
                className="px-6 py-3 bg-gradient-to-r from-orange-500 to-orange-600 text-white rounded-xl hover:from-orange-600 hover:to-orange-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl flex items-center gap-2 font-medium"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span className="hidden sm:inline">Thinking...</span>
                  </>
                ) : (
                  <>
                    <Send className="w-5 h-5" />
                    <span className="hidden sm:inline">Send</span>
                  </>
                )}
              </button>
            </div>
            <p className="text-xs text-gray-400 mt-2 text-center">
              Press Enter to send • Shift+Enter for new line
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

// Message Bubble Component
function MessageBubble({ message, onQuestionClick }: { message: Message; onQuestionClick: (q: string) => void }) {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (message.role === 'user') {
    return (
      <div className="flex justify-end gap-4 mb-6 max-w-4xl ml-auto">
        <div className="bg-blue-600 text-white rounded-2xl px-6 py-4 max-w-2xl shadow-lg">
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center flex-shrink-0 shadow-lg">
          <User className="w-6 h-6 text-white" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-4 mb-6 max-w-4xl">
      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-orange-500 to-orange-600 flex items-center justify-center flex-shrink-0 shadow-lg">
        <Bot className="w-6 h-6 text-white" />
      </div>
      <div className="flex-1">
        <div className="bg-white rounded-2xl px-6 py-5 shadow-sm border border-gray-100">
          {/* Main Content with Enhanced Markdown */}
          <div className="prose prose-sm max-w-none prose-headings:font-semibold prose-h2:text-xl prose-h2:mt-6 prose-h2:mb-3 prose-p:text-gray-700 prose-li:text-gray-700 prose-strong:text-gray-900">
            <ReactMarkdown
              components={{
                code({ node, inline, className, children, ...props }: any) {
                  const match = /language-(\w+)/.exec(className || '');
                  return !inline && match ? (
                    <SyntaxHighlighter
                      style={vscDarkPlus as any}
                      language={match[1]}
                      PreTag="div"
                      {...props}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  ) : (
                    <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono text-gray-800" {...props}>
                      {children}
                    </code>
                  );
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>

          {/* Metadata Bar */}
          <div className="flex items-center gap-4 mt-4 pt-4 border-t border-gray-100">
            <button
              onClick={copyToClipboard}
              className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-700 transition-colors"
            >
              {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
              {copied ? 'Copied!' : 'Copy'}
            </button>
            {message.confidence && (
              <div className="text-xs text-gray-500">
                Confidence: <span className="font-medium">{Math.round(message.confidence * 100)}%</span>
              </div>
            )}
            {message.mcp && (
              <div className="text-xs text-gray-500">
                via <span className="font-medium text-blue-600">{message.mcp.toUpperCase()}</span>
              </div>
            )}
          </div>

          {/* Sources */}
          {message.sources && message.sources.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-100">
              <p className="text-xs font-semibold text-gray-600 mb-2">Sources ({message.sources.length})</p>
              <div className="flex flex-wrap gap-2">
                {message.sources.map((source, i) => (
                  <div
                    key={i}
                    className="px-3 py-1.5 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-600 hover:bg-gray-100 transition-colors cursor-pointer"
                    title={source}
                  >
                    📄 {source.length > 30 ? source.substring(0, 30) + '...' : source}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Suggested Questions */}
          {message.suggestedQuestions && message.suggestedQuestions.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-100">
              <p className="text-xs font-semibold text-gray-600 mb-3 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-orange-500" />
                Suggested follow-ups
              </p>
              <div className="space-y-2">
                {message.suggestedQuestions.map((question, i) => (
                  <button
                    key={i}
                    onClick={() => onQuestionClick(question)}
                    className="w-full text-left px-4 py-2.5 bg-gradient-to-r from-orange-50 to-orange-50/50 border border-orange-200 rounded-lg text-sm text-gray-700 hover:from-orange-100 hover:to-orange-100/50 hover:border-orange-300 transition-all group"
                  >
                    <span className="group-hover:text-gray-900">{question}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
