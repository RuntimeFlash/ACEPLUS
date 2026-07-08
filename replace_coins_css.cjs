const fs = require('fs');
const file = '/home/ayushpandey/Code/aceplus/src/components/Coins.css';
let content = fs.readFileSync(file, 'utf8');

const replacements = {
  'rgba\\(28, 28, 30, 0\\.85\\)': 'var(--bg-raised)',
  'linear-gradient\\(135deg, #6a82fb, #fc5c7d\\)': 'var(--primary)',
  'linear-gradient\\(90deg, #6a82fb, #fc5c7d\\)': 'var(--primary)',
  '#ffc107': 'var(--accent)',
  'rgba\\(255, 193, 7, 0\\.15\\)': 'var(--accent-soft)',
  'rgba\\(255, 193, 7, 0\\.1\\)': 'var(--accent-soft)',
  '#2ecc71': 'var(--success)',
  'rgba\\(46, 204, 113, 0\\.2\\)': 'var(--success-soft)',
  'rgba\\(46, 204, 113, 0\\.3\\)': 'var(--success-soft)',
  'rgba\\(255, 255, 255, 0\\.07\\)': 'var(--bg-surface)',
  'rgba\\(255, 255, 255, 0\\.1\\)': 'var(--border-subtle)',
  'rgba\\(255, 255, 255, 0\\.2\\)': 'var(--border-default)',
  'rgba\\(106, 130, 251, 0\\.5\\)': 'var(--border-focus)',
  'rgba\\(106, 130, 251, 0\\.4\\)': 'var(--primary-glow)',
  '#f0f0f0': 'var(--text-primary)',
  '#fff': 'var(--text-primary)',
  'white': 'var(--text-primary)',
  '#b0b0b0': 'var(--text-secondary)',
  '#a0a0a0': 'var(--text-muted)',
  '#8a9ffc': 'var(--info)',
  'rgba\\(138, 159, 252, 0\\.1\\)': 'var(--info-soft)'
};

for (const [oldVar, newVar] of Object.entries(replacements)) {
  content = content.replace(new RegExp(oldVar, 'g'), newVar);
}

fs.writeFileSync(file, content, 'utf8');
console.log('done');
