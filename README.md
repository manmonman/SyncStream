\# SyncStream 🎵



\*\*SyncStream\*\* is a Python-based application for synchronized music listening. It allows one user to host a YouTube song, while others can join as listeners and stay in sync in real-time.  



---



\## Features



\- Host YouTube songs for others to listen live  

\- Listeners automatically sync to the hosted song  

\- Simple terminal-based interface with progress bar  

\- Cross-platform: works on Windows, Linux, macOS  



---



\## Installation



1\. \*\*Clone the repository\*\*:



&nbsp;   ```bash

&nbsp;   git clone https://github.com/yourusername/SyncStream.git

&nbsp;   cd SyncStream

&nbsp;   ```



2\. \*\*Create a virtual environment\*\* (recommended):



&nbsp;   ```bash

&nbsp;   python3 -m venv venv

&nbsp;   source venv/bin/activate  # Linux/macOS

&nbsp;   venv\\Scripts\\activate     # Windows

&nbsp;   ```



3\. \*\*Install dependencies\*\*:



&nbsp;   ```bash

&nbsp;   pip install -r requirement.txt

&nbsp;   ```



---



\## Configuration



SyncStream requires a WebSocket server URL to connect clients and host songs.  



1\. Create a `.env` file in the root directory:



&nbsp;   ```env

&nbsp;   SERVER\_URL=wss://your-server-url-here

&nbsp;   ```



2\. The `client.py` will read this URL to connect.  





---



\## Usage



\### Host a Song



```bash

python client.py





\## Server Setup and Deployment



SyncStream uses a WebSocket server to manage hosted song state and listener connections. You can run your own server locally or deploy it online.  



---







1\. Navigate to the server folder:



```bash

cd server





\## Server Setup and Deployment



SyncStream uses a WebSocket server to manage hosted song state and listener connections. You can run your own server locally or deploy it online.  







