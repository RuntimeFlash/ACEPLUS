const fs = require('fs');

let takingCode = fs.readFileSync('/home/ayushpandey/Code/aceplus/src/components/ExamTaking.jsx', 'utf8');
takingCode = takingCode.replace(/font-family: 'Fira Code', monospace;/g, 'font-family: var(--font-mono);');
fs.writeFileSync('/home/ayushpandey/Code/aceplus/src/components/ExamTaking.jsx', takingCode);

let resultsCode = fs.readFileSync('/home/ayushpandey/Code/aceplus/src/components/ExamResults.jsx', 'utf8');
resultsCode = resultsCode.replace(/font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;/g, 'font-family: var(--font-body);');
fs.writeFileSync('/home/ayushpandey/Code/aceplus/src/components/ExamResults.jsx', resultsCode);

