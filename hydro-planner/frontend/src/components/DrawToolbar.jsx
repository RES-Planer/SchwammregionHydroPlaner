import React, { useState } from 'react';

const BUTTON_BASE = {
  display: 'block',
  width: '36px',
  height: '36px',
  margin: '4px 0',
  border: '1px solid #ccc',
  borderRadius: '4px',
  background: '#fff',
  cursor: 'pointer',
  fontSize: '18px',
  lineHeight: '36px',
  textAlign: 'center',
  boxShadow: '0 1px 4px rgba(0,0,0,0.3)',
  userSelect: 'none',
  touchAction: 'manipulation',
};

const BUTTON_ACTIVE = {
  ...BUTTON_BASE,
  background: '#4a90d9',
  color: '#fff',
  borderColor: '#2a70b9',
};

export default function DrawToolbar({ onModeChange, onDeleteAll }) {
  const [activeMode, setActiveMode] = useState('simple_select');

  const activate = (mode) => {
    setActiveMode(mode);
    onModeChange(mode);
  };

  return (
    <div
      style={{
        position: 'absolute',
        top: '10px',
        left: '10px',
        zIndex: 10,
        display: 'flex',
        flexDirection: 'column',
        gap: '2px',
      }}
    >
      <button
        title="Auswählen"
        style={activeMode === 'simple_select' ? BUTTON_ACTIVE : BUTTON_BASE}
        onClick={() => activate('simple_select')}
      >
        ↖
      </button>
      <button
        title="Polygon zeichnen"
        style={activeMode === 'draw_polygon' ? BUTTON_ACTIVE : BUTTON_BASE}
        onClick={() => activate('draw_polygon')}
      >
        ⬡
      </button>
      <button
        title="Alles löschen"
        style={BUTTON_BASE}
        onClick={() => {
          onDeleteAll();
          setActiveMode('simple_select');
        }}
      >
        🗑
      </button>
    </div>
  );
}
