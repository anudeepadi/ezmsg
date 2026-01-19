'use client';

import { useEffect, useState, useRef } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import { Header } from '@/components/layout';
import {
  simulator,
  SimulatorMessage,
  QuickReply,
  ApiError,
} from '@/lib/api';
import { useToastStore } from '@/lib/store';
import { cn } from '@/lib/utils';
import {
  ArrowLeft,
  Send,
  Play,
  Clock,
  MessageCircle,
  Bot,
  User,
  ChevronRight,
  RotateCcw,
  FastForward,
  ExternalLink,
  ImageIcon,
} from 'lucide-react';

// Helper to detect if URL is an image/GIF
const isImageUrl = (url: string): boolean => {
  const imageExtensions = /\.(gif|jpe?g|png|webp|svg|bmp|ico)(\?.*)?$/i;
  const imageHosts = /(giphy\.com|tenor\.com|imgur\.com|gfycat\.com)/i;
  return imageExtensions.test(url) || imageHosts.test(url);
};

// Helper to detect if URL is a video (YouTube, etc.)
const isVideoUrl = (url: string): boolean => {
  return /(youtube\.com|youtu\.be|vimeo\.com)/i.test(url);
};

// Extract YouTube video ID
const getYouTubeId = (url: string): string | null => {
  const match = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]+)/);
  return match ? match[1] : null;
};

interface ChatMessage {
  id: string;
  type: 'system' | 'user';
  content: string;
  mediaUrl?: string | null;
  timestamp: string;
  nodeId?: number;
  nodeName?: string;
  displayName?: string | null;
  delayDescription?: string | null;
  isTerminal?: boolean;
  quickReplies?: QuickReply[];
  availableEdges?: { to_node_id: number; to_node_name: string; label: string | null }[];
}

export default function ProtocolSimulatorPage() {
  const params = useParams();
  const projectId = Number(params.id);
  const { addToast } = useToastStore();
  const chatEndRef = useRef<HTMLDivElement>(null);

  const [loading, setLoading] = useState(false);
  const [started, setStarted] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentNodeId, setCurrentNodeId] = useState<number | null>(null);
  const [currentTime, setCurrentTime] = useState<string>('');
  const [inputValue, setInputValue] = useState('');
  const [projectName, setProjectName] = useState('');
  const [isTerminal, setIsTerminal] = useState(false);
  const [languageId, setLanguageId] = useState(1);
  const [expectsReply, setExpectsReply] = useState(false);

  // Scroll to bottom when messages change
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const formatTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  const formatDate = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    });
  };

  const addSystemMessage = (msg: SimulatorMessage) => {
    const newMessage: ChatMessage = {
      id: `sys-${Date.now()}-${msg.node_id}`,
      type: 'system',
      content: msg.message_text || '(No message content)',
      mediaUrl: msg.media_url,
      timestamp: msg.scheduled_time,
      nodeId: msg.node_id,
      nodeName: msg.node_name,
      displayName: msg.display_name,
      delayDescription: msg.delay_description,
      isTerminal: msg.is_terminal,
      quickReplies: msg.quick_replies,
      availableEdges: msg.available_edges,
    };
    setMessages(prev => [...prev, newMessage]);
    setCurrentNodeId(msg.node_id);
    setCurrentTime(msg.scheduled_time);
    setIsTerminal(msg.is_terminal);
    setExpectsReply(msg.expects_reply);
  };

  const addUserMessage = (content: string, timestamp: string) => {
    const newMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      type: 'user',
      content,
      timestamp,
    };
    setMessages(prev => [...prev, newMessage]);
  };

  const handleStart = async () => {
    setLoading(true);
    try {
      const result = await simulator.start(projectId, { language_id: languageId });
      setStarted(true);
      setProjectName(result.project_name);
      setMessages([]);
      addSystemMessage(result.message);
    } catch (err) {
      if (err instanceof ApiError) {
        addToast('error', `Failed to start simulation: ${err.statusText}`);
      } else {
        addToast('error', 'Failed to start simulation');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleReply = async (replyValue: string, displayValue?: string) => {
    if (!currentNodeId || !currentTime) return;

    setLoading(true);
    try {
      // Add user message to chat
      addUserMessage(displayValue || replyValue, currentTime);

      const result = await simulator.reply(projectId, {
        current_node_id: currentNodeId,
        reply_value: replyValue,
        current_time: currentTime,
        language_id: languageId,
      });

      if (result.message) {
        addSystemMessage(result.message);
      } else if (result.end_reason) {
        setIsTerminal(true);
        addToast('info', `Simulation ended: ${result.end_reason}`);
      }
    } catch (err) {
      if (err instanceof ApiError) {
        addToast('error', `Failed to process reply: ${err.statusText}`);
      } else {
        addToast('error', 'Failed to process reply');
      }
    } finally {
      setLoading(false);
      setInputValue('');
    }
  };

  const handleAdvance = async () => {
    if (!currentNodeId || !currentTime) return;

    setLoading(true);
    try {
      const result = await simulator.advance(projectId, {
        current_node_id: currentNodeId,
        current_time: currentTime,
        language_id: languageId,
      });

      if (result.message) {
        addSystemMessage(result.message);
      } else if (result.end_reason) {
        setIsTerminal(true);
        addToast('info', `Simulation ended: ${result.end_reason}`);
      }
    } catch (err) {
      if (err instanceof ApiError) {
        addToast('error', `Failed to advance: ${err.statusText}`);
      } else {
        addToast('error', 'Failed to advance');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setStarted(false);
    setMessages([]);
    setCurrentNodeId(null);
    setCurrentTime('');
    setIsTerminal(false);
    setInputValue('');
    setExpectsReply(false);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim()) {
      handleReply(inputValue.trim());
    }
  };

  // Get the last message for quick replies
  const lastMessage = messages[messages.length - 1];
  const showQuickReplies = lastMessage?.type === 'system' && lastMessage.quickReplies?.length && !isTerminal;

  return (
    <>
      <Header
        title="Protocol Simulator"
        description={projectName || 'Interactive protocol flow testing'}
        actions={
          <div className="flex items-center gap-3">
            <Link href={`/admin/projects/${projectId}`} className="btn-secondary">
              <ArrowLeft className="h-4 w-4" />
              Back
            </Link>
            {started && (
              <button onClick={handleReset} className="btn-secondary">
                <RotateCcw className="h-4 w-4" />
                Reset
              </button>
            )}
          </div>
        }
      />

      <div className="flex flex-col h-[calc(100vh-140px)]">
        {!started ? (
          // Start screen
          <div className="flex-1 flex items-center justify-center p-6">
            <div className="card p-8 max-w-md w-full text-center">
              <div className="w-16 h-16 rounded-full bg-accent-light flex items-center justify-center mx-auto mb-6">
                <MessageCircle className="h-8 w-8 text-accent" />
              </div>
              <h2 className="text-title text-text mb-2">Interactive Protocol Simulator</h2>
              <p className="text-body text-text-secondary mb-6">
                Walk through the messaging protocol step-by-step. You'll see each message and can choose how to respond.
              </p>

              <div className="mb-6">
                <label className="block text-body-sm font-medium text-text mb-2">
                  Language
                </label>
                <select
                  value={languageId}
                  onChange={(e) => setLanguageId(Number(e.target.value))}
                  className="input w-full"
                >
                  <option value={1}>English</option>
                  <option value={2}>Spanish</option>
                </select>
              </div>

              <button
                onClick={handleStart}
                disabled={loading}
                className="btn-primary w-full"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                    Starting...
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-2">
                    <Play className="h-4 w-4" />
                    Start Simulation
                  </span>
                )}
              </button>
            </div>
          </div>
        ) : (
          // Chat interface
          <>
            {/* Messages area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((msg, index) => {
                const showDateDivider = index === 0 ||
                  formatDate(messages[index - 1].timestamp) !== formatDate(msg.timestamp);

                return (
                  <div key={msg.id}>
                    {showDateDivider && (
                      <div className="flex items-center justify-center my-4">
                        <span className="px-3 py-1 bg-background rounded-full text-caption text-text-muted">
                          {formatDate(msg.timestamp)}
                        </span>
                      </div>
                    )}

                    <div
                      className={cn('flex', {
                        'justify-start': msg.type === 'system',
                        'justify-end': msg.type === 'user',
                      })}
                    >
                      <div
                        className={cn('max-w-[80%] rounded-2xl p-4', {
                          'bg-surface': msg.type === 'system',
                          'bg-accent text-white': msg.type === 'user',
                        })}
                      >
                        {msg.type === 'system' && (
                          <div className="flex items-center gap-2 mb-2">
                            <Bot className="h-4 w-4 text-accent" />
                            <span className="text-caption font-medium text-accent">
                              {msg.displayName || msg.nodeName}
                            </span>
                            {msg.delayDescription && (
                              <span className="text-caption text-text-muted flex items-center gap-1">
                                <Clock className="h-3 w-3" />
                                {msg.delayDescription}
                              </span>
                            )}
                          </div>
                        )}

                        <p className={cn('text-body whitespace-pre-wrap', {
                          'text-text': msg.type === 'system',
                        })}>
                          {msg.content}
                        </p>

                        {msg.mediaUrl && (
                          <div className="mt-3">
                            {isImageUrl(msg.mediaUrl) ? (
                              // Render image/GIF
                              <div className="relative rounded-lg overflow-hidden">
                                <img
                                  src={msg.mediaUrl}
                                  alt="Media content"
                                  className="max-w-full max-h-64 rounded-lg object-contain"
                                  loading="lazy"
                                />
                                <a
                                  href={msg.mediaUrl}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="absolute top-2 right-2 p-1.5 bg-black/50 rounded-full hover:bg-black/70 transition-colors"
                                  title="Open in new tab"
                                >
                                  <ExternalLink className="h-3.5 w-3.5 text-white" />
                                </a>
                              </div>
                            ) : isVideoUrl(msg.mediaUrl) ? (
                              // Render YouTube embed
                              <div className="relative rounded-lg overflow-hidden">
                                {getYouTubeId(msg.mediaUrl) ? (
                                  <div className="aspect-video">
                                    <iframe
                                      src={`https://www.youtube.com/embed/${getYouTubeId(msg.mediaUrl)}`}
                                      title="Video"
                                      className="w-full h-full rounded-lg"
                                      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                      allowFullScreen
                                    />
                                  </div>
                                ) : (
                                  <a
                                    href={msg.mediaUrl}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="flex items-center gap-2 p-3 bg-background rounded-lg hover:bg-background/80 transition-colors"
                                  >
                                    <Play className="h-5 w-5 text-accent" />
                                    <span className="text-body-sm text-accent">Watch Video</span>
                                    <ExternalLink className="h-3.5 w-3.5 text-accent ml-auto" />
                                  </a>
                                )}
                              </div>
                            ) : (
                              // Render link with preview attempt
                              <a
                                href={msg.mediaUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center gap-2 p-3 bg-background rounded-lg hover:bg-background/80 transition-colors"
                              >
                                <ImageIcon className="h-5 w-5 text-text-muted" />
                                <span className="text-body-sm text-accent truncate flex-1">
                                  {msg.mediaUrl}
                                </span>
                                <ExternalLink className="h-3.5 w-3.5 text-text-muted" />
                              </a>
                            )}
                          </div>
                        )}

                        <div className={cn('mt-2 text-caption', {
                          'text-text-muted': msg.type === 'system',
                          'text-white/70': msg.type === 'user',
                        })}>
                          {formatTime(msg.timestamp)}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}

              {isTerminal && (
                <div className="flex items-center justify-center my-4">
                  <span className="px-4 py-2 bg-success-light text-success rounded-full text-body-sm font-medium">
                    ✓ Protocol Complete
                  </span>
                </div>
              )}

              <div ref={chatEndRef} />
            </div>

            {/* Quick replies */}
            {showQuickReplies && (
              <div className="px-4 pb-2">
                <div className="flex flex-wrap gap-2">
                  {lastMessage.quickReplies!.map((qr) => (
                    <button
                      key={qr.value}
                      onClick={() => handleReply(qr.value, qr.label)}
                      disabled={loading}
                      className="px-4 py-2 rounded-full border border-accent text-accent hover:bg-accent hover:text-white transition-colors text-body-sm font-medium disabled:opacity-50"
                    >
                      {qr.label}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Input area */}
            <div className="border-t border-border p-4">
              {!isTerminal ? (
                <div className="flex items-center gap-3">
                  {/* Auto-advance button for non-reply nodes */}
                  {!expectsReply && lastMessage?.type === 'system' && (
                    <button
                      onClick={handleAdvance}
                      disabled={loading}
                      className="btn-secondary flex items-center gap-2"
                      title="Auto-advance to next message"
                    >
                      <FastForward className="h-4 w-4" />
                      Next
                    </button>
                  )}

                  <form onSubmit={handleSubmit} className="flex-1 flex items-center gap-3">
                    <input
                      type="text"
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      placeholder={expectsReply ? "Type your reply..." : "Type a custom reply or click Next..."}
                      className="input flex-1"
                      disabled={loading}
                    />
                    <button
                      type="submit"
                      disabled={loading || !inputValue.trim()}
                      className="btn-primary"
                    >
                      <Send className="h-4 w-4" />
                    </button>
                  </form>
                </div>
              ) : (
                <div className="text-center">
                  <p className="text-body text-text-secondary mb-3">
                    The simulation has ended.
                  </p>
                  <button onClick={handleReset} className="btn-primary">
                    <RotateCcw className="h-4 w-4" />
                    Start New Simulation
                  </button>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </>
  );
}
