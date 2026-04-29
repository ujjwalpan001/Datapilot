import React from 'react';
import ReactPlotly from 'react-plotly.js';

// Vite CommonJS interop: sometimes default exports are nested in a .default property
const Plot = ReactPlotly.default || ReactPlotly;

function PlotlyChart({ chartJsonStr }) {
  if (!chartJsonStr) return null;

  try {
    const chartData = typeof chartJsonStr === 'string' ? JSON.parse(chartJsonStr) : chartJsonStr;
    
    // Ensure responsive layout and premium 3D dark theme styling
    const layout = {
      ...(chartData.layout || {}),
      autosize: true,
      margin: { t: 50, r: 20, l: 50, b: 50 },
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
      font: { 
        color: '#f0eeff', 
        family: '"Outfit", "Inter", sans-serif',
        size: 11
      },
      colorway: ['#7c3aed', '#06b6d4', '#ec4899', '#f59e0b', '#10b981'],
      xaxis: {
        ...(chartData.layout?.xaxis || {}),
        gridcolor: 'rgba(124, 58, 237, 0.1)',
        zerolinecolor: 'rgba(124, 58, 237, 0.2)',
        tickfont: { color: '#9b95c9' }
      },
      yaxis: {
        ...(chartData.layout?.yaxis || {}),
        gridcolor: 'rgba(124, 58, 237, 0.1)',
        zerolinecolor: 'rgba(124, 58, 237, 0.2)',
        tickfont: { color: '#9b95c9' }
      }
    };

    return (
      <div className="chart-wrapper" style={{ 
        width: '100%', 
        minHeight: '320px', 
        padding: '10px 0',
        background: 'radial-gradient(circle at 50% 50%, rgba(124, 58, 237, 0.05) 0%, transparent 70%)',
        borderRadius: '12px'
      }}>
        <Plot
          data={chartData.data || []}
          layout={layout}
          config={{ 
            responsive: true, 
            displayModeBar: true,
            displaylogo: false,
            modeBarButtonsToRemove: ['lasso2d', 'select2d']
          }}
          style={{ width: '100%', height: '100%' }}
          useResizeHandler={true}
        />
      </div>
    );
  } catch (err) {
    console.error("Failed to parse Plotly JSON or render", err);
    return <div style={{ color: '#ec4899', fontSize: '0.8rem', padding: '10px' }}>Failed to render chart: {err.message}</div>;
  }
}

export default PlotlyChart;
