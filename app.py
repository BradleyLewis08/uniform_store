# All imports from the Flask library
from flask import Flask, render_template, request, redirect, session
# Imports all database functions from my other python file, "db.py"
from db import *
 
# Initiates the flask App
app = Flask(__name__)
app.secret_key = "\xef\xfe\x0f\x85v\xbfe\xa9\xe3v\x1c\x87\x01\xf7\x81\x8f\x08\xeaN\x00\x19\x86\x18."
# Defines a function that is called when the user first goes to the website URL
@app.route('/')
def index():
    # Redirects the user to the login page as soon as they land on the website
    return redirect("/login")
 
# Defines a function that is called when the user is directed to the "/register" route.
 
 
#There are two request methods that this route can handle - 'POST' allows for data to be passed into the route and handled, while 'GET' is where a resource is retrieved from the server. In each of the routes, I define the methods available for each route.
@app.route("/register", methods=['POST', 'GET'])
def register():
    # If the user is simply being redirected to the register route, a html page is rendered where they are able to enter details to register.
    if request.method == "GET":
        return render_template("register.html")
    # Once the user has entered their details and has pressed the 'register' button, the details are then passed to this python file to be processed and stored.
    elif request.method == 'POST':
        # A means of getting the data from the form via the name of each HTML input field
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        email = request.form["email"]
        password = request.form["password"]
        # Call a function "check_email" which is in the python file "db.py". This is explained in more depth in the comments within that file, but the function returns a list of email addresses that are already registered. If the length of that list is 0, then the email that the user entered has not yet been registered and the user can use this email to create a new account.
        if len(check_email(email)) > 0:
            # If the email is already taken, an error page is displayed. 
            return render_template("fail.html", message="That email has already been registered.", link="/register")
        # Otherwise, a function "store_details" is called.
        else:
            # This function exists in the "db.py" file, and is explained in more depth there. It acts as a way of storing the user's account details in the database once they have registered.
            store_details(first_name, last_name, email, password)
            # Once the user has created their account, they are redirected to the login page.
            return redirect("/login")
 
 
@app.route("/login", methods=['POST', 'GET'])
def login():
    # If the user has been redirected to the login route, the login page is rendered.
    if request.method == "GET":
        return render_template("login.html")
    # Once the user presses login, their credentials are processed here.
    elif request.method=="POST":
        # A means of getting the user's credentials from the HTML form.
        email = request.form["email"]
        password = request.form["password"]
        # Calls the function "check_details" in "db.py" and passes in the credentials entered in the form as parameters. The function returns a list of all the registered accounts that match the credentials passed in. If the length of this list is 0, the user has entered invalid credentials and is shown an error message.
        if len(check_details(email, password)) == 0:
            # An error message is displayed and a link is available for the user to go back to the login page.
            return render_template("fail.html", message="Incorrect email and password combination!", link="/login")
        else:
            # If the user successfully logs in, their details are retrieved using the "get_user_details" function in "db.py". The function returns a dictionary with all the user's details as key:value pairs.
            # Here, I am making use of Flask's Session capability. This is a way of storing variables across multiple routes. 'Session' acts as a dictionary, and to add a new variable I define a new key and set it equal to a value. Here, the variable is "user_info" and I am storing the dictionary with all the user's info in this variable.
            session["user_info"] = get_user_details(email)
            # If the user enters an admin's credentials, they are redirected to the admin route.
            if session["user_info"]["role"] == "admin":
                return redirect("/admin")
            # If the user is not an admin, they are redirected to the "/display" route.
            else:
                return redirect("/display")
 
@app.route("/display", methods=['GET'])
def home():
    # Calls the function "get_product_names" in "db.py", which returns a list of all the names of the products available for purchase.
    uniform_items = get_product_names()
    # Renders a HTML page where all the items are displayed.
    return render_template("home.html", items=uniform_items)
 
# This route makes use of a variable within the route name called 'item'. Each item has its own unique route, and when the route is navigated to, the variable 'item' can be accessed by passing it into the function "display_item" that is called when this route is navigated to.
@app.route("/display/<item>", methods=['GET'])
def display_item(item):
    # This makes use of Flask's sessions once again. Here, it calls the function "get_item_info", which takes the item's unique ID as a parameter. The function then returns a dictionary with relevant data and stores it in the session variable "current_item_info".
    session['current_item_info'] = get_item_info(item)
    # The page for this specific item is then displayed with all the relevant data on display.
    return render_template("displayitem.html", item=item, sizes=session['current_item_info']["available_sizes"], price=session['current_item_info']["price"])
 
# This route is reached whenever the user makes an order.
@app.route("/order", methods=['GET', 'POST'])
def confirm_order():
    if request.method == 'POST':
        size = request.form["size"]
        quantity = request.form["quantity"]
        # The item_id that needs to be stored includes the size of the item that was ordered by the customer, so string concatenation is used here to form the complete id.
        item_id = session['current_item_info']["id"] + "-" + size
        # This calls the function "check_quantity", which returns True if the quantity ordered by the customer does not exceed current available stock levels, and returns False otherwise.
        if check_quantity(item_id, int(quantity)):
            # Here, the information about the item being ordered is stored in a session variable to be processed later.
            session["current_item_info"]["id"] = item_id
            # Calls the function "calclate_price", which returns the final price of the order given the item_id and the quantity being ordered.
            final_price = calclate_price(session["current_item_info"]["id"], quantity)
            session['current_item_info']['quantity'] = quantity
            session['current_item_info']['price'] = final_price
            # Calls the function "add_order", which stores the order in the database given the order information and the user information.
            add_order(session["current_item_info"], session["user_info"]["user_id"])
            # Calls the function "update_stock", which updates stock levels to reflect new stock levels after the order has been placed.
            update_stock(-int(quantity), item_id)
            return redirect("/orders")
        # If the desired quantity exceeds available stock levels, an error message is displayed.
        else:
            return render_template("fail.html", message="Insufficient stock remaining to make this order!", link="/display")
 
# This route simply displays all the orders made by the user who is logged in.
@app.route("/orders", methods=['GET'])
def display_orders():
    # Calls the function "get_user_orders", which returns a list of all the orders that correspond with the user that is logged in.
    all_orders = get_user_orders(session["user_info"]["user_id"])
    # Navigates the user to a page which displays all their orders in a table format.
    return render_template("orders.html", orders=all_orders, user_details = session["user_info"], role=session["user_info"]["role"])
 
# A route which allows the user to log out.
@app.route("/logout", methods=['GET'])
def logout():
    # Clears the user details from the session.
    session.pop("user_info")
    # Once the user is logged out, they are redirected to the login page.
    return redirect("/login")
 
# A route which allows the user to search for items in the store.
@app.route("/search", methods=['GET', 'POST'])
def search():
    # Once the user navigates to the route, they are met with a page that has a search bar.
    if request.method == 'GET':
        return render_template("search.html")
    # When the user clicks search, their data is passed here and processed.
    else:
        term = request.form["search"]
        # Calls the function "search_items" which takes a search term as a parameter and returns all the items that match with the search term.
        results = search_items(term)
        # Renders a page which displays all the search results.
        return render_template("search_results.html", results = results)
 
# A route which only the system admin can access. Once an admin user is logged in they are navigated to this page.
@app.route("/admin", methods=['GET', 'POST'])
def admin():
    if request.method == 'GET':
        # Calls the function "check_privileges", which checks the role of the user that is logged in and returns True if the user is an admin and false if they are not an admin.
        if check_privileges(session["user_info"]["role"]):
            # Renders an 'admin dashboard' page which an admin user can use to perform administrative tasks. 
            return render_template("dashboard.html")
        else:
            # If the user does not have admin privileges, an error message is displayed.
            return render_template("fail.html", message="Insufficient admin privileges", link="/display")
 
# A route which admin users can use to view all orders.
@app.route("/admin/orders", methods=['GET', 'POST'])
def admin_orders():
    if request.method == 'GET':
        # Calls the function "get_all_orders" which retrieves all orders from the database and returns a list of these orders.
        orders = get_all_orders()
        # Displays the orders in a table, which is specially formatted if the user is an admin.
        return render_template("orders.html", orders=orders, user_details=session["user_info"], role=session["user_info"]["role"])
 
# A route which allows the admin to manage a specific order
@app.route("/admin/orders/<order>", methods=['GET', 'POST'])
def manage_orders(order):
    if request.method == 'GET':
        # Checks if the user is an admin and denies regular users access.
        if not check_privileges(session["user_info"]["role"]):
            return render_template("fail.html", message="Insufficient admin privileges", link="/display")
        else:
            # Calls the function "get_order", which retrieves the specific order by order_id
            order = get_order(order)
            return render_template("manage.html", orders=order, user_details=session["user_info"], role=session["user_info"]["role"])
 
# This route allows the admin to request the user to acknowledge that the order has been completed and the user has gone to the store and received their items. The admin can click a "Complete Order" button which changes the status of the order from "Incomplete" to "Pending". The user who made the order must then view their orders and click "Complete Order" for the order to then be marked as complete.
@app.route("/complete/<order>", methods=['GET', 'POST'])
def complete_order(order):
    if request.method == 'GET':
        # Checks if the user is an admin or a regular user. If the user is an admin, pressing the "Complete order" button will change the order status from "Incomplete" to "Pending".
        if check_privileges(session["user_info"]["role"]):
            # Calls a function "change_order_status" which changes the status of the order in the database.
            change_order_status(order, "Pending")
            # Once the order is marked as pending, the admin user is redirected to the table of all orders. The change in status should be reflected in this table.
            return redirect("/admin/orders")
        else:
            # If the user is a regular user, the status is changed from "pending" to "complete" once the "complete order" button is pressed. The button is only available to be pressed after the admin has made the order "pending".
            change_order_status(order, "Complete")
            # Once the order is completed, the user is redirected to the table with their orders. The change in status should be reflected in this table.
            return redirect("/orders")
 
# This route allows the admin user to view all the products in the store as well as stock levels.
@app.route("/admin/products", methods=['GET', 'POST'])
def manage_products():
    # Admin user verification
    if check_privileges(session["user_info"]["role"]):
        if request.method=="GET":
            # Calls the function "get_products", which gets information about all the products available from the store and returns this as a list.
            products = get_products()
            # Renders a page with a table of all the products and their details.
            return render_template("products.html", products=products)
    else:
        return render_template("fail.html", message="Insufficient admin privileges", link="/display")
 
# A route that allows the admin user to add new stocks to the database
@app.route("/admin/stocks/<item>", methods=['GET', 'POST'])
def update_stocks(item):
    if request.method == "GET":
        # Gets the item information from the database, including its name, ID and current stock quantity
        item_info = get_product_details(item)
        # Renders a form where the admin user can enter new stocks
        return render_template("stocks.html", item = item_info)
    else:
        quantity_added = request.form["quantity_added"]
        # Once the form is submitted, the new stock is calculated in the function "update_stock" and the new quantity is stored in the database.
        update_stock(quantity_added, item)
        # Redirects the admin back to the products page.
        return redirect("/admin/products")
 
# Takes in the user's role as a parameter and returns True if the user is an admin, or False if the user is a regular user.
def check_privileges(role):
    if role != "admin":
        return False
    else:
        return True
 
# Starts the Flask app when this file is run.
if __name__ == '__main__':
    app.run()
