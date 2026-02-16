const fs = require('fs');
const path = require('path');

// Read the English source file
const enUSPath = path.join(__dirname, '../src/locales/en_US.json');
const enUS = JSON.parse(fs.readFileSync(enUSPath, 'utf8'));
const enKeys = Object.keys(enUS);

// Update existing language files with missing keys
const languages = [
  { code: 'ar_SA', name: 'Arabic' },
  { code: 'zh_CN', name: 'Chinese' },
  { code: 'hi_IN', name: 'Hindi' }
];

languages.forEach(({ code, name }) => {
  const langPath = path.join(__dirname, '../src/locales', `${code}.json`);
  const langData = JSON.parse(fs.readFileSync(langPath, 'utf8'));

  let addedCount = 0;
  const updatedData = {};

  // Preserve the order from en_US.json and add missing keys
  enKeys.forEach(key => {
    if (Object.prototype.hasOwnProperty.call(langData, key)) {
      updatedData[key] = langData[key];
    } else {
      updatedData[key] = enUS[key]; // Use English as fallback
      addedCount++;
    }
  });

  // Write the updated file
  fs.writeFileSync(langPath, JSON.stringify(updatedData, null, 2), 'utf8');

  console.log(`✓ Updated ${name} (${code}):`);
  console.log(`  - Total keys: ${Object.keys(updatedData).length}`);
  console.log(`  - Added missing keys: ${addedCount}`);
  console.log(`  - Preserved existing translations: ${Object.keys(langData).length}`);
});

console.log('\n✅ All existing language files have been updated with missing keys!');
console.log('Missing keys use English text as fallback and should be translated.');
