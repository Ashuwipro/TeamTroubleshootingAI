# SFTP Integration Implementation Summary

## Overview
This document summarizes the implementation of SFTP directory browsing functionality for the Saas-N, Saas-P Non Prod, and Saas-P Prod servers in the Drop File modal.

## Components Implemented

### 1. Backend Changes (app.py)

#### Added Imports
- `import stat` - For checking if SFTP items are directories
- `import paramiko` - SFTP library
- `from paramiko import SSHClient, AutoAddPolicy` - SSH client for SFTP connections

#### New Endpoint: `/api/sftp-directory`
**Method:** GET
**Parameters:**
- `saas` - Server section (saasN, saasPNonProd, or saasPProd)
- `path` - Remote path to browse (default: '/')

**Functionality:**
1. Retrieves login credentials from `login_credentials.json` for the specified server
2. Retrieves connection info (hostname, port) from `connection_info.json`
3. Establishes SSH connection using Paramiko
4. Lists directory contents with file/directory identification
5. Returns directory structure in JSON format

**Response Format:**
```json
{
  "path": "/current/path",
  "parentPath": "/parent/path",
  "entries": [
    {
      "name": "directory_name",
      "path": "/current/path/directory_name",
      "entryType": "directory",
      "size": 4096,
      "modified": 1712525632
    }
  ]
}
```

**Error Handling:**
- Authentication failures (401)
- Connection failures (500)
- Permission denied errors (403)

### 2. Frontend Changes (index.html)

#### Modified RightPanelModule
- **loadDirectory()** - Updated to call `/api/sftp-directory` endpoint instead of `/api/directory-tree`
- **buildPathCrumbs()** - Updated to handle Unix-style forward slashes for remote paths
- **updatePathHeader()** - Changed path separator from backslash to forward slash

#### Updated DropFileModule
- **openModal()** - Now triggers RightPanelModule to load SFTP directory when modal opens

### 3. Dependencies

#### Updated requirements.txt
Added: `paramiko` - Python SFTP/SSH library

## How It Works

### User Flow
1. User clicks "Drop File" button
2. Drop File modal opens
3. Right panel automatically loads Saas-N tab with SFTP directory structure
4. User can click on directories to navigate
5. System credentials from login_credentials.json are used automatically
6. Connection info from connection_info.json determines which server to connect to

### Technical Flow
1. Frontend calls `RightPanelModule.switchTab('saas-n')`
2. This calls `loadDirectory(tabId, '')`  with empty path
3. Frontend fetches `/api/sftp-directory?saas=saasN&path=/`
4. Backend reads credentials and connection info
5. Backend establishes SFTP connection
6. Backend lists directory contents
7. Frontend renders directory tree with clickable entries

## Features

### Navigation
- Click on directories to navigate deeper
- "Up one level" button to go to parent directory
- Breadcrumb navigation showing current path
- Clickable path segments for quick navigation

### Directory Operations
- Automatic sorting (directories first, then files)
- File/directory type identification
- Path display in Unix format (e.g., /path/to/directory)

### Error Handling
- Authentication failures display appropriate error messages
- Permission denied shows error but allows going back
- Connection failures handled gracefully

## Configuration

### Credentials Required
Users must have entered credentials in the Login popup:
- Username for Saas-N
- Password for Saas-N

### Connection Info Used
From connection_info.json:
- **Saas-N:** pcmqaftp.bottomline.com:2222
- **Saas-P Non Prod:** pcmtestftp.bottomline.com:2222
- **Saas-P Prod:** pcmftp.bottomline.com:2222

Protocol: SFTP (configured in UI but backend uses SFTP via Paramiko)

## Testing Checklist

- [ ] Flask app starts without errors
- [ ] SFTP endpoint is accessible
- [ ] Can retrieve directory listing from Saas-N with valid credentials
- [ ] Navigation to subdirectories works
- [ ] Back button works correctly
- [ ] Error handling for invalid credentials
- [ ] Error handling for permission denied
- [ ] UI displays directory structure correctly
- [ ] Breadcrumb navigation works
- [ ] Tab switching between Saas-N, Saas-P Non Prod, Saas-P Prod works

## Notes

- Paramiko automatically accepts host keys via AutoAddPolicy (for non-production use)
- Timeout set to 10 seconds for SSH connections
- Directories sorted before files for better UX
- Path handling supports both Windows and Unix-style paths on frontend
- SFTP connections are closed after each request to avoid resource leaks

