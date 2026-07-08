const fs = require('fs');

let code = fs.readFileSync('/home/ayushpandey/Code/aceplus/src/components/ExamResults.jsx', 'utf8');
code = code.replace(/#FFF/g, 'var(--text-primary)');
code = code.replace(/#aaa/g, 'var(--text-secondary)');
code = code.replace(/#2196f3/g, 'var(--primary)');
fs.writeFileSync('/home/ayushpandey/Code/aceplus/src/components/ExamResults.jsx', code);
