from flask import Flask, render_template, request, redirect, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "your_secret_key"

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/pharmacyf")
db = client["product_db"]
users_collection = db["users"]
products_collection = db["products"]
orders_collection = db["orders"]

def notify_admin(order_id):
    # Implement admin notification logic here
    pass

def send_order_confirmation_email(user_email, total_price, ordered_products):
    # Prepare email data
    email_data = {
        'user_email': user_email,
        'total_price': total_price,
        'ordered_products': ordered_products
    }

    # You'll need to implement the JavaScript code to send the email using EmailJS in your client-side code
    # For demonstration purposes, we'll print the email data here
    print("Sending order confirmation email:")
    print(email_data)

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = users_collection.find_one({"username": username})
        if user and check_password_hash(user["password"], password):
            session["username"] = username
            if username == "admin":
                return redirect("/admin")
            else:
                return redirect("/client")
        else:
            flash("Invalid username or password. Please try again.", "error")
            return redirect("/")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password)
        if users_collection.find_one({"username": username}):
            flash("Username already exists. Please choose another username.", "error")
            return redirect("/register")
        else:
            users_collection.insert_one({"username": username, "password": hashed_password})
            flash("Registration successful. You can now log in.", "success")
            return redirect("/")
    return render_template("register.html")

@app.route("/client")
def client_dashboard():
    products = products_collection.find()
    orders = orders_collection.find({"username": session.get("username")})
    
    # Retrieve cart products based on session
    cart_products = []
    if "cart" in session:
        cart_product_ids = session["cart"]
        cart_products = [products_collection.find_one({"_id": ObjectId(product_id)}) for product_id in cart_product_ids]
    
    return render_template("client_dashboard.html", username=session.get("username"), products=products, orders=orders, cart_products=cart_products)

@app.route("/add_to_cart/<product_id>")
def add_to_cart(product_id):
    if "cart" not in session:
        session["cart"] = []
    session["cart"].append(product_id)
    flash("Product added to cart.", "success")
    return redirect("/client")

def get_cart_products_from_database():
    if "cart" in session and session["cart"]:
        cart_product_ids = session["cart"]
        cart_products = [products_collection.find_one({"_id": ObjectId(product_id)}) for product_id in cart_product_ids]
        return cart_products
    else:
        return []

def calculate_total_price(cart_products):
    total_price = 0
    for product in cart_products:
        total_price += product["price"]
    return total_price

@app.route('/checkout')
def checkout():
    cart_products = get_cart_products_from_database()
    total_price = calculate_total_price(cart_products)
    for product in cart_products:
        product['_id'] = str(product['_id'])
    return render_template('checkout.html', cart_products=cart_products, total_price=total_price)

@app.route("/place_order", methods=["POST"])
def place_order():
    if "cart" not in session or not session["cart"]:
        flash("Your cart is empty.", "error")
        return redirect("/client")
    
    cart_products = [products_collection.find_one({"_id": ObjectId(product_id)}) for product_id in session["cart"]]
    
    order = {
        "username": session["username"],
        "products": cart_products,
        "status": "pending"
    }
    order_id = orders_collection.insert_one(order).inserted_id
    session.pop("cart")
    flash("Order placed successfully. Thank you for your purchase!", "success")
    notify_admin(order_id)
    
    # After successfully placing the order, call the function to send the order confirmation email
    send_order_confirmation_email('shriram73yt@gmail.com', 15813, 'products')
    
    return redirect("/client")

@app.route("/admin")
def admin_dashboard():
    if "username" not in session:
        return redirect("/")
    orders = orders_collection.find()
    products = products_collection.find()
    return render_template("admin_dashboard.html", orders=orders, products=products)

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect("/")

@app.route("/add_product", methods=["POST"])
def add_product():
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        price = float(request.form["price"])
        image = request.form["image"]
        product = {
            "name": name,
            "description": description,
            "price": price,
            "image": image
        }
        products_collection.insert_one(product)
        flash("Product added successfully.", "success")
    return redirect("/admin")

@app.route("/remove_product/<product_id>")
def remove_product(product_id):
    products_collection.delete_one({"_id": ObjectId(product_id)})
    flash("Product removed successfully.", "success")
    return redirect("/admin")

@app.route("/remove_product", methods=["POST"])
def remove_product_post():
    product_id = request.form.get("product_id")
    if product_id:
        products_collection.delete_one({"_id": ObjectId(product_id)})
        flash("Product removed successfully.", "success")
    else:
        flash("Product ID is required.", "error")
    return redirect("/admin")

if __name__ == "__main__":
    app.run(debug=True)
