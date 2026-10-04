// Get the current date and time
const now = new Date();

// Open the text file in append mode and write the current date and time
const fs = require('fs');
fs.appendFile('timestamps.txt', `${now}\n`, (err) => {
    if (err) throw err;
    console.log('The date and time have been saved!');
});
