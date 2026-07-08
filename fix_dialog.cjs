const fs = require('fs');
const file = '/home/ayushpandey/Code/aceplus/src/components/CreateTest.jsx';
let content = fs.readFileSync(file, 'utf8');

// Remove import exactly
content = content.replace(/import \{ Dialog \} from '@mui\/material';\r?\n/, '');

// Replace closing tags
content = content.replace(/<\/Dialog>/g, '</div></div>)}');

fs.writeFileSync(file, content, 'utf8');
console.log('done');
