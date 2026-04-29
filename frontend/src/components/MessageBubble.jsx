import { FiUser, FiCpu, FiTool, FiBarChart2, FiDownload } from 'react-icons/fi';
import PlotlyChart from './PlotlyChart';
import ErrorBoundary from './ErrorBoundary';
import './MessageBubble.css';

function MessageBubble({ msg, apiBaseUrl }) {
  // ── System Message ──────────────────────────────────
  if (msg.role === 'system') {
    return (
      <div className="message system-msg animate-fade-in">
        <div className="system-msg-content">{msg.content}</div>
      </div>
    );
  }

  const isUser = msg.role === 'user';

  // ── Parse data preview ──────────────────────────────
  let previewKeys = [];
  let previewRows = [];
  try {
    if (!isUser && msg.data_preview) {
      const firstVal = Object.values(msg.data_preview)[0];
      if (Array.isArray(firstVal) && firstVal.length > 0) {
        previewKeys = Object.keys(firstVal[0] || {});
        previewRows = firstVal;
      }
    }
  } catch (e) {
    console.error('Error parsing data preview', e);
  }

  // ── Format message text with basic markdown ─────────
  const formatText = (text) => {
    if (!text) return '';
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\n/g, '<br/>');
  };

  // ── User Bubble ──────────────────────────────────────
  if (isUser) {
    return (
      <div className="message user-msg animate-fade-in">
        <div className="msg-avatar"><FiUser size={14} /></div>
        <div className="msg-body">
          <div className="user-bubble">{msg.content}</div>
        </div>
      </div>
    );
  }

  // ── AI Response ──────────────────────────────────────
  return (
    <ErrorBoundary>
      <div className="message assistant-msg animate-fade-in">
        <div className="msg-avatar"><FiCpu size={14} /></div>

        <div className="msg-body">
          <div className="ai-card">
            {/* Tool calls used */}
            {msg.tool_calls && msg.tool_calls.length > 0 && (
              <div className="tool-calls-strip">
                {msg.tool_calls.map((tc, idx) => {
                  let params = '';
                  try {
                    params = Object.values(tc.parameters || {})
                      .map(v => typeof v === 'object' ? JSON.stringify(v) : v)
                      .join(', ');
                  } catch (e) {}
                  const label = `${tc.tool_name}(${params.substring(0, 24)}${params.length > 24 ? '…' : ''})`;
                  return (
                    <span key={idx} className="tool-chip">
                      <FiTool className="tc-icon" size={9} />
                      {label}
                    </span>
                  );
                })}
              </div>
            )}

            {/* Main content */}
            <div className="ai-content">
              {/* Insight label */}
              {msg.content && (
                <>
                  <div className="insight-label">
                    <FiBarChart2 className="il-icon" size={10} />
                    Insight
                  </div>
                  <div
                    className="msg-text"
                    dangerouslySetInnerHTML={{ __html: formatText(msg.content) }}
                  />
                </>
              )}

              {/* Data Preview Table */}
              {previewKeys.length > 0 && (
                <div className="data-preview">
                  <div className="table-scroll">
                    <table className="data-table">
                      <thead>
                        <tr>{previewKeys.map(k => <th key={k}>{k}</th>)}</tr>
                      </thead>
                      <tbody>
                        {previewRows.map((row, i) => (
                          <tr key={i}>
                            {previewKeys.map((k, j) => (
                              <td key={j} title={String(row[k] ?? 'null')}>
                                {row[k] !== null && row[k] !== undefined ? String(row[k]) : <em style={{ opacity: 0.4 }}>null</em>}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Plotly Chart */}
              {msg.chart_json && (
                <div className="chart-container">
                  <ErrorBoundary>
                    <PlotlyChart chartJsonStr={msg.chart_json} />
                  </ErrorBoundary>
                </div>
              )}

              {/* Fallback image chart */}
              {msg.chart_url && !msg.chart_json && (
                <div className="chart-container">
                  <img
                    src={`${apiBaseUrl}${msg.chart_url}`}
                    alt="Chart"
                    style={{ maxWidth: '100%', borderRadius: '8px', display: 'block' }}
                  />
                </div>
              )}

              {/* Export Button */}
              {msg.export_url && (
                <a
                  href={`${apiBaseUrl}${msg.export_url}`}
                  className="export-btn"
                  download
                  target="_blank"
                  rel="noreferrer"
                >
                  <FiDownload className="eb-icon" size={13} />
                  Export Results
                </a>
              )}
            </div>
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
}

export default MessageBubble;
