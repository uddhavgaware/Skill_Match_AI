import os
import re

def main():
    backend_url = os.environ.get("BACKEND_URL", "").strip().rstrip("/")
    index_path = os.path.join("frontend", "index.html")
    
    if not os.path.exists(index_path):
        print(f"File not found: {index_path}")
        return

    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()

    if backend_url:
        print(f"==> Injecting BACKEND_URL: {backend_url}")
        content = re.sub(
            r'window\.BACKEND_API_URL\s*=\s*["\'].*?["\'];',
            f'window.BACKEND_API_URL = "{backend_url}";',
            content
        )
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("==> Backend URL successfully linked to frontend!")
    else:
        print("==> No BACKEND_URL environment variable found. Using same-origin fallback.")

if __name__ == "__main__":
    main()
