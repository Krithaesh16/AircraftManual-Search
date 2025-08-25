import os
from flask import Flask, request, render_template_string, send_from_directory
from whoosh.fields import Schema, TEXT, ID, NUMERIC, STORED
from whoosh import index as whoosh_index
from whoosh.qparser import QueryParser

app = Flask(__name__)

INDEX_DIR = "storage/index"
PDF_DIR = "storage/pdfs"   # where your PDFs are stored

# -------------------------------
# Define / Get Index
# -------------------------------
def get_index(create=True):
    schema = Schema(
        doc_id=ID(stored=True, unique=True),
        filename=STORED,
        title=TEXT(stored=True),
        page=NUMERIC(stored=True),
        content=TEXT
    )
    if not os.path.exists(INDEX_DIR):
        os.makedirs(INDEX_DIR, exist_ok=True)
    if create and not whoosh_index.exists_in(INDEX_DIR):
        return whoosh_index.create_in(INDEX_DIR, schema)
    return whoosh_index.open_dir(INDEX_DIR)

# -------------------------------
# HTML Template
# -------------------------------
TEMPLATE = """
<!doctype html>
<html>
<head>
    <title>PDF Search</title>
</head>
<body>
    <h1>Search PDFs</h1>
    <form method="GET">
        <input type="text" name="q" placeholder="Enter keyword" value="{{ query }}">
        <button type="submit">Search</button>
    </form>
    {% if results %}
        <h2>Results</h2>
        <ul>
        {% for r in results %}
            <li>
                <b>{{ r['title'] }}</b> ({{ r['filename'] }}, page {{ r['page'] }})
                <a href="/pdfs/{{ r['filename'] }}" target="_blank">📂 Open PDF</a>
            </li>
        {% endfor %}
        </ul>
    {% endif %}
</body>
</html>
"""

# -------------------------------
# Routes
# -------------------------------
@app.route("/", methods=["GET"])
def search_page():
    query = request.args.get("q", "")
    results = []

    if query:
        ix = get_index(create=False)
        with ix.searcher() as searcher:
            parser = QueryParser("content", schema=ix.schema)
            q = parser.parse(query)
            res = searcher.search(q, limit=20)
            for hit in res:
                results.append({
                    "title": hit["title"],
                    "filename": hit["filename"],
                    "page": hit["page"]
                })

    return render_template_string(TEMPLATE, query=query, results=results)

# Serve PDFs from storage/pdfs
@app.route("/pdfs/<path:filename>")
def serve_pdf(filename):
    return send_from_directory(PDF_DIR, filename)

# -------------------------------
# Main
# -------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)

