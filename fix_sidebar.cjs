const fs = require('fs');
let code = fs.readFileSync('/home/ayushpandey/Code/aceplus/src/components/ExamResults.jsx', 'utf8');
code = code.replace(/\.sidebar:hover ~ & \{[\s\S]*?\}/, '');
fs.writeFileSync('/home/ayushpandey/Code/aceplus/src/components/ExamResults.jsx', code);
