import { FiDownload } from 'react-icons/fi';
import './MessageBubble.css'; // Relies on the same export-btn styles

function ExportButton({ url, label = "Export Results" }) {
  if (!url) return null;

  return (
    <a 
      href={url}
      className="export-btn"
      download
      target="_blank"
      rel="noreferrer"
    >
      <FiDownload className="eb-icon" size={13} />
      {label}
    </a>
  );
}

export default ExportButton;
