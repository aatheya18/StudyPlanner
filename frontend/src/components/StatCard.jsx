import React from 'react';

export default function StatCard({ icon: Icon, value, label, accentColor }) {
  return (
    <div className="stat-card" style={accentColor ? { borderLeftColor: accentColor } : {}}>
      <div className="stat-icon" style={accentColor ? { color: accentColor, backgroundColor: `${accentColor}18` } : {}}>
        {Icon && <Icon size={24} />}
      </div>
      <div className="stat-info">
        <div className="stat-value">{value}</div>
        <div className="stat-label">{label}</div>
      </div>
    </div>
  );
}
