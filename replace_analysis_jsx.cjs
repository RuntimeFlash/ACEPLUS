const fs = require('fs');
const file = '/home/ayushpandey/Code/aceplus/src/components/TestAnalysis.jsx';
let content = fs.readFileSync(file, 'utf8');

// Replace getDivisionColor
content = content.replace(
  /const getDivisionColor = \(division\) => \{[\s\S]*?return colors\[division\] \|\| '#8B4513'; \/\/ Brown for fallback\n  \};/,
  `const getDivisionColor = (division) => {
    const colors = {
      A: 'var(--gradient-math)',
      B: 'var(--gradient-science)',
      C: 'var(--gradient-english)',
      D: 'var(--gradient-ss)'
    };
    return colors[division] || 'var(--gradient-math)';
  };`
);

// Replace backgroundColor assignment
content = content.replace(
  /style={{ backgroundColor: getDivisionColor\(division\), color: '#ffffff' }}/g,
  `style={{ background: getDivisionColor(division), color: 'var(--text-primary)' }}`
);

// Replace color: '#ffffff' inside style
content = content.replace(
  /color: '#ffffff'/g,
  `color: 'var(--text-primary)'`
);

// Replace chart colors
content = content.replace(
  /backgroundColor: \[\s*'#4CAF50',\s*'#2196F3',\s*'#FFC107',\s*'#9C27B0',\s*'#FF5722'\s*\]/g,
  `backgroundColor: ['var(--color-math)', 'var(--color-science)', 'var(--color-english)', 'var(--color-ss)', 'var(--primary)']`
);
content = content.replace(
  /borderColor: \[\s*'#4CAF50',\s*'#2196F3',\s*'#FFC107',\s*'#9C27B0',\s*'#FF5722'\s*\]/g,
  `borderColor: ['var(--color-math)', 'var(--color-science)', 'var(--color-english)', 'var(--color-ss)', 'var(--primary)']`
);
content = content.replace(
  /backgroundColor: \['#4CAF50', '#ff6b6b'\]/g,
  `backgroundColor: ['var(--success)', 'var(--error)']`
);
content = content.replace(
  /borderColor: \['#4CAF50', '#ff6b6b'\]/g,
  `borderColor: ['var(--success)', 'var(--error)']`
);
content = content.replace(
  /backgroundColor: '#2196F3'/g,
  `backgroundColor: 'var(--color-ss)'`
);
content = content.replace(
  /borderColor: '#2196F3'/g,
  `borderColor: 'var(--color-ss)'`
);

fs.writeFileSync(file, content, 'utf8');
console.log('done');
