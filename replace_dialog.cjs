const fs = require('fs');
const file = '/home/ayushpandey/Code/aceplus/src/components/CreateTest.jsx';
let content = fs.readFileSync(file, 'utf8');

// Remove import
content = content.replace("import { Dialog } from '@mui/material';\n", '');

// Replace <Dialog open={showPrivacyNotice} onClose={() => setShowPrivacyNotice(false)} PaperProps={{ className: 'privacy-dialog-paper' }}>
content = content.replace(
  /<Dialog open={showPrivacyNotice} onClose={\(\) => setShowPrivacyNotice\(false\)} PaperProps={{ className: 'privacy-dialog-paper' }}>/g,
  `{showPrivacyNotice && (
                    <div className="dialog-overlay" onClick={() => setShowPrivacyNotice(false)}>
                        <div className="privacy-dialog-paper" onClick={e => e.stopPropagation()}>`
);
// Need to find closing </Dialog> for privacy
content = content.replace(
  /<\/div>\n                <\/Dialog>/g,
  `</div>\n                        </div>\n                    </div>\n                )}`
);

// Replace no questions dialog
content = content.replace(
  /<Dialog open={showNoQuestionsDialog} onClose={handleCloseNoQuestionsDialog} PaperProps={{className: 'no-questions-dialog-paper'}}>/g,
  `{showNoQuestionsDialog && (
                    <div className="dialog-overlay" onClick={handleCloseNoQuestionsDialog}>
                        <div className="no-questions-dialog-paper" onClick={e => e.stopPropagation()}>`
);

// Replace other </Dialog>
content = content.replace(
  /<\/div>\n                 <\/Dialog>/g,
  `</div>\n                        </div>\n                    </div>\n                )}`
);

fs.writeFileSync(file, content, 'utf8');
console.log('done');
