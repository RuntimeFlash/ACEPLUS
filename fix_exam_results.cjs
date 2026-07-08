const fs = require('fs');
let code = fs.readFileSync('/home/ayushpandey/Code/aceplus/src/components/ExamResults.jsx', 'utf8');

// Margins and structural fixes based on rules
code = code.replace(/margin-left: 80px;[\s\S]*?margin-left: 220px;\n\s*\}/, '');
code = code.replace(/@media \(max-width: 768px\) \{\n\s*margin-left: 0;/g, '@media (max-width: 768px) {');

// Colors replacement
// #1a1a1a -> var(--bg-raised)
code = code.replace(/#1a1a1a/g, 'var(--bg-raised)');
// #1E1E1E -> var(--bg-raised)
code = code.replace(/#1E1E1E/g, 'var(--bg-raised)');
// #2D2D2D -> var(--bg-hover)
code = code.replace(/#2D2D2D/g, 'var(--bg-hover)');
// #2a2a2a, #242424, #1f1f1f, #222 -> var(--bg-surface)
code = code.replace(/#2a2a2a/g, 'var(--bg-surface)');
code = code.replace(/#242424/g, 'var(--bg-surface)');
code = code.replace(/#1f1f1f/g, 'var(--bg-surface)');
code = code.replace(/#222/g, 'var(--bg-surface)');
// #383838 -> var(--border-default)
code = code.replace(/#383838/g, 'var(--border-default)');
// #333 -> var(--border-subtle)
code = code.replace(/#333/g, 'var(--border-subtle)');

// #ffffff, #fff, #e0e0e0, #b3b3b3 -> var(--text-primary)
code = code.replace(/#ffffff/g, 'var(--text-primary)');
code = code.replace(/#fff/g, 'var(--text-primary)');
code = code.replace(/#e0e0e0/g, 'var(--text-primary)');
code = code.replace(/#b3b3b3/g, 'var(--text-secondary)');
// #b0b0b0, #888, #666 -> var(--text-muted) or var(--text-secondary)
code = code.replace(/#b0b0b0/g, 'var(--text-secondary)');
code = code.replace(/#888/g, 'var(--text-muted)');
code = code.replace(/#666/g, 'var(--text-muted)');

// Primary colors
// #4a90e2, #667eea -> var(--primary)
code = code.replace(/#4a90e2/g, 'var(--primary)');
code = code.replace(/#667eea/g, 'var(--primary)');

// Success colors
// #4caf50, #4CAF50, #81c784, #81C784 -> var(--success)
code = code.replace(/#4caf50/gi, 'var(--success)');
code = code.replace(/#81c784/gi, 'var(--success)');

// Warning colors
// #ff9800, #FF9800, #ffb74d, #FFB74D -> var(--warning)
code = code.replace(/#ff9800/gi, 'var(--warning)');
code = code.replace(/#ffb74d/gi, 'var(--warning)');

// Error colors
// #f44336, #F44336, #e57373, #E57373 -> var(--error)
code = code.replace(/#f44336/gi, 'var(--error)');
code = code.replace(/#e57373/gi, 'var(--error)');

// Alpha transparent backgrounds
code = code.replace(/rgba\(76, 175, 80, 0\.1\)/g, 'var(--success-soft)');
code = code.replace(/rgba\(76, 175, 80, 0\.12\)/g, 'var(--success-soft)');
code = code.replace(/rgba\(76, 175, 80, 0\.18\)/g, 'var(--success-soft)');
code = code.replace(/rgba\(255, 152, 0, 0\.1\)/g, 'var(--warning-soft)');
code = code.replace(/rgba\(244, 67, 54, 0\.1\)/g, 'var(--error-soft)');
code = code.replace(/rgba\(244, 67, 54, 0\.12\)/g, 'var(--error-soft)');
code = code.replace(/rgba\(244, 67, 54, 0\.18\)/g, 'var(--error-soft)');
code = code.replace(/rgba\(74, 144, 226, 0\.1\)/g, 'var(--primary-soft)');
code = code.replace(/rgba\(74, 144, 226, 0\.3\)/g, 'var(--primary-glow)');

// Gray backgrounds
code = code.replace(/rgba\(255, 255, 255, 0\.02\)/g, 'var(--bg-base)');
code = code.replace(/rgba\(255, 255, 255, 0\.03\)/g, 'var(--bg-surface)');
code = code.replace(/rgba\(255, 255, 255, 0\.05\)/g, 'var(--bg-hover)');
code = code.replace(/rgba\(255, 255, 255, 0\.08\)/g, 'var(--bg-hover)');
code = code.replace(/rgba\(255, 255, 255, 0\.1\)/g, 'var(--border-default)');
code = code.replace(/rgba\(255, 255, 255, 0\.06\)/g, 'var(--border-subtle)');

// Shadows
code = code.replace(/rgba\(0, 0, 0, 0\.2\)/g, 'var(--shadow-md)');
code = code.replace(/rgba\(0, 0, 0, 0\.1\)/g, 'var(--shadow-sm)');
code = code.replace(/rgba\(0, 0, 0, 0\.12\)/g, 'var(--shadow-sm)');

fs.writeFileSync('/home/ayushpandey/Code/aceplus/src/components/ExamResults.jsx', code);
