import sqlite3
import sys
import hashlib
import uuid
from datetime import date
 
# This init function connects the program to the database. The 'conn' object is a means of writing and saving changes to the database, while the 'c' object is a cursor object that allows for navigation and retrieval of data from the database.
def init():
    conn = sqlite3.connect("uniform.db")
    c = conn.cursor()
    # Returns both the 'c' and 'conn' objects
    return conn, c
 
# This function is called when the user registers a new email. It checks if the email that the user registered is already in the database and returns a list of 
def check_email(email):
    conn, c = init()
    # Executes a SELECT SQL statement that returns a list of all the emails in the database that match the email address entered by the user.
    # It is insecure to construct SQL statements using Python's string operations, as this makes my database vulnerable to SQL attacks. As such, I am using the 'parameter substitution' functionality of the sqlite3 Python library to pass in values from Python variables. The value is represented within the query with a placeholder of '?', and the actual values are passed in as a tuple as seen below with the email address.
    c.execute("SELECT * FROM details WHERE email=?", [email])
    # Returns the result of the SQL query in the form of a list
    return (c.fetchall())
 
# This function takes the user's details that they have registered with and stores it in the database. This is called after a user has successfully registered.
def store_details(first_name, last_name, email, password):
    conn, c = init()
    # Calls the "encrypt_pass" function which returns a hashed version of the registered password
    hashed_password = encrypt_pass(email, password)
    # Sets the user's role to 'user'. There is only one account with admin privileges, and the credentials for this account are given to the cashier at the uniform store.
    role = "user"
    # SQL INSERT statement that inserts the user's registered details into the database. Again, note the use of parameter substitution to reduce vulnerability to SQL attacks.
    c.execute("INSERT INTO details (first_name, last_name, email, password, role) VALUES(?,?,?,?,?)", (first_name, last_name, email, hashed_password, role))
    # Commits the changes to the database and closes the connection.
    conn.commit()
    conn.close()
 
# An algorithm that takes in an email and password and encrypts this. This is called either when a user is registered and their password needs to be hashed and stored, or when a user logs in and the server needs to hash the provided password to check it against all the other hashed passwords in the database.
def encrypt_pass(email, password):
    # Encodes the password in bytes using 'utf-8' encoding
    password = bytes(password, 'utf-8')
    # Encodes the email in bytes using 'utf-8' encoding. This is used as a 'salt' in the hashing process.
    salt = bytes(email, 'utf-8')
    # Creates a password hash using sha512 hashing, with the encoded email address as a salt and returns this hashed password
    hashed_pass = hashlib.sha512(password+salt).digest()
    return hashed_pass
 
# Checks the user's details to see if they are valid. Returns a list of all the matching login details that correspond with those entered by the user. This is called whenever a user tries to log in.
def check_details(email, password):
    conn, c = init()
    # Hashes the password entered along with the user's email as a salt to compare with the hashed version of the password within the database. This makes sure passwords in the database are never converted into plaintext for security purposes. 
    check_hash = encrypt_pass(email, password)
    # SQL SELECT statement that retrieves all of the login details that match with those entered by the user
    c.execute("SELECT * FROM details WHERE email=? AND password=? ", (email, check_hash))
    # Returns a list of all matching login details 
    return (c.fetchall())
 
# A function that retrieves all a user's details given the user's email address, and returns a dictionary with all this information. This is called whenever a user logs in.
def get_user_details(email):
    conn, c = init()
    # SQL SELECT statement that retrieves all the user's details from the database where the email address is identical to that provided as a parameter.
    c.execute("SELECT * FROM details WHERE email=?", (email,))
    # Creates a dictionary with key:value pairs that make it easy to access a given piece of information about the user
    user_details = {"user_id":"", "email":"","first_name":"", "last_name":""}
    db_search_return = c.fetchall()
    # Matches the values retrieved from the database to the appropriate keys in the database.
    user_details["user_id"] = db_search_return[0][0]
    user_details["email"] = db_search_return[0][1]
    user_details["first_name"] = db_search_return[0][3]
    user_details["last_name"] = db_search_return[0][4]
    user_details["role"] = db_search_return[0][5]
    # Returns the dictionary with all the user details.
    return user_details
 
# Gets a list of all the names of the available products for use on the "Display" page. This is called whenever a user navigates to the /display route and wishes to have a list of the names of all the available products.
def get_product_names():
    conn, c = init()
    # Retrieves all uniform items from the uniform table.
    c.execute("SELECT * FROM uniform")
    items = c.fetchall()
    # Creates a list of items that is to be returned with the names of the products. 
    item_list = []
    # Iterates through the results from the database query and checks if the item has already been added to the item list. This is necessary as there are multiple items with the same name but with different sizes and IDs.
    for item in items:
        if item[1] in item_list:
            continue
        else:
            item_list.append(item[1])
    print(item_list)
    return item_list
 
# Gets information about an item when given the name of the item. THis is called whenever a user clicks on a specific item to get more details about it and to place an order for that item.
def get_item_info(item):
    conn, c = init()
    # Retrieves all items in the 'uniform' table that match with the item name provided as a parameter.
    c.execute("SELECT * FROM uniform WHERE item_name=?", (item,))
    item = c.fetchall()
    # Creates a dictionary with key:value pairs that allow for easy access of the information about each item
    return_data = {"id":"","name":"","available_sizes":[], "price":0, "quantity":0}
    # Adds the item ID without the 'size' suffix to the dictionary
    return_data["id"] = item[0][0][0:6]
    # Adds the item price to the dictionary
    return_data["price"] = item[0][2]
    # Adds the item name to the dictionary
    return_data["name"] = item[0][1]
    # Iterates through each of the sizes available for the product
    for detail in item:
        # Appends all available sizes to the list that matches the key 'available_sizes' in the dictionary.
        return_data["available_sizes"].append(detail[3])
    return return_data
 
# This function calculates the final price of an order given the ID of the uniform being ordered and the quantity being ordered.
def calclate_price(uniform_id, quantity):
    conn, c = init()
    # Gets the price of the uniform that corresponds with the given uniform_id as a parameter.
    c.execute("SELECT price FROM uniform WHERE uniform_id=?", (uniform_id,))
    # Uses indexing to retrieve the price from the database query.
    price = c.fetchall()[0][0]
    # Multiplies the price of the uniform by the quantity desired to obtain the final price of the order.
    final_price = price * int(quantity)
    return final_price
 
# This function stores a user made order in the database. It is given "order_info", a dictionary with information regarding the order, and "user_id", the id of the user who made the order. The order is then given an ID within the database and is stored alongside the user ID. This is called whenever a user makes an order.
def add_order(order_info, user_id):
    conn, c = init()
    # Uses the "date" library to get the date that the order was made. This is then stored in the database alongside the order details.
    todays_date = (date.today()).strftime("%d/%m/%Y")
    # SQL INSERT statement to store the order in the 'orders' table within the database.
    c.execute('INSERT INTO orders (item_id, quantity, date, customer_id, final_price, order_status) VALUES(?,?,?,?,?,?)', (order_info["id"], order_info["quantity"], todays_date, user_id, order_info["price"], "Incomplete"))
    # Commits the changes and closes the database connection.
    conn.commit()
    conn.close()
 
# This function retrieves all the orders made by a specific user, given the user's ID. THis is called whenever a user wishes to see all the orders they have placed.
def get_user_orders(user_id):
    conn, c = init()
    # Retrieves all orders that have the corresponding user_id attached to it
    c.execute("SELECT * FROM orders WHERE customer_id=?", (user_id,))
    order_details = c.fetchall()
    # Returns the list of all the orders that were found to match the user's ID.
    return order_details
 
# Retrieves the details of an order given the order's specific ID. This is used when an admin user wishes to manage a specific order.
def get_order(order):
    conn, c = init()
    # Retrieves the details of the order from the 'orders' table in the database.
    c.execute("SELECT * FROM orders where order_id=?", (order,))
    order = c.fetchall()
    # Returns the order details
    return order
 
# Retrieves all orders that are stored in the database. Used to render the admin orders page.
def get_all_orders():
    conn, c = init()
    c.execute("SELECT * FROM orders")
    return (c.fetchall())
 
# Gets information regarding a specific product given the product's uniform id. This is called whenever an admin user wishes to manage stock quantities of a specific item.
def get_product_details(item_id):
    conn, c = init()
    c.execute("SELECT * FROM uniform WHERE uniform_id=?", (item_id,))
    # Returns the row in the database with the details of the item that was queried
    return c.fetchall()
 
# This function is used to change the order status, either from "Incomplete" to "Pending" when an admin initiates the completion process, or "Pending" to "Complete" when the user acknowledges that they have received the order. The appropriate status change is passed in as a parameter.
def change_order_status(order, status):
    conn, c = init()
    # SQL statement that updates the 'order_status' column of the order with the corresponding order_id that was passed in as a parameter.
    c.execute("UPDATE orders SET order_status=? WHERE order_id=?", (status, order))
    # Commits the changes and closes the connection to the database.
    conn.commit()
    conn.close()
 
# This function takes in a search term as a parameter and searches through the 'uniform' table for all items that match the search criteria. This is called whenever the user searches for an item.
def search_items(term):
    conn, c = init()
    # Calls the 'get_products' function defined earlier to retrieve a list of all the items in the database.
    items = get_product_names()
    # Creates an empty list for all the search results to be appended to
    search_results = []
    # Iterates through each item that was retrieved from the database.
    for item in items:
        # Checks if the search term is present in the name of the item
        if term in item:
            # If the term is present, the item is appended to the array of search results.
            search_results.append(item)
    # If the length of the array of search results is 0, this means that there were no items that matched the search term. As such, an appropriate message is added to the array to be displayed on a webpage.
    if len(search_results) == 0:
        search_results.append("No results were found!")
    return search_results
 
# Gets a list of all the products available in the database. This is used when an admin user wants to display the list of all the products for them to manage stock quantities.
def get_products():
    conn, c = init()
    c.execute("SELECT * FROM uniform")
    return c.fetchall()
 
# This function checks if the quantity ordered by a user exceeds the available quantity that is in stock. This is called before an order made by a user can be accepted and stored in the database.
def check_quantity(item, quantity):
    conn, c = init()
    # SQL Select statement to retrieve the remaining stock of the item that was passed in as a parameter to this function.
    c.execute("SELECT stock FROM uniform WHERE uniform_id=?", (item,))
    # Uses indexing to retrieve the stock data from the database query result
    current_quantity = c.fetchall()[0][0]   
    # Calculates what the new stock quantity will be after the quantity ordered by the user is removed.
    new_quantity = int(current_quantity) - int(quantity)
    # If the remaining quantity is less than 0, this means that there aren't enough stocks for the order to be processed. The function returns 'False' and this is handled by the server.
    if new_quantity < 0:
        return False
    # If the remaining quantity is equal to or more than 0, this means that there is enough stock for the order to be processed.
    else:
        return True
 
# This function updates the remaining stock of a particular item. This can be used both when the admin manually adds stocks, or when the user makes an order and the quantity decreases.
def update_stock(quantity, item):
    conn, c = init()
    # Gets the current stock level of the item from the database.
    c.execute("SELECT stock FROM uniform WHERE uniform_id=?", (item,))
    # Uses indexing to obtain the quantity from the database query result.
    current_quantity = c.fetchall()[0][0]   
    # Calculates the new quantity by adding the quantity passed into the function to the existing quantity. If the user is ordering, the quantity to be added is negative to reflect a depletion of stocks.
    new_quantity = int(current_quantity) + int(quantity)
    # SQL UPDATE statement to update the stock levels to reflect the new stock within the database.
    c.execute('UPDATE uniform SET stock=? WHERE uniform_id=?', (new_quantity, item))
    # Commit the changes and close the connection to the database.
    conn.commit()
    conn.close()

"""
def add_item(uniform_id, name, price, size, stock):
    conn, c = init()
    c.execute("INSERT INTO uniform (uniform_id, item_name, price, size, stock) VALUES(?,?,?,?,?)", (uniform_id, name, price, size, stock))
    conn.commit()
    conn.close()

add_item("300040-L", "Black Hoodie", 50, "L", 500)
"""