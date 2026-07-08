const fs = require('fs');

let code = fs.readFileSync('/home/ayushpandey/Code/aceplus/src/components/ExamTaking.jsx', 'utf8');
code = code.replace(/rgba\(18, 18, 18, 0\.8\)/g, 'var(--bg-base)');
code = code.replace(/rgba\(102, 102, 102, 0\.3\)/g, 'var(--border-subtle)');
fs.writeFileSync('/home/ayushpandey/Code/aceplus/src/components/ExamTaking.jsx', code);
