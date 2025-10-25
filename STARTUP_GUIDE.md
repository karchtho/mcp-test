# Cours-MCP Startup Guide

## Project Overview
This project is an MCP (Model Context Protocol) server that manages educational courses in a MySQL database. It provides:
- A Flask web interface for uploading and managing courses
- An MCP server for Claude to search and add courses
- Integration with ngrok for public access

## Prerequisites
- Python 3.8+
- MySQL server running
- ngrok installed (or download from https://ngrok.com/download)

## Initial Setup

### 1. Database Setup
First, create the MySQL database and table:

```bash
mysql -u root -p
```

Then execute:
```sql
CREATE DATABASE cours_mcp CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE cours_mcp;

CREATE TABLE cours (
    id INT AUTO_INCREMENT PRIMARY KEY,
    titre VARCHAR(255) NOT NULL,
    matiere VARCHAR(100),
    type_contenu ENUM('cours', 'exercice', 'corrige') DEFAULT 'cours',
    contenu TEXT NOT NULL,
    date_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_titre (titre),
    INDEX idx_matiere (matiere),
    FULLTEXT INDEX idx_contenu (contenu)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 2. Configure Database Credentials
Edit [config.py](config.py) with your MySQL credentials:
```python
DATABASE_CONFIG = {
    'host': 'localhost',
    'user': 'YOUR_USERNAME',
    'password': 'YOUR_PASSWORD',
    'database': 'cours_mcp',
    'charset': 'utf8mb4'
}
```

### 3. Virtual Environment Setup
Activate the virtual environment and install dependencies:

```bash
# Activate virtual environment
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

## Starting the Application

### Option 1: Manual Start (for development)

Open 3 separate terminal windows:

**Terminal 1 - MCP Server:**
```bash
cd /home/ubuntu/cours-mcp
source venv/bin/activate
python server.py
```

**Terminal 2 - Web Interface:**
```bash
cd /home/ubuntu/cours-mcp
source venv/bin/activate
python web_interface.py
# Server will start on http://localhost:5000
```

**Terminal 3 - ngrok Tunnel:**
```bash
cd /home/ubuntu/cours-mcp
./ngrok http 5000
# Copy the public URL from the output (e.g., https://xxxx.ngrok-free.app)
```

### Option 2: Quick Start Script
Create a startup script:

```bash
# Create start.sh
cat > start.sh << 'EOF'
#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Start web interface in background
python web_interface.py &
WEB_PID=$!

# Start ngrok in background
./ngrok http 5000 --log=stdout > ngrok.log 2>&1 &
NGROK_PID=$!

# Wait for ngrok to start
sleep 3

# Display ngrok URL
echo "==================================="
echo "Services started successfully!"
echo "==================================="
echo "Web Interface: http://localhost:5000"
echo "Ngrok URL:"
curl -s http://localhost:4040/api/tunnels | python -m json.tool | grep -i "public_url"
echo ""
echo "MCP Server: Run 'python server.py' in another terminal"
echo ""
echo "To stop services:"
echo "  kill $WEB_PID $NGROK_PID"
echo "==================================="

# Save PIDs to file for easy cleanup
echo "$WEB_PID" > .pids
echo "$NGROK_PID" >> .pids
EOF

chmod +x start.sh
```

Then run:
```bash
./start.sh
```

## Using the Application

### Web Interface
1. Access http://localhost:5000 (local) or your ngrok URL (public)
2. Upload .md or .txt course files
3. Or add courses manually via the form
4. View all courses at /list

### MCP Server (with Claude)
The MCP server provides two tools for Claude:

1. **rechercher_cours**: Search courses by keyword
2. **ajouter_cours**: Add new courses

Configure Claude Desktop to use the MCP server by adding to your Claude config:
```json
{
  "mcpServers": {
    "cours-mcp": {
      "command": "python3",
      "args": ["/home/ubuntu/cours-mcp/server.py"],
      "env": {
        "PATH": "/home/ubuntu/cours-mcp/venv/bin:/usr/bin:/bin"
      }
    }
  }
}
```

## Stopping the Application

If using the startup script:
```bash
# Read PIDs and kill processes
kill $(cat .pids)
rm .pids
```

If started manually, press Ctrl+C in each terminal.

## Troubleshooting

### Database Connection Errors
- Verify MySQL is running: `sudo systemctl status mysql`
- Check credentials in [config.py](config.py)
- Ensure database exists: `mysql -u root -p -e "SHOW DATABASES;"`

### Port Already in Use
- Flask (5000): `lsof -ti:5000 | xargs kill -9`
- ngrok (4040): `pkill ngrok`

### ngrok Not Found
If ngrok binary is not executable:
```bash
tar xvzf ngrok-v3-stable-linux-amd64.tgz
chmod +x ngrok
```

### MCP Server Issues
- Ensure virtual environment is activated
- Check Python version: `python --version` (should be 3.8+)
- Reinstall dependencies: `pip install -r requirements.txt`

## Project Structure
```
cours-mcp/
├── server.py              # MCP server for Claude integration
├── web_interface.py       # Flask web interface
├── config.py              # Database configuration
├── http_adapter.py        # HTTP adapter utilities
├── mcp-config.json        # MCP server configuration
├── requirements.txt       # Python dependencies
├── uploads/               # Uploaded course files
├── venv/                  # Virtual environment
└── STARTUP_GUIDE.md       # This file
```

## Quick Reference

| Service | Command | Port/Access |
|---------|---------|-------------|
| Web Interface | `python web_interface.py` | http://localhost:5000 |
| MCP Server | `python server.py` | stdio (for Claude) |
| ngrok | `./ngrok http 5000` | Public URL + http://localhost:4040 (dashboard) |

## Additional Notes
- The uploads folder stores uploaded course files
- Web interface runs on port 5000 by default
- ngrok dashboard accessible at http://localhost:4040
- MCP server communicates via stdio (standard input/output)
