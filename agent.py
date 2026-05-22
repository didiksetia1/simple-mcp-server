"""
agent_gemini.py — AI Agent yang connect ke MCP server (main.py) dengan auto tool calling menggunakan Gemini.

Cara pakai:
    pip install google-genai requests
    python agent_gemini.py

Pastikan MCP server sudah jalan:
    uvicorn main:app --reload --port 8000
"""

import json
import requests
from google import genai
from google.genai import types

# ── Config ────────────────────────────────────────────────────────────────────
MCP_URL = "http://localhost:8000/mcp"
# Menggunakan model flagship terbaru Gemini 2.5 Flash / Pro
MODEL   = "gemini-2.5-flash" 

# Inisialisasi client (pastikan sudah export GEMINI_API_KEY="api-kamu" di terminal)
client = genai.Client()

# ── Python Functions sebagai Tools ───────────────────────────────────────────
# Berbeda dengan Anthropic yang pakai skema JSON rumit, Gemini bisa langsung 
# membaca fungsi Python biasa (berkat bantuan Type Hints dan Docstring).

def get_stock(product: str) -> str:
    """Cek stok produk di gudang ERP.
    
    Args:
        product: Nama produk, misal: laptop, mouse, keyboard
    """
    payload = {"tool": "get_stock", "input": {"product": product}}
    return call_mcp(payload)

def create_order(product: str, qty: int) -> str:
    """Buat pesanan / order baru untuk suatu produk.
    
    Args:
        product: Nama produk yang dipesan
        qty: Jumlah unit yang dipesan
    """
    payload = {"tool": "create_order", "input": {"product": product, "qty": qty}}
    return call_mcp(payload)

def list_orders() -> str:
    """Tampilkan semua order yang sudah dibuat."""
    payload = {"tool": "list_orders", "input": {}}
    return call_mcp(payload)


# ── Panggil MCP server ────────────────────────────────────────────────────────
def call_mcp(payload: dict) -> str:
    """Kirim tool call ke MCP server, return hasil sebagai string JSON."""
    print(f"  [tool] {payload['tool']}({json.dumps(payload['input'], ensure_ascii=False)})")
    try:
        resp = requests.post(MCP_URL, json=payload, timeout=10)
        resp.raise_for_status()
        result_str = json.dumps(resp.json(), ensure_ascii=False)
        print(f"  [result] {result_str}")
        return result_str
    except requests.RequestException as e:
        error_str = json.dumps({"error": str(e)})
        print(f"  [result] {error_str}")
        return error_str

# ── Agentic loop ──────────────────────────────────────────────────────────────
def run_agent(user_message: str) -> str:
    """Jalankan agent menggunakan fitur Auto Function Calling milik Gemini."""
    
    # Daftarkan fungsi Python di atas sebagai tools
    my_tools = [get_stock, create_order, list_orders]
    
    # Konfigurasi agar Gemini otomatis mengeksekusi fungsi lokal jika dibutuhkan
    config = types.GenerateContentConfig(
        tools=my_tools,
        temperature=0.0, # Rendah agar agent lebih presisi memilih tool
    )
    
    # Panggil Gemini. Loop chat, eksekusi tool, dan pengiriman balik hasil 
    # dihandle otomatis di balik layar oleh SDK google-genai.
    response = client.models.generate_content(
        model=MODEL,
        contents=user_message,
        config=config
    )
    
    return response.text

# ── CLI interaktif ────────────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  ERP AI Agent (Gemini)  |  ketik 'exit' untuk keluar")
    print("=" * 55)
    print("Contoh perintah:")
    print("  • Berapa stok laptop?")
    print("  • Pesan 3 unit mouse")
    print("  • Tampilkan semua order")
    print("-" * 55)

    while True:
        try:
            user_input = input("\nAnda: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit", "keluar"}:
            print("Bye!")
            break

        print("Agent: ", end="", flush=True)
        answer = run_agent(user_input)
        print(answer)

if __name__ == "__main__":
    main()