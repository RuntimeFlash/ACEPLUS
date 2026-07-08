const fs = require('fs');
const file = '/home/ayushpandey/Code/aceplus/src/components/TestAnalysis.css';
let content = fs.readFileSync(file, 'utf8');

const replacements = {
  'var(--background-color, #121212)': 'var(--bg-base)',
  '#121212': 'var(--bg-base)',
  '#1a1a1a': 'var(--bg-raised)',
  '#2d3748': 'var(--bg-surface)',
  '#4a5568': 'var(--border-default)',
  '#ffffff': 'var(--text-primary)',
  '#b3b3b3': 'var(--text-secondary)',
  '#a0aec0': 'var(--text-secondary)',
  '#e2e8f0': 'var(--text-secondary)',
  '#4CAF50': 'var(--primary)',
  '#3d8b40': 'var(--primary-hover)',
  '#FFC107': 'var(--warning)',
  '#ff6b6b': 'var(--error)'
};

for (const [oldVar, newVar] of Object.entries(replacements)) {
  content = content.replace(new RegExp(oldVar, 'g'), newVar);
}

// Add pill styles to nav-button
content = content.replace(
  /\.nav-button \{([^}]+)\}/,
  `.nav-button {
  background: var(--bg-surface);
  color: var(--text-primary);
  border: 1px solid var(--border-default);
  padding: 0.5rem 1.5rem;
  border-radius: var(--radius-full);
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s ease;
}`
);

fs.writeFileSync(file, content, 'utf8');
console.log('done');
