const fs = require('fs');
const file = '/home/ayushpandey/Code/aceplus/src/components/UnsubmittedExamPopup.css';
let content = fs.readFileSync(file, 'utf8');

// Remove :root
content = content.replace(/:root\s*\{[^}]+\}/, '');

const replacements = {
  'var\\(--surface\\)': 'var(--bg-raised)',
  'var\\(--surface-hover\\)': 'var(--bg-hover)',
  'var\\(--text\\)': 'var(--text-primary)',
  'var\\(--text-muted\\)': 'var(--text-secondary)',
  'var\\(--border\\)': 'var(--border-subtle)',
  'var\\(--border-strong\\)': 'var(--border-default)',
  'var\\(--shadow-strong\\)': 'var(--shadow-xl)',
  'var\\(--ring\\)': '0 0 0 3px var(--primary-glow)',
  'var\\(--blue-400\\)': 'var(--info)',
  'var\\(--blue-500\\)': 'var(--primary-hover)',
  'var\\(--blue-600\\)': 'var(--primary)',
  'var\\(--blue-700\\)': 'var(--primary-muted)',
  'linear-gradient\\(135deg, rgba\\(15, 23, 42, 0\\.95\\), rgba\\(2, 6, 23, 0\\.92\\)\\)': 'var(--bg-raised)',
  'radial-gradient\\(circle at 50% 50%, rgba\\(59, 130, 246, 0\\.08\\), transparent\\)': 'none',
  'rgba\\(59, 130, 246, 0\\.35\\)': 'var(--border-default)',
  'rgba\\(59, 130, 246, 0\\.55\\)': 'var(--border-focus)',
  'rgba\\(255, 255, 255, 0\\.03\\)': 'transparent',
  'rgba\\(59, 130, 246, 0\\.15\\)': 'var(--border-subtle)',
  'rgba\\(37, 99, 235, 0\\.12\\)': 'transparent',
  'rgba\\(37, 99, 235, 0\\.28\\)': 'transparent',
  'rgba\\(37, 99, 235, 0\\.35\\)': 'transparent',
  'rgba\\(239, 68, 68, 0\\.12\\)': 'var(--error-soft)',
  'rgba\\(239, 68, 68, 0\\.35\\)': 'var(--error)',
  'rgba\\(239, 68, 68, 0\\.25\\)': 'transparent',
  'linear-gradient\\(135deg, #ef4444, #dc2626\\)': 'var(--error)',
  'linear-gradient\\(135deg, #ef4444, #b91c1c\\)': 'var(--error)',
  '#ef4444': 'var(--error)'
};

for (const [oldVar, newVar] of Object.entries(replacements)) {
  content = content.replace(new RegExp(oldVar, 'g'), newVar);
}

fs.writeFileSync(file, content, 'utf8');
console.log('done');
