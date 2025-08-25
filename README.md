# PDF Search Webapp (Flask + Whoosh)

A simple, Windows-friendly webapp to **upload PDFs** and **search by defect/keyword**, returning **which PDF and page** contains the term. No external services required.

## 🧰 What you get
- `Flask` web server with an upload form and search page
- `PyMuPDF` for fast per-page text extraction
- `Whoosh` full-text index (stores each page as a searchable document)
- Results show: file name, page number, highlighted snippet, and a link to open the PDF at that page

---

## ⚙️ Windows Setup (Step-by-step)

> **Requires:** Python 3.10+ on Windows. Get from https://www.python.org/downloads/

1) **Unzip this folder** somewhere easy (e.g., `C:\pdf-search-app`).  
2) Open **Windows PowerShell** in the unzipped folder (Shift + Right-click → *Open PowerShell window here*).  
3) Create a virtual environment:
```powershell
python -m venv .venv
```
4) Activate it:
```powershell
.\.venv\Scripts\Activate.ps1
```
If PowerShell blocks it, run once as admin:
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```
Then activate again.

5) Install dependencies:
```powershell
pip install -r requirements.txt
```

6) Put your PDFs in: `storage/pdfs/`  
   You can also upload via the web UI later.

7) **Index your PDFs** (build/search index for pages):
```powershell
python import_pdfs.py --folder storage/pdfs
```
You can re-run this anytime after adding/removing PDFs.

8) **Run the webapp**:
```powershell
$env:FLASK_APP="app.py"
flask run --host=0.0.0.0 --port=8000
```
Open **http://localhost:8000** on your computer.

> **Let teammates on same Wi‑Fi see it**
- Find your IP:
```powershell
ipconfig
```
Use the **IPv4 Address** (e.g., `192.168.1.45`), then share this URL:
```
http://192.168.1.45:8000
```
- If it doesn't open from other PCs, add a Windows Defender Firewall **Inbound Rule** allowing TCP **port 8000**.

> **Open to the internet (optional, simple)**
- Use a tunneling tool like **Cloudflare Tunnel** or **ngrok** (free tiers exist) and share the tunnel URL.

---

## 🔒 Optional simple login (Basic Auth)
Set two env vars before `flask run`:
```powershell
$env:BASIC_AUTH_USER="admin"
$env:BASIC_AUTH_PASS="strongpassword123"
```
Then start the app. The UI will prompt for a username/password.

---

## 🧪 Try it
1) Start the app.  
2) Go to **Upload** tab → add a few PDFs.  
3) Search `hydraulic leak` (or any defect type).  
4) Click a result → it opens the PDF at that page (`#page=N`).

---

## 🗂 Project structure
```
pdf-search-app/
├─ app.py                    # Flask app (upload + search UI)
├─ import_pdfs.py            # Bulk indexer for a folder
├─ requirements.txt
├─ templates/
│  ├─ layout.html
│  └─ index.html
├─ static/
│  └─ style.css
└─ storage/
   ├─ pdfs/                  # Your PDFs go here
   └─ index/                 # Whoosh search index (auto-created)
```

---

## 🧹 Maintenance
- Add/remove PDFs → run `python import_pdfs.py --folder storage/pdfs` to refresh the index.
- Index is safe to delete anytime (folder `storage/index`) — it will rebuild on next import.
- Back up your `storage/pdfs` folder regularly.

## ❓Troubleshooting
- **No results?** Make sure you ran the bulk indexer after adding PDFs.
- **Upload errors?** Very large files can take time to extract. Let it finish.
- **Can't access from another PC?** Use `--host=0.0.0.0` and allow port 8000 through Windows Firewall.
- **Basic Auth keeps popping up?** Ensure both `$env:BASIC_AUTH_USER` and `$env:BASIC_AUTH_PASS` are set in the same PowerShell window you run `flask`.

Enjoy!
