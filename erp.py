import os
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. Ambil URL Database dari Heroku secara otomatis
DATABASE_URL = os.getenv("DATABASE_URL")

# Trik khusus Heroku: SQLAlchemy versi terbaru membutuhkan awalan 'postgresql://' bukan 'postgres://'
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Jika dijalankan lokal dan tidak ada DATABASE_URL, pakai SQLite cadangan saja
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./test.db"

# 2. Setup Koneksi Database
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 3. Definisi Tabel di Database
class ProductStock(Base):
    __tablename__ = "product_stocks"
    product = Column(String, primary_key=True, index=True)
    stock = Column(Integer, default=0)

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product = Column(String)
    qty = Column(Integer)

# Perintah untuk membuat tabel otomatis di Heroku Postgres jika belum ada
Base.metadata.create_all(bind=engine)


# 4. Fungsi Utama yang dipanggil oleh main.py (Dihubungkan ke DB)
def get_stock(data: dict):
    product_name = data.get("product")
    db = SessionLocal()
    try:
        item = db.query(ProductStock).filter(ProductStock.product == product_name).first()
        # Jika produk baru pertama kali dicek dan belum ada di DB, buatkan bawaannya (default)
        if not item:
            # Beri stok awal default jika database-nya masih kosong melompong
            default_stocks = {"laptop": 10, "mouse": 25, "keyboard": 15}
            initial_stock = default_stocks.get(product_name, 0)
            
            item = ProductStock(product=product_name, stock=initial_stock)
            db.add(item)
            db.commit()
            db.refresh(item)
            
        return {"product": product_name, "stock": item.stock}
    finally:
        db.close()

def create_order(data: dict):
    product_name = data.get("product")
    quantity = data.get("qty", 0)
    
    db = SessionLocal()
    try:
        # A. Ambil data produk dan KURANGI STOKNYA di database asli!
        item = db.query(ProductStock).filter(ProductStock.product == product_name).first()
        if item:
            if item.stock >= quantity:
                item.stock -= quantity  # Stok berkurang di DB!
            else:
                return {"status": "error", "message": f"Stok tidak cukup. Sisa stok: {item.stock}"}
        
        # B. Masukkan data pesanan baru ke tabel orders
        new_order = Order(product=product_name, qty=quantity)
        db.add(new_order)
        db.commit()  # Simpan permanen ke Heroku Postgres
        db.refresh(new_order)
        
        return {
            "status": "created",
            "order": {"product": new_order.product, "qty": new_order.qty}
        }
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

def list_orders():
    db = SessionLocal()
    try:
        all_orders = db.query(Order).all()
        orders_list = [{"product": o.product, "qty": o.qty} for o in all_orders]
        return {"orders": orders_list}
    finally:
        db.close()

def tambah_stok(product: str, qty: int) -> str:
    """Menambahkan atau mengisi ulang stok produk di gudang ERP."""
    payload = {"tool": "tambah_stok", "input": {"product": product, "qty": qty}}
    return call_mcp(payload)