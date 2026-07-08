const fs = require('fs');
let code = fs.readFileSync('/home/ayushpandey/Code/aceplus/src/components/ExamTaking.jsx', 'utf8');

// ExamWrapper margins
code = code.replace(/margin-left: 70px;[\s\S]*?margin-left: 220px;\n\s*\}/, '');
code = code.replace(/padding-top: 60px; \/\* Account for header \*\//, '');
code = code.replace(/transition: margin-left 0\.3s ease-in-out;/, '');
code = code.replace(/@media \(max-width: 768px\) \{\n\s*margin-left: 0;\n\s*\}/, '');

// Colors
code = code.replace(/rgba\(255, 215, 0, 0\.1\)/g, 'var(--accent-soft)');
code = code.replace(/rgba\(255, 215, 0, 0\.2\)/g, 'var(--accent-soft)');
code = code.replace(/rgba\(255, 215, 0, 0\.05\)/g, 'var(--accent-soft)');
code = code.replace(/rgba\(255, 215, 0, 0\.15\)/g, 'var(--accent-soft)');
code = code.replace(/rgba\(255, 215, 0, 0\.3\)/g, 'var(--accent-soft)');
code = code.replace(/rgba\(255, 215, 0, 0\.4\)/g, 'var(--accent)');
code = code.replace(/rgba\(255, 215, 0, 0\.03\)/g, 'var(--accent-soft)');
code = code.replace(/rgba\(255, 215, 0, 0\.06\)/g, 'var(--accent-soft)');
code = code.replace(/#ffd700/g, 'var(--accent)');

code = code.replace(/#1a1a1a/g, 'var(--bg-raised)');
code = code.replace(/rgba\(0, 0, 0, 0\.2\)/g, 'var(--shadow-md)');
code = code.replace(/rgba\(255, 255, 255, 0\.1\)/g, 'var(--border-subtle)');
code = code.replace(/rgba\(255, 255, 255, 0\.2\)/g, 'var(--border-default)');
code = code.replace(/rgba\(255, 255, 255, 0\.05\)/g, 'var(--bg-surface)');
code = code.replace(/rgba\(255, 255, 255, 0\.08\)/g, 'var(--bg-hover)');
code = code.replace(/rgba\(255, 255, 255, 0\.03\)/g, 'var(--bg-surface)');
code = code.replace(/rgba\(255, 255, 255, 0\.02\)/g, 'var(--bg-base)');
code = code.replace(/#ffffff/g, 'var(--text-primary)');
code = code.replace(/#fff/g, 'var(--text-primary)');

code = code.replace(/rgba\(102, 126, 234, 0\.1\)/g, 'var(--primary-soft)');
code = code.replace(/rgba\(102, 126, 234, 0\.15\)/g, 'var(--primary-glow)');
code = code.replace(/rgba\(102, 126, 234, 0\.2\)/g, 'var(--border-focus)');
code = code.replace(/rgba\(102, 126, 234, 0\.3\)/g, 'var(--primary)');
code = code.replace(/#667eea/g, 'var(--primary)');

code = code.replace(/#2196f3/g, 'var(--primary)');
code = code.replace(/rgba\(79, 172, 254, 0\.1\)/g, 'var(--primary-soft)');
code = code.replace(/rgba\(79, 172, 254, 0\.05\)/g, 'var(--primary-glow)');

code = code.replace(/#666/g, 'var(--text-muted)');
code = code.replace(/#22c55e/g, 'var(--success)');
code = code.replace(/#dc2626/g, 'var(--error)');
code = code.replace(/#b0b0b0/g, 'var(--text-secondary)');

fs.writeFileSync('/home/ayushpandey/Code/aceplus/src/components/ExamTaking.jsx', code);
