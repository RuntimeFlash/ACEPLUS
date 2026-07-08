const fs = require('fs');

const fixSizes = (filePath) => {
  let code = fs.readFileSync(filePath, 'utf8');
  code = code.replace(/font-size:\s*0\.75rem;/g, 'font-size: var(--text-xs);');
  code = code.replace(/font-size:\s*0\.8[0-9]*rem;/g, 'font-size: var(--text-sm);');
  code = code.replace(/font-size:\s*0\.9[0-9]*rem;/g, 'font-size: var(--text-sm);');
  code = code.replace(/font-size:\s*1rem;/g, 'font-size: var(--text-base);');
  code = code.replace(/font-size:\s*1\.1rem;/g, 'font-size: var(--text-lg);');
  code = code.replace(/font-size:\s*1\.2rem;/g, 'font-size: var(--text-lg);');
  code = code.replace(/font-size:\s*1\.3rem;/g, 'font-size: var(--text-xl);');
  code = code.replace(/font-size:\s*1\.4rem;/g, 'font-size: var(--text-xl);');
  code = code.replace(/font-size:\s*1\.5rem;/g, 'font-size: var(--text-2xl);');
  code = code.replace(/font-size:\s*1\.6rem;/g, 'font-size: var(--text-2xl);');
  code = code.replace(/font-size:\s*1\.8rem;/g, 'font-size: var(--text-3xl);');
  code = code.replace(/font-size:\s*2rem;/g, 'font-size: var(--text-3xl);');
  code = code.replace(/font-size:\s*2\.2rem;/g, 'font-size: var(--text-4xl);');
  
  // also spacing values that are commonly used:
  // 1rem -> var(--space-4)
  // 1.5rem -> var(--space-6)
  // 2rem -> var(--space-8)
  // 3rem -> var(--space-12)
  
  fs.writeFileSync(filePath, code);
};

fixSizes('/home/ayushpandey/Code/aceplus/src/components/ExamTaking.jsx');
fixSizes('/home/ayushpandey/Code/aceplus/src/components/ExamResults.jsx');
