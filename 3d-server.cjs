const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 8082;

const server = http.createServer((req, res) => {
  // Serve the 3d-resume-analyzer.html file for all requests
  const filePath = path.join(__dirname, '3d-resume-analyzer.html');

  fs.readFile(filePath, (err, content) => {
    if (err) {
      res.writeHead(500);
      res.end(`Error loading the file: ${err.message}`);
      return;
    }

    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(content);
  });
});

server.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}/`);
  console.log('Open your browser and navigate to the URL above to see GIMME YOUR RESUME');
  console.log('Press Ctrl+C to stop the server');
});
