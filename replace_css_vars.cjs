const fs = require('fs');
const file = '/home/ayushpandey/Code/aceplus/src/components/CreateTest.css';
let content = fs.readFileSync(file, 'utf8');

// Remove :root block
content = content.replace(/:root\s*\{[^}]+\}/, '');

const replacements = {
  '--primary-color': '--primary',
  '--secondary-color': '--primary-hover',
  '--bg-color': '--bg-base',
  '--card-bg-color': '--bg-raised',
  '--input-bg-color': '--bg-surface',
  '--text-color': '--text-primary',
  '--text-color-secondary': '--text-secondary',
  '--border-color': '--border-subtle',
  '--border-color-hover': '--border-default',
  '--success-color': '--success',
  '--error-color': '--error'
};

for (const [oldVar, newVar] of Object.entries(replacements)) {
  content = content.replace(new RegExp(oldVar, 'g'), newVar);
}

fs.writeFileSync(file, content, 'utf8');
console.log('done');
