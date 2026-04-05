import React, { useState } from 'react';
import './FriendPicker.css';

const friendsData = Array.from({ length: 9 }).map((_, idx) => ({
  id: idx + 1,
  name: `Friend ${idx + 1}`,
  img: `https://i.pravatar.cc/150?img=${idx + 1}`,
}));

const FriendPicker = () => {
  const [selected, setSelected] = useState(new Set());

  const toggleFriend = (id) => {
    const newSet = new Set(selected);
    if (newSet.has(id)) newSet.delete(id);
    else newSet.add(id);
    setSelected(newSet);
  };

  const selectedCount = selected.size;
  const minRequired = 3;

  return (
    <div className="fp-container">
      <div className="fp-header">
        <h2>Step 1 of 2</h2>
        <p>Select at least {minRequired} friends you know</p>
      </div>
      <div className="fp-grid">
        {friendsData.map((f) => (
          <div
            key={f.id}
            className={`fp-card ${selected.has(f.id) ? 'selected' : ''}`}
            onClick={() => toggleFriend(f.id)}
          >
            <img src={f.img} alt={f.name} />
            <span className="fp-name">{f.name}</span>
          </div>
        ))}
      </div>
      <div className="fp-footer">
        <span>{selectedCount} selected</span>
        <button disabled={selectedCount < minRequired}>Continue</button>
      </div>
    </div>
  );
};

export default FriendPicker;
