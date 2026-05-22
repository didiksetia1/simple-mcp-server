stock_db = {
    "laptop": 10,
    "mouse": 25,
    "keyboard": 15
}

orders_db = []

def get_stock(data):
    product = data.get("product")

    return {
        "product": product,
        "stock": stock_db.get(product, 0)
    }


def create_order(data):
    order = {
        "product": data.get("product"),
        "qty": data.get("qty")
    }

    orders_db.append(order)

    return {
        "status": "created",
        "order": order
    }


def list_orders():
    return {
        "orders": orders_db
    }