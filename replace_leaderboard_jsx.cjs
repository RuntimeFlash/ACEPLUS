const fs = require('fs');
const file = '/home/ayushpandey/Code/aceplus/src/components/LeaderboardPopup.jsx';
let content = fs.readFileSync(file, 'utf8');

const replacements = {
  'rgba\\(0, 0, 0, 0\\.6\\)': 'var(--bg-overlay)',
  'rgba\\(26, 26, 26, 0\\.95\\)': 'var(--bg-raised)',
  '#333': 'var(--border-subtle)',
  '#222': 'var(--bg-surface)',
  '#444': 'var(--border-default)',
  '#555': 'var(--border-focus)',
  'color: #fff;': 'color: var(--text-primary); font-family: var(--font-display);',
  'color: #999;': 'color: var(--text-secondary);',
  'color: #ccc;': 'color: var(--text-secondary);',
  'color: #666;': 'color: var(--text-muted);',
  '#ff6b6b': 'var(--error)',
  '#4dabf7': 'var(--info)',
  'rgba\\(255, 0, 0, 0\\.1\\)': 'var(--error-soft)',
  'rgba\\(255, 0, 0, 0\\.15\\)': 'var(--error-soft)',
  'rgba\\(255, 215, 0, 0\\.15\\)': 'var(--accent-soft)',
  'rgba\\(255, 215, 0, 0\\.2\\)': 'var(--accent-soft)',
  'rgba\\(192, 192, 192, 0\\.15\\)': 'rgba(255, 255, 255, 0.1)',
  'rgba\\(192, 192, 192, 0\\.2\\)': 'rgba(255, 255, 255, 0.15)',
  'backgroundColor: \\\'rgba\\(26, 26, 26, 0\\.95\\)\\\'': 'backgroundColor: \'var(--bg-raised)\''
};

for (const [oldVar, newVar] of Object.entries(replacements)) {
  content = content.replace(new RegExp(oldVar, 'g'), newVar);
}

// hover background fallback
content = content.replace(/return '#222';/g, "return 'var(--bg-hover)';");

fs.writeFileSync(file, content, 'utf8');
console.log('done');
