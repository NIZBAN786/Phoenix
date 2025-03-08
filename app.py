import uuid
from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
from flask_bcrypt import Bcrypt
from flask_session import Session
from pymongo import MongoClient
from fpdf import FPDF
import os
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
app.secret_key = 'f9e2c3a64b27d4e6a1d8f2e5b8c3d9e0e4a7b6c9d1a2f5b3c6e8d9a2f4b7c1d2'
bcrypt = Bcrypt(app)
client = MongoClient('mongodb://localhost:27017/')
db = client['phoenix']
users_collection = db['users']
orders_collection = db['orders']

app.config["SESSION_TYPE"] = "mongodb"
app.config["SESSION_MONGODB"] = client
app.config["SESSION_MONGODB_DB"] = "phoenix"
app.config["SESSION_MONGODB_COLLECT"] = "sessions"

Session(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/accept_order/<order_id>', methods=["POST"])
def accept_order(order_id):
    order = orders_collection.find_one({"order_id": order_id})
    if order and order["status"] == "Processing":
        orders_collection.update_one(
            {"order_id": order_id},
            {"$set": {"status": "Confirmed"}}
        )
        flash("Order confirmed successfully.")
    else:
        flash("Order not found or already confirmed.")
    return redirect(url_for('admin'))

@app.route('/cancel_order/<order_id>', methods=["POST"])
def cancel_order(order_id):
    order = orders_collection.find_one({"order_id": order_id})
    if order and order["status"] in ["Processing", "Confirmed"]:
        orders_collection.update_one(
            {"order_id": order_id},
            {"$set": {"status": "Cancelled"}}
        )
        flash("Order cancelled successfully.")
    else:
        flash("Order not found or cannot be cancelled.")
    return redirect(url_for('admin'))

@app.route('/user_cancel_order/<order_id>', methods=["POST"])
def user_cancel_order(order_id):
    if "username" not in session:
        return redirect(url_for('login'))
    
    order = orders_collection.find_one({"order_id": order_id, "username": session["username"]})
    if order and order["status"] in ["Processing", "Confirmed"]:
        orders_collection.update_one(
            {"order_id": order_id},
            {"$set": {"status": "Cancelled"}}
        )
        flash("Order cancelled successfully.")
    else:
        flash("Order not found or cannot be cancelled.")
    return redirect(url_for('profile'))

@app.route('/about')
def about():
    return render_template('aboutus.html')

@app.route('/support')
def support():
    return render_template('support.html')

@app.route('/wirelessearbuds')
def wirelessearbuds():
    return render_template('wirelessearbuds.html')

@app.route('/headphones')
def headphones():
    return render_template('headphones.html')

@app.route('/speakers')
def speakers():
    return render_template('speakers.html')

@app.route('/keyboards')
def keyboards():
    return render_template('keyboards.html')

@app.route('/flobuds100')
def flobuds100():
    return render_template('flobuds100.html')

@app.route('/flobuds200')
def flobuds200():
    return render_template('flobuds200.html')

@app.route('/phantom340')
def phantom340():
    return render_template('phantom340.html')

@app.route('/centerstage120')
def centerstage120():
    return render_template('centerstage120.html')

@app.route('/script')
def script():
    return render_template('app.js')

@app.route('/centerstage400')
def centerstage400():
    return render_template('centerstage400.html')

@app.route('/grind100')
def grind100():
    return render_template('grind100.html')

@app.route('/grind105')
def grind105():
    return render_template('grind105.html')

@app.route('/order', methods=["GET", "POST"])
def order():
    if "username" not in session:
        return redirect(url_for('login'))

    if request.method == "POST":
        username = session["username"]
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        address = request.form["address"]
        state = request.form["state"]
        pincode = request.form["pincode"]
        phone_number = request.form["phone_number"]
        payment_method = request.form["payment_method"]

        product_name = request.form.get("product_name", "Unknown Product")
        product_price = request.form.get("product_price", "0")

        order_id = str(uuid.uuid4())  # Generate a unique order ID

        order_data = {
            "order_id": order_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "address": address,
            "state": state,
            "pincode": pincode,
            "phone_number": phone_number,
            "payment_method": payment_method,
            "product_name": product_name,
            "product_price": product_price,
            "status": "Processing"
        }

        orders_collection.insert_one(order_data)

        receipt_path = generate_receipt(order_data)
        return send_file(receipt_path, as_attachment=True)

    return render_template('order.html')

def generate_receipt(order):
    receipt_path = f"receipts/{order['order_id']}.pdf"
    os.makedirs("receipts", exist_ok=True)

    product_name = order['product_name'].lower().replace(' ', '')
    product_url = f'http://127.0.0.1:5000/{product_name}'
    response = requests.get(product_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    img_tag = soup.find('img', id='bigimg')
    img_url = img_tag['src'] if img_tag else None

    if img_url and not img_url.startswith(('http://', 'https://')):
        img_url = f'http://127.0.0.1:5000{img_url}'

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=16)
    pdf.set_draw_color(0, 0, 0)
    pdf.rect(5, 5, 200, 287)

    pdf.cell(200, 10, txt="Phoenix", ln=True, align='C')
    pdf.line(10, 20, 200, 20) 
    pdf.cell(200, 10, txt="Order Receipt", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Order ID: {order['order_id']}", ln=True)
    pdf.cell(200, 10, txt=f"Customer Name: {order['first_name']} {order['last_name']}", ln=True)
    pdf.cell(200, 10, txt=f"Address: {order['address']}, {order['state']}, {order['pincode']}", ln=True)
    pdf.cell(200, 10, txt=f"Phone Number: {order['phone_number']}", ln=True)
    pdf.cell(200, 10, txt=f"Payment Method: {order['payment_method']}", ln=True)
    pdf.cell(200, 10, txt=f"Product: {order['product_name']}", ln=True)
    pdf.cell(200, 10, txt=f"Price: {order['product_price']}", ln=True)
    pdf.cell(200, 10, txt="Thank you for your order!", ln=True)

    if img_url:
        image_response = requests.get(img_url)
        with open("temp_image.jpg", "wb") as img_file:
            img_file.write(image_response.content)
        pdf.ln(10)
        pdf.image("temp_image.jpg", x=10, y=pdf.get_y(), w=100)
        os.remove("temp_image.jpg")

    pdf.output(receipt_path)

    return receipt_path

@app.route('/phantom850')
def phantom850():
    return render_template('phantom850.html')

@app.route('/productdetail')
def productdetail():
    return render_template('productdetail.html')

@app.route('/thunder')
def thunder():
    return render_template('thunder.html')

@app.route('/vader100')
def vader100():
    return render_template('vader100.html')

@app.route('/upbeat101')
def upbeat101():
    return render_template('upbeat101.html')

@app.route('/vader200')
def vader200():
    return render_template('vader200.html')

@app.route('/vader350')
def vader350():
    return render_template('vader350.html')

@app.route('/vader300')
def vader300():
    return render_template('vader300.html')

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = users_collection.find_one({"username": username})
        if user and bcrypt.check_password_hash(user["password"], password):
            session["username"] = username
            session_id = str(uuid.uuid4())  # Generate a unique session ID
            session["session_id"] = session_id
            session_collection = db["sessions"]
            session_collection.insert_one(
                {"username": username, "session_id": session_id}
            )
            return redirect(url_for("home"))
        return "Invalid credentials"
    return render_template("login.html")

@app.route('/signup', methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        existing_user = users_collection.find_one({"username": username})
        if existing_user:
            return "Username already exists. Please choose a different username."
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        users_collection.insert_one({"username": username, "password": hashed_password})
        return redirect(url_for("login"))    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

@app.route('/profile')
def profile():
    if "username" in session:
        username = session["username"]
        orders = list(orders_collection.find({"username": username}))
        return render_template('profile.html', orders=orders)
    return redirect(url_for('login'))

@app.route('/add_to_cart/<product_id>', methods=["POST"])
def add_to_cart(product_id):
    if "username" not in session:
        return redirect(url_for('login'))
    
    username = session["username"]
    user_cart = db['carts'].find_one({"username": username})
    
    if not user_cart:
        db['carts'].insert_one({"username": username, "cart": [product_id]})
    else:
        if product_id not in user_cart["cart"]:
            db['carts'].update_one(
                {"username": username},
                {"$push": {"cart": product_id}}
            )
    
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<product_id>', methods=["POST"])
def remove_from_cart(product_id):
    if "username" not in session:
        return redirect(url_for('login'))
    
    username = session["username"]
    db['carts'].update_one(
        {"username": username},
        {"$pull": {"cart": product_id}}
    )
    
    return redirect(url_for('cart'))

@app.route('/cart')
def cart():
    if "username" not in session:
        return redirect(url_for('login'))
    
    username = session["username"]
    user_cart = db['carts'].find_one({"username": username})
    
    if not user_cart:
        cart_items = []
    else:
        cart_items = user_cart["cart"]
    
    cart_images = []
    for item in cart_items:
        url = f'http://127.0.0.1:5000/{item}'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        img_tag = soup.find('img', id='bigimg')
        if img_tag:
            cart_images.append(img_tag['src'])
    
    return render_template('cart.html', cart_items=cart_items, cart_images=cart_images, zip=zip)

@app.route('/admin', methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        if username == "admin" and password == "phoenix":
            users = list(users_collection.find({}, {"_id": 0, "password": 0}))
            orders = list(orders_collection.find({}, {"_id": 0}))
            carts = list(db['carts'].find({}, {"_id": 0}))
            
            return render_template('admin.html', users=users, orders=orders, carts=carts)
        else:
            return "Invalid admin credentials"
    
    return render_template('admin_login.html')

@app.route('/delete_user/<username>', methods=["POST"])
def delete_user(username):
    users_collection.delete_one({"username": username})
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)