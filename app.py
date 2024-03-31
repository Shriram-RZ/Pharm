from flask import Flask, render_template, request, redirect, session, flash, render_template_string
from flask_mail import Mail, Message
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Flask-Mail configuration for Gmail SMTP
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'shriram73yt@gmail.com'  # Replace with your Gmail address
app.config['MAIL_PASSWORD'] = 'wchu poqa aift dxfo'  # Replace with your Gmail password
app.config['MAIL_DEFAULT_SENDER'] = 'shriram73yt@gmail.com'  # Replace with your Gmail address

mail = Mail(app)

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/pharmacyf")
db = client["product_db"]
users_collection = db["users"]
products_collection = db["products"]
orders_collection = db["orders"]
prescriptions_collection = db["prescriptions"]

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
    if "username" not in session:
        return redirect("/")
    products = products_collection.find()
    orders = orders_collection.find({"username": session.get("username")})
    cart_products = []
    if "cart" in session:
        cart_product_ids = session["cart"]
        cart_products = [products_collection.find_one({"_id": ObjectId(product_id)}) for product_id in cart_product_ids]
    prescriptions = prescriptions_collection.find()  # Retrieve prescriptions from the database
    return render_template("client_dashboard.html", username=session.get("username"), products=products, orders=orders, cart_products=cart_products, prescriptions=prescriptions)

@app.route("/search")
def search():
    query = request.args.get("query")
    if query:
        # Perform a case-insensitive search for products matching the query
        matched_products = products_collection.find({"$or": [{"name": {"$regex": query, "$options": "i"}},
                                                             {"description": {"$regex": query, "$options": "i"}}]})
        return render_template("search_results.html", query=query, products=matched_products)
    else:
        flash("Please enter a search query.", "error")
        return redirect("/client")
    search_results = products_collection.find({"$text": {"$search": query}})
    return render_template("search_results.html", query=query, products=search_results)


@app.route("/upload_prescription", methods=["POST"])
def upload_prescription():
    fullname = request.form["fullname"]
    email = request.form["email"]
    phone = request.form["phone"]
    prescription_file = request.files["prescription"]
    
    # Create the 'prescriptions' directory if it doesn't exist
    if not os.path.exists("prescriptions"):
        os.makedirs("prescriptions")

    # Save the prescription image to the 'prescriptions' directory
    prescription_filename = os.path.join("prescriptions", prescription_file.filename)
    prescription_file.save(prescription_filename)

    # Save prescription details to the database
    prescription_data = {
        "fullname": fullname,
        "email": email,
        "phone": phone,
        "prescription_file": prescription_filename  # Save the file path
    }
    prescriptions_collection.insert_one(prescription_data)

    # Redirect the user to the client dashboard or any other page
    flash("Prescription uploaded successfully.", "success")
    return redirect("/client")

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
        if product is not None:
            total_price += product.get("price", 0)
    return total_price

@app.route('/checkout')
def checkout():
    cart_products = get_cart_products_from_database()
    if cart_products:
        total_price = calculate_total_price(cart_products)
        for product in cart_products:
            if product:
                product['_id'] = str(product['_id'])
        return render_template('checkout.html', cart_products=cart_products, total_price=total_price)
    else:
        flash("Your cart is empty.", "error")
        return redirect("/client")

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
    send_order_confirmation_email(session["username"], calculate_total_price(cart_products), cart_products)
    return redirect("/client")

@app.route("/admin")
def admin_dashboard():
    if "username" not in session:
        return redirect("/")
    orders = list(orders_collection.find())
    products = list(products_collection.find())
    prescriptions = list(prescriptions_collection.find())  # Retrieve prescriptions from the database
    return render_template("admin_dashboard.html", orders=orders, products=products, prescriptions=prescriptions)

@app.route("/send_prescription_email/<prescription_id>")
def send_prescription_email(prescription_id):
    prescription = prescriptions_collection.find_one({"_id": ObjectId(prescription_id)})
    if prescription:
        # Email prescription details
        send_prescription_email_to_admin(prescription)
        flash("Prescription details sent to admin.", "success")
    else:
        flash("Prescription not found.", "error")
    return redirect("/admin")

def send_prescription_email_to_admin(prescription):
    recipient_email = 'shriram73yt@gmail.com'  # Replace with admin's email address
    msg = Message('New Prescription Uploaded', recipients=[recipient_email])

    # Render the email body using a template string
    email_body = render_template_string("""
    <html>
    <head></head>
    <body>
        <h2>New Prescription Uploaded</h2>
        <p><strong>Full Name:</strong> {{ prescription.fullname }}</p>
        <p><strong>Email:</strong> {{ prescription.email }}</p>
        <p><strong>Phone:</strong> {{ prescription.phone }}</p>
        <p><strong>Prescription Image:</strong></p>
        <img src="cid:prescription_image" alt="Prescription Image" style="max-width: 100%;">
    </body>
    </html>
    """, prescription=prescription)

    # Attach the prescription image
    with app.open_resource(prescription['prescription_file']) as fp:
        msg.attach('prescription.png', 'image/png', fp.read(), 'inline', headers=[('Content-ID', '<prescription_image>')])

    msg.html = email_body

    mail.send(msg)




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

def send_order_confirmation_email(user_email, total_price, ordered_products):
    recipient_email = 'shriram73yt@gmail.com'  # Change this to the correct recipient email address
    msg = Message('Order Confirmation', recipients=[recipient_email])

    # HTML content for the email body
    html_content = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
            }}
            .order-details {{
                border-collapse: collapse;
                width: 100%;
            }}
            .order-details th, .order-details td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            .order-details th {{
                background-color: #f2f2f2;
            }}
        </style>
    </head>
    <body>
        <h2>Order Confirmation</h2>
        <p>Thank you for your order!</p>
        <p><strong>Total Price:</strong> ${total_price}</p>
        <h3>Ordered Products:</h3>
        <table class="order-details">
            <tr>
                <th>Product</th>
                <th>Price</th>
            </tr>
    """

    # Adding ordered products to the email content
    for product in ordered_products:
        html_content += f"""
            <tr>
                <td>{product['name']}</td>
                <td>${product['price']}</td>
            </tr>
        """

    # Closing HTML tags
    html_content += """
        </table>
    </body>
    </html>
    """

    # Set the HTML content of the email
    msg.html = html_content

    # Send the email
    mail.send(msg)

if __name__ == "__main__":
    app.run(debug=True)
