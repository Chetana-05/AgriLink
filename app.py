from flask import Flask, render_template, request, jsonify, redirect, session
from pymongo import MongoClient
from bson import ObjectId

cluster = MongoClient("mongodb+srv://chetana:1234567890@cluster0.nddb1.mongodb.net/")
db = cluster['agrilink']
users = db["users"]
bookings=db['bookings']

app = Flask(__name__)
app.secret_key="agrilink"

@app.route("/")
def index():
    return render_template("hackmain.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/feedback")
def feedback():
    return render_template("feedback.html")

@app.route("/farmer_dashboard")
def farmer_dashboard():
    workers=users.find({"Role":"worker"})
    return render_template("farmers.html",workers=workers)

@app.route("/worker_dashboard")
def worker_dashboard():
    booking=bookings.find({"worker":session['username']})
    return render_template("worker.html",bookings=booking)

@app.route("/login", methods=["POST"])
def logi():
    username = request.form.get("username")
    password = request.form.get("password")
    
    user = users.find_one({"User_name": username})
    
    if user and user.get("Password") == password:
        role = user.get("Role")
        if role == "farmer":
            session['username']=username
            return redirect("/farmer_dashboard")
        elif role == "worker":
            session['username']=username
            return redirect("/worker_dashboard")
    else:
        return jsonify({"error": "Invalid username or password"}), 401

@app.route("/register", methods=["POST"])
def register_user():
    data = {
        "User_name": request.form.get("username"),
        "Password": request.form.get("password"),
        "Role": request.form.get("role"),
        "Work_Type": request.form.get("worktype"),
        "Mobile_Number": request.form.get("mobile_number"),
        "Address": request.form.get("Address"),
        "Village_Name": request.form.get("village_name"),
        "State_Name": request.form.get("state_name"),
        "District_Name": request.form.get("district_name")
    }
    
    existing_user = users.find_one({"User_name": data["User_name"]})
    if existing_user:
        return render_template("register.html",data="Username already exists. Please choose another username."), 400
    
    users.insert_one(data)
    return render_template("login.html"), 201

@app.route("/bookworker")
def book_worker():
    id=request.args.get("id")
    user=users.find_one({"_id":ObjectId(id)})
    worker=bookings.find_one({"booked_by":session['username'],"worker":user['User_name']})
    farmer=users.find_one({"User_name":session['username']})
    workers=users.find({"Role":"worker"})
    if worker:
        return render_template("farmers.html",data="Request already sent",workers=workers)
    bookings.insert_one({"booked_by":session["username"],"worker":user['User_name'],"Address":farmer["Address"],"Village_name":farmer["Village_Name"],"Mobile_number":farmer['Mobile_Number'],"status":"pending"})
    return render_template("farmers.html",data="Request sent successfuly",workers=workers)

@app.route("/accept", methods=["GET"])
def accept_worker():
    worker_id = request.args.get("id")
    if not worker_id:
        return jsonify({"error": "Worker ID is required"}), 400
    
    result = bookings.update_one({"_id": ObjectId(worker_id)}, {"$set": {"status": "accepted"}})
    if result.modified_count:
        return redirect("/worker_dashboard")
    return jsonify({"error": "Worker not found"}), 404

@app.route("/reject", methods=["GET"])
def reject_worker():
    worker_id = request.args.get("id")
    if not worker_id:
        return jsonify({"error": "Worker ID is required"}), 400
    
    result = bookings.update_one({"_id": ObjectId(worker_id)}, {"$set": {"status": "rejected"}})
    if result.modified_count:
        return redirect("/worker_dashboard")
    return jsonify({"error": "Worker not found"}), 404

@app.route("/mybookings")
def mybookings():
    booking=bookings.find({"booked_by":session['username']})
    return render_template("bookings.html",bookings=booking)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
