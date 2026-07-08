const fs = require('fs');
const path = require('path');

const directoryPath = path.join(__dirname, 'src', 'components');

const replacements = [
  // Fonts
  { regex: /font-family:\s*['"]?(?:Roboto|Montserrat|Poppins|Inter|system-ui)[^;]*;/gi, replacement: 'font-family: var(--font-body);' },
  // General text colors
  { regex: /color:\s*#([Ff]{3}|[Ff]{6})\b/g, replacement: 'color: var(--text-primary)' },
  { regex: /color:\s*#([Aa86]{3}|[Aa86]{6})\b/g, replacement: 'color: var(--text-secondary)' },
  { regex: /color:\s*#333(?:333)?\b/gi, replacement: 'color: var(--text-primary)' },
  // Backgrounds
  { regex: /background(?:-color)?:\s*#1[a-eA-E0-9]{2,5}\b/gi, replacement: 'background: var(--bg-raised)' },
  { regex: /background(?:-color)?:\s*#2[a-eA-E0-9]{2,5}\b/gi, replacement: 'background: var(--bg-surface)' },
  { regex: /background(?:-color)?:\s*rgba\(0,\s*0,\s*0,\s*0\.[1-9]\)/g, replacement: 'background: rgba(0,0,0,0.3)' },
  // Success/Error/Warning
  { regex: /#4CAF50/gi, replacement: 'var(--success)' },
  { regex: /#F44336/gi, replacement: 'var(--error)' },
  { regex: /#FF9800/gi, replacement: 'var(--warning)' },
  { regex: /#2196[Ff]3/gi, replacement: 'var(--info)' },
  { regex: /#667eea/gi, replacement: 'var(--primary)' },
  { regex: /#764ba2/gi, replacement: 'var(--primary-hover)' },
  // Linear gradients for primary
  { regex: /linear-gradient\(to\s+right,\s*#667eea,\s*#764ba2\)/gi, replacement: 'linear-gradient(to right, var(--primary), var(--primary-hover))' },
  { regex: /linear-gradient\(135deg,\s*#667eea\s+0%,\s*#764ba2\s+100%\)/gi, replacement: 'linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%)' },
];

function processFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  let originalContent = content;

  replacements.forEach(({ regex, replacement }) => {
    content = content.replace(regex, replacement);
  });

  if (content !== originalContent) {
    fs.writeFileSync(filePath, content, 'utf8');
    console.log(`Updated: ${path.basename(filePath)}`);
  }
}

function traverseDirectory(dir) {
  const files = fs.readdirSync(dir);

  files.forEach(file => {
    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);

    if (stat.isDirectory()) {
      traverseDirectory(fullPath);
    } else if (stat.isFile() && (fullPath.endsWith('.jsx') || fullPath.endsWith('.js') || fullPath.endsWith('.css'))) {
      processFile(fullPath);
    }
  });
}

traverseDirectory(directoryPath);
console.log('Token replacement complete.');
