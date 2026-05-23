import os
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. Ambil URL Database dari Heroku secara otomatis (Config Vars)
# Jika dijalankan lokal/tidak diisi di Heroku, otomatis pakai cadangan MySQL Docker Codespaces
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "mysql+pymysql://app_user:password123@localhost:3306/app_db"
)

# Trik khusus Heroku: Jika sewaktu-waktu beralih ke Heroku Postgres kembali
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 2. Setup Koneksi Database (Hanya dibuat 1 kali setelah string beres)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# 3. Definisi Tabel di Database
class ProductStock(Base):
    __tablename__ = "product_stocks"
    product = Column(String(50), primary_key=True, index=True) # Tambah limit panjang string untuk MySQL
    stock = Column(Integer, default=0)

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product = Column(String(50)) # Tambah limit panjang string untuk MySQL
    qty = Column(Integer)


# Perintah untuk membuat tabel otomatis di MySQL Docker jika belum ada
Base.metadata.create_all(bind=engine)


# 4. Fungsi Utama yang dipanggil oleh main.py (Dihubungkan ke DB)
def get_stock(data: dict):
    product_name = data.get("product")
    db = SessionLocal()
    try:
        item = db.query(ProductStock).filter(ProductStock.product == product_name).first()
        # Jika produk baru pertama kali dicek dan belum ada di DB, buatkan bawaannya (default)
        if not item:
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
        db.commit()  # Simpan permanen ke MySQL Docker Codespaces lewat internet
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

# Fungsi Backend Asli untuk Menambah Stok (Perbaikan dari fungsi nyasar tadi)
def update_stock_backend(data: dict):
    product_name = data.get("product")
    quantity = data.get("qty", 0)
    
    db = SessionLocal()
    try:
        item = db.query(ProductStock).filter(ProductStock.product == product_name).first()
        if item:
            item.stock += quantity
        else:
            item = ProductStock(product=product_name, stock=quantity)
            db.add(item)
            
        db.commit()
        db.refresh(item)
        return {"status": "success", "message": f"Stok {product_name} berhasil ditambah. Stok sekarang: {item.stock}"}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
