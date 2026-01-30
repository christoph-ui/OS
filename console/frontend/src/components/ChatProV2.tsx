'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Bot, User, Sparkles, ChevronRight, Copy, Check, Zap } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { colors, fonts } from './mcps/theme';

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

interface Tool {
  id: string;
  name: string;
  description: string;
  example: string;
  icon: string;
}

interface MCP {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  tools: Tool[];
  tool_count: number;
}

interface ChatProV2Props {
  activeMCP: string | null;
}

export default function ChatProV2({ activeMCP }: ChatProV2Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [mcps, setMcps] = useState<MCP[]>([]);
  const [activeMcpData, setActiveMcpData] = useState<MCP | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadMCPs();
  }, []);

  useEffect(() => {
    // Update active MCP data when selection changes
    if (activeMCP && activeMCP !== 'auto') {
      const mcpData = mcps.find(m => m.id === activeMCP);
      setActiveMcpData(mcpData || null);
    } else {
      setActiveMcpData(null);
    }
  }, [activeMCP, mcps]);

  const loadMCPs = async () => {
    try {
      const response = await fetch('http://localhost:4010/api/mcps/capabilities');
      const data = await response.json();
      setMcps(data.mcps || []);
    } catch (error) {
      console.error('Error loading MCPs:', error);
    }
  };

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
          mcp: activeMCP === 'auto' ? null : activeMCP,
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

  const handleToolClick = (example: string) => {
    setInput(example);
    sendMessage(example);
  };

  return (
    <div className="flex h-full" style={{ backgroundColor: colors.light }}>
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="px-6 py-4 border-b" style={{ backgroundColor: colors.dark, borderColor: colors.dark }}>
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold flex items-center gap-2" style={{ color: colors.light, fontFamily: fonts.heading }}>
                <Sparkles className="w-5 h-5" style={{ color: colors.orange }} />
                AI Assistant
              </h2>
              <p className="text-sm mt-1" style={{ color: colors.midGray, fontFamily: fonts.body }}>
                Powered by Claude Sonnet 4.5 • {mcps.length} AI Experts • {mcps.reduce((sum, m) => sum + m.tool_count, 0)} Tools
              </p>
            </div>
            {activeMCP && activeMCP !== 'auto' && (
              <div className="px-3 py-1 rounded-lg text-sm font-medium flex items-center gap-2" style={{ backgroundColor: colors.orange + '20', color: colors.orange, fontFamily: fonts.heading }}>
                <span>{activeMCP.toUpperCase()} MCP</span>
              </div>
            )}
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          {messages.length === 0 && (
            <EmptyState mcps={mcps} onToolClick={handleToolClick} />
          )}

          {messages.map((message) => (
            <MessageBubble
              key={message.id}
              message={message}
              onQuestionClick={handleToolClick}
            />
          ))}

          {isLoading && <LoadingIndicator />}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="px-6 py-4 border-t" style={{ backgroundColor: colors.light, borderColor: colors.lightGray }}>
          <div className="max-w-4xl mx-auto">
            <div className="flex gap-3">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about products, competitors, market intelligence..."
                rows={1}
                className="flex-1 resize-none rounded-lg px-4 py-3 focus:outline-none border"
                style={{
                  minHeight: '48px',
                  maxHeight: '120px',
                  borderColor: colors.lightGray,
                  backgroundColor: colors.light,
                  color: colors.dark,
                  fontFamily: fonts.body
                }}
                onFocus={(e) => e.currentTarget.style.borderColor = colors.orange}
                onBlur={(e) => e.currentTarget.style.borderColor = colors.lightGray}
              />
              <button
                onClick={() => sendMessage()}
                disabled={!input.trim() || isLoading}
                className="px-6 py-3 rounded-lg flex items-center gap-2 font-semibold transition-all"
                style={{
                  backgroundColor: (!input.trim() || isLoading) ? colors.midGray : colors.orange,
                  color: colors.light,
                  fontFamily: fonts.heading,
                  cursor: (!input.trim() || isLoading) ? 'not-allowed' : 'pointer',
                  opacity: (!input.trim() || isLoading) ? 0.6 : 1
                }}
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </div>
            <p className="text-xs mt-2 text-center" style={{ color: colors.midGray, fontFamily: fonts.body }}>
              Press Enter to send • Shift+Enter for new line
            </p>
          </div>
        </div>
      </div>

      {/* Right Sidebar - Tool Palette */}
      <ToolPalette
        mcps={mcps}
        activeMCP={activeMCP}
        activeMcpData={activeMcpData}
        onToolClick={handleToolClick}
      />
    </div>
  );
}

// Tool Palette (Right Sidebar)
function ToolPalette({ mcps, activeMCP, activeMcpData, onToolClick }: any) {
  const allTools = mcps.flatMap((mcp: MCP) =>
    mcp.tools.map(tool => ({ ...tool, mcp: mcp.id, mcpName: mcp.name, mcpIcon: mcp.icon }))
  );

  // Filter tools if specific MCP selected
  const displayTools = activeMCP && activeMCP !== 'auto' && activeMcpData
    ? activeMcpData.tools.map((t: any) => ({ ...t, mcp: activeMcpData.id, mcpName: activeMcpData.name, mcpIcon: activeMcpData.icon }))
    : allTools;

  return (
    <div className="w-80 border-l overflow-y-auto" style={{ backgroundColor: colors.dark, borderColor: colors.dark }}>
      <div className="p-4 border-b" style={{ borderColor: colors.midGray + '33' }}>
        <h3 className="font-semibold flex items-center gap-2" style={{ color: colors.light, fontFamily: fonts.heading }}>
          <Zap className="w-4 h-4" style={{ color: colors.orange }} />
          {activeMCP && activeMCP !== 'auto' ? (
            <span>{activeMcpData?.name || activeMCP.toUpperCase()} Tools ({displayTools.length})</span>
          ) : (
            <span>All Tools ({displayTools.length})</span>
          )}
        </h3>
        <p className="text-xs mt-1" style={{ color: colors.midGray, fontFamily: fonts.body }}>Click any tool to try it</p>
      </div>

      <div className="p-3 space-y-2">
        {displayTools.map((tool: any, idx: number) => (
          <button
            key={idx}
            onClick={() => onToolClick(tool.example)}
            className="w-full text-left p-3 border rounded-lg transition-all group"
            style={{ backgroundColor: colors.light + '08', borderColor: colors.light + '15' }}
            onMouseEnter={(e) => e.currentTarget.style.borderColor = colors.orange + '66'}
            onMouseLeave={(e) => e.currentTarget.style.borderColor = colors.light + '15'}
          >
            <div className="flex items-start gap-2">
              <div className="flex-1 min-w-0">
                <div className="font-medium text-sm" style={{ color: colors.light, fontFamily: fonts.heading }}>
                  {tool.name}
                </div>
                <div className="text-xs mt-1 line-clamp-2" style={{ color: colors.midGray, fontFamily: fonts.body }}>
                  {tool.description}
                </div>
                {(!activeMCP || activeMCP === 'auto') && (
                  <div className="mt-2 inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded" style={{ backgroundColor: colors.light + '15', color: colors.midGray, fontFamily: fonts.heading }}>
                    <span>{tool.mcp.toUpperCase()}</span>
                  </div>
                )}
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

// Empty State with Sample Questions
function EmptyState({ mcps, onToolClick }: any) {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-12">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-xl mb-4" style={{ backgroundColor: colors.dark }}>
          <Sparkles className="w-8 h-8" style={{ color: colors.light }} />
        </div>
        <h3 className="text-2xl font-semibold mb-2" style={{ color: colors.dark, fontFamily: fonts.heading }}>
          Your AI Product Intelligence Team
        </h3>
        <p className="text-gray-600 max-w-2xl mx-auto">
          {mcps.length} specialized AI experts ready to help. Ask about products, competitors,
          market intelligence, or generate content for any channel.
        </p>
      </div>

      {/* Quick Start with MCPs */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {mcps.slice(0, 4).map((mcp: MCP) => (
          <div key={mcp.id} className="border border-gray-200 rounded-xl p-4 bg-white">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-3xl">{mcp.icon}</span>
              <div>
                <h4 className="font-semibold text-gray-900">{mcp.name}</h4>
                <p className="text-xs text-gray-500">{mcp.tool_count} tools</p>
              </div>
            </div>
            <div className="space-y-2">
              {mcp.tools.slice(0, 2).map((tool: Tool) => (
                <button
                  key={tool.id}
                  onClick={() => onToolClick(tool.example)}
                  className="w-full text-left p-2 bg-gray-50 hover:bg-blue-50 rounded-lg text-sm transition-colors group"
                >
                  <div className="flex items-center gap-2">
                    <span>{tool.icon}</span>
                    <span className="text-gray-700 group-hover:text-blue-700 text-xs">
                      {tool.name}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Message Bubble
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
          {/* Main Content */}
          <div className="prose prose-sm max-w-none prose-headings:font-semibold prose-h2:text-xl prose-h2:mt-6 prose-h2:mb-3 prose-p:text-gray-700 prose-li:text-gray-700 prose-strong:text-gray-900">
            <ReactMarkdown
              components={{
                code({ node, inline, className, children, ...props }) {
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

// Loading Indicator
function LoadingIndicator() {
  return (
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
  );
}
