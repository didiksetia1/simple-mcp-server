import os
import json
import time
import requests
from google import genai
from google.genai import types
from google.genai.errors import APIError
from dotenv import load_dotenv

# Muat file .env otomatis
load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
MCP_URL = "https://lapor-pak-415ea445196f.herokuapp.com/mcp"
MODEL   = "gemini-2.5-flash" 

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("[Error] API Key tidak ditemukan di file .env!")
    exit(1)

client = genai.Client(api_key=api_key)

# ── Tools Definition ──────────────────────────────────────────────────────────
def get_stock(product: str) -> str:
    """Cek stok produk di gudang ERP."""
    payload = {"tool": "get_stock", "input": {"product": product}}
    return call_mcp(payload)

def create_order(product: str, qty: int) -> str:
    """Buat pesanan / order baru untuk suatu produk."""
    payload = {"tool": "create_order", "input": {"product": product, "qty": qty}}
    return call_mcp(payload)

def list_orders() -> str:
    """Tampilkan semua order yang sudah dibuat."""
    payload = {"tool": "list_orders", "input": {}}
    return call_mcp(payload)

def call_mcp(payload: dict) -> str:
    print(f"  [tool] {payload['tool']}({json.dumps(payload['input'])})")
    try:
        resp = requests.post(MCP_URL, json=payload, timeout=10)
        resp.raise_for_status()
        result_str = json.dumps(resp.json())
        print(f"  [result] {result_str}")
        return result_str
    except requests.RequestException as e:
        error_str = json.dumps({"error": str(e)})
        print(f"  [result] {error_str}")
        return error_str

# ── Inisialisasi Chat Session dengan Tools ────────────────────────────────────
my_tools = [get_stock, create_order, list_orders]
config = types.GenerateContentConfig(tools=my_tools, temperature=0.0)
chat_session = client.chats.create(model=MODEL, config=config)

# ── Fungsi Pengaman Anti-Crash (Safe Request) ─────────────────────────────────
def send_message_with_retry(message: str, max_retries=3, delay=4):
    """Mengirim pesan ke Gemini dengan fitur auto-retry jika terkena limit/beban padat."""
    for attempt in range(max_retries):
        try:
            response = chat_session.send_message(message)
            return response.text
        except APIError as e:
            # Jika error 429 (Quota) atau 503 (Server Overload)
            if e.code in [429, 503]:
                if attempt < max_retries - 1:
                    print(f"\n  [Server Sibuk/Quota Limit] Mencoba kembali dalam {delay} detik... (Percobaan {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    continue
            return f"\n[Gagal] Google Server sedang sangat sibuk (Error {e.code}). Silakan coba lagi beberapa saat lagi."
        except Exception as e:
            return f"\n[Error Tidak Diketahui]: {str(e)}"

# ── Main Loop ─────────────────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  ERP AI Agent (Gemini Anti-Crash) | ketik 'exit' untuk keluar")
    print("=" * 55)

    while True:
        try:
            user_input = input("\nAnda: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input: continue
        if user_input.lower() in {"exit", "quit", "keluar"}: break

        print("Agent: ", end="", flush=True)
        
        # Panggil fungsi pengaman
        reply = send_message_with_retry(user_input)
        print(reply)

if __name__ == "__main__":
    main()