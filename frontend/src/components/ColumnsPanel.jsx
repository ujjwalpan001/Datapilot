import { FiLayers, FiChevronRight } from 'react-icons/fi';
import './ColumnsPanel.css';

function ColumnsPanel({ columns, onColumnClick }) {
  if (!columns || columns.length === 0) return null;

  return (
    <aside className="columns-panel" id="columns-panel">
      {/* Header */}
      <div className="columns-header">
        <div className="columns-header-title">
          <div className="ch-icon">
            <FiLayers size={11} />
          </div>
          <span>Schema</span>
          <div className="columns-count-badge">{columns.length}</div>
        </div>
        <div className="columns-header-hint">Click a column to analyze</div>
      </div>

      {/* Column List */}
      <div className="columns-scroll">
        {columns.map((col, idx) => (
          <div
            key={idx}
            className="column-item"
            onClick={() => onColumnClick(col)}
            title={`Analyze "${col}"`}
            style={{ animationDelay: `${idx * 0.03}s` }}
          >
            <div className="col-type-badge">#</div>
            <span className="col-name">{col}</span>
            <FiChevronRight className="col-arrow" size={10} />
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="columns-footer">
        {columns.length} columns detected
      </div>
    </aside>
  );
}

export default ColumnsPanel;
