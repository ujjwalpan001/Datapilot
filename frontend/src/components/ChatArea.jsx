import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { FiSend, FiBarChart2, FiTrendingUp, FiFilter, FiRefreshCw } from 'react-icons/fi';
import MessageBubble from './MessageBubble';
import './ChatArea.css';

const SUGGESTIONS = [
  { icon: <FiBarChart2 />,   text: 'Plot the distribution of the main numeric column' },
  { icon: <FiTrendingUp />,  text: 'Show top 5 values by count in this dataset' },
  { icon: <FiFilter />,      text: 'Clean the dataset and report issues found' },
  { icon: <FiRefreshCw />,   text: 'Forecast trends for the next 30 days' },
];

function ChatArea({ session, messages, setMessages, activeFile, apiBaseUrl, query, setQuery }) {
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });

  useEffect(() => { scrollToBottom(); }, [messages, isLoading]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim() || isLoading) return;

    const userMessage = { role: 'user', content: query };
    setMessages(prev => [...prev, userMessage]);
    setQuery('');
    setIsLoading(true);

    try {
      const res = await axios.post(`${apiBaseUrl}/analyze`, {
        query: userMessage.content,
        filename: activeFile,
        session_id: session?.id,
      });

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: res.data.insight,
        chart_url: res.data.chart_url,
        chart_json: res.data.chart_json,
        export_url: res.data.export_url,
        data_preview: res.data.data_preview,
        tool_calls: res.data.tool_calls_made,
      }]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, {
        role: 'system',
        content: `Error: ${err.response?.data?.detail || err.message}`,
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="chat-container">
      {/* Messages */}
      <div className="messages-area">
        {messages.length === 0 && (
          <div className="empty-chat-state">
            <div className="empty-chat-icon">🔭</div>
            <div>
              <div className="empty-chat-title">Ready to explore your data</div>
              <div className="empty-chat-sub">
                Ask anything about <strong style={{ color: 'var(--violet-light)' }}>{activeFile}</strong>
              </div>
            </div>
            <div className="suggestions-grid">
              {SUGGESTIONS.map((s, i) => (
                <button
                  key={i}
                  className="suggestion-chip"
                  onClick={() => setQuery(s.text)}
                  style={{ animationDelay: `${i * 0.07}s` }}
                >
                  <span className="suggestion-icon">{s.icon}</span>
                  {s.text}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, idx) => (
          <MessageBubble key={idx} msg={msg} apiBaseUrl={apiBaseUrl} />
        ))}

        {isLoading && (
          <div className="loading-bubble">
            <div className="loading-dots">
              <div className="loading-dot" />
              <div className="loading-dot" />
              <div className="loading-dot" />
            </div>
            <span className="loading-text">Analyzing…</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="input-area">
        <form className="input-form" onSubmit={handleSubmit} id="chat-form">
          <input
            id="chat-input"
            className="chat-input"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={`Ask anything about ${activeFile}…`}
            disabled={isLoading}
            autoComplete="off"
          />
          <button
            type="submit"
            id="send-btn"
            className="send-btn"
            disabled={!query.trim() || isLoading}
            aria-label="Send message"
          >
            <FiSend size={16} />
          </button>
        </form>
      </div>
    </div>
  );
}

export default ChatArea;
