const fs = require('fs');

const fixRadii = (filePath) => {
  let code = fs.readFileSync(filePath, 'utf8');
  code = code.replace(/border-radius:\s*4px/g, 'border-radius: var(--radius-sm)');
  code = code.replace(/border-radius:\s*6px/g, 'border-radius: var(--radius-sm)');
  code = code.replace(/border-radius:\s*8px/g, 'border-radius: var(--radius-md)');
  code = code.replace(/border-radius:\s*12px/g, 'border-radius: var(--radius-lg)');
  code = code.replace(/border-radius:\s*16px/g, 'border-radius: var(--radius-xl)');
  code = code.replace(/border-radius:\s*24px/g, 'border-radius: var(--radius-xl)');
  code = code.replace(/border-radius:\s*999px/g, 'border-radius: var(--radius-full)');
  code = code.replace(/border-radius:\s*0 4px 4px 0/g, 'border-radius: 0 var(--radius-sm) var(--radius-sm) 0');
  fs.writeFileSync(filePath, code);
};

fixRadii('/home/ayushpandey/Code/aceplus/src/components/ExamTaking.jsx');
fixRadii('/home/ayushpandey/Code/aceplus/src/components/ExamResults.jsx');
