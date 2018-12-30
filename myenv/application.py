import os
import re
import pandas as pd
from flask import Flask, jsonify, render_template, request, url_for, flash, redirect,json, send_file
from flask_jsglue import JSGlue
from datetime import date, timedelta, datetime
from sys import argv, exit, stdout
from random import Random
import argparse
from ortools.sat.python import cp_model
from google.protobuf import text_format
from collections import defaultdict
from schedule_generator import main as sc
from schedule_generator import PARSER, solve_shift_scheduling
from talent_schedule_generator import main as tc
from datetime import datetime, date, time


from cs50 import SQL
#Configure application
app = Flask(__name__)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///myenv/database.db")

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
def index():
    """Render map"""
    return render_template("index.html")

@app.route("/about")
def about():
    """Render about page"""
    return render_template("about.html")

@app.route("/delete_requests/<id>",methods = ["GET","POST"])
def delete_requests(id):
    db.execute("DELETE from requests where id = :id", id = id)
    return redirect(url_for("requests"))

@app.route("/download_as_csv/<role>",methods = ["GET","POST"])
def download_as_csv(role):
    if role == 'Manager':
        return send_file('/home/ubuntu/workspace/final/templates/manager-schedule-for-December.csv',
                     mimetype='text/csv',
                     attachment_filename='manager-schedule-for-December.csv',
                     as_attachment=True)
    else:
        return send_file('/home/ubuntu/workspace/final/templates/talent-schedule-for-December.csv',
                     mimetype='text/csv',
                     attachment_filename='talent-schedule-for-December.csv',
                     as_attachment=True)


@app.route("/employees", methods=["GET", "POST"])
def employees():
    """Add new employee"""
    if request.method == "POST":
        try:
            name = request.form.get("first-name")
            last_name = request.form.get("last-name")
            role = request.form.get("role")
            email = request.form.get("email")
        except:
            return apology("enter some input")

        if not name:
            return apology("enter employee name")
        if not last_name:
            return apology("enter employee last name")
        if not role:
            return apology("enter employee role")
        if not email:
            return apology("enter employee email")

        db.execute("INSERT INTO employees (first_name,last_name,role,email) \
                    VALUES(:first_name, :last_name, :role, :email)", \
                    first_name = name, last_name=last_name, \
                    role = role, email = email)
        employees = db.execute("SELECT * FROM employees ORDER BY role ASC")
        total_employees = db.execute("SELECT COUNT(first_name) FROM employees")
        return redirect(url_for("employees"))
    employees = db.execute("SELECT * FROM employees ORDER BY role ASC")
    total_managers = db.execute("SELECT COUNT(role) FROM employees WHERE role = :role", role = "Manager")
    total_talents = db.execute("SELECT COUNT(role) FROM employees WHERE role = :role", role = "Talent")
    total_managers = total_managers[0]['COUNT(role)']
    total_talents = total_talents[0]['COUNT(role)']
    return render_template("employees.html",employees = employees,  total_talents = total_talents,total_managers = total_managers)

@app.route("/requests", methods=["GET", "POST"])
def requests():
    """Add new request"""
    if request.method == "POST":
        try:
            name = request.form.get("name")
            day = int(request.form.get("day"))
            month = request.form.get("month")
            req= request.form.get("req")
        except:
            return apology("enter some input")

        if not name:
            return apology("enter employee name")
        if not day or day < 1 or day >31:
            return apology("enter valid day")
        if not month:
            return apology("enter month")
        if not req:
            return apology("enter request")

        employees = db.execute("SELECT * FROM employees ORDER BY first_name ASC")

        db.execute("INSERT INTO requests (requestee,day,month,req) \
                    VALUES(:requestee, :day, :month, :req)", \
                   requestee = name, day = day, \
                    month = month, req = req)

        return redirect(url_for("requests"))
    employees = db.execute("SELECT * FROM employees ORDER BY first_name ASC")
    requests = db.execute("SELECT * FROM requests")
    total_requests = db.execute("SELECT COUNT(*) FROM requests")
    total_requests = total_requests[0]['COUNT(*)']
    return render_template("requests.html", employees = employees,requests = requests, total_requests = total_requests)

@app.route("/template", methods=["GET", "POST"])
def schedule():
    """Prompts the user to create a new schedule"""
    return render_template("template.html")

@app.route("/template1", methods=["GET", "POST"])
def schedule_talent():
    """Prompts the user to create a new schedule"""
    return render_template("template1.html")


@app.route('/create_manager_schedule', methods = ["POST","GET"])
def make_schedule():
    """Creates and loads a new schedule"""
    if request.method == "POST":
        month = datetime.now().strftime('%B')
        PARSER = argparse.ArgumentParser()
        PARSER.add_argument( '--output_proto', default="", help='Output file to write the cp_model' 'proto to.')
        PARSER.add_argument('--params', default="", help='Sat solver parameters.')
        args, unknown = PARSER.parse_known_args()
        this = pd.DataFrame.from_dict(sc(args))
        schedule = this.transpose()
        length = len(schedule.columns)
        days = list(range(1, length+1))
        df = pd.DataFrame(days)
        df = df.transpose()
        schedule.columns=["M", "T", "W", "T", "F", "S","S","M", "T", "W", "T", "F", "S","S","M", "T", "W", "T", "F", "S","S","M", "T", "W", "T", "F", "S","S"]
        schedule.rename(index={0:"Jose",1: 'Claudia',2:"Alba",3:"Javi",4:'Varun'},inplace = True)
        path = r'final/templates'
        schedule.to_html('/home/ubuntu/workspace/final/templates/new-schedule.html')
        filename1 = 'manager-schedule-for-' + month + '.csv'
        schedule.to_csv(os.path.join(r"/home/ubuntu/workspace/final/templates",filename1))
        return render_template("template.html", month = month)

@app.route('/create_talent_schedule', methods = ["POST","GET"])
def make_talent_schedule():
    """Creates and loads a new schedule"""
    if request.method == "POST":
        month = datetime.now().strftime('%B')
        PARSER = argparse.ArgumentParser()
        PARSER.add_argument( '--output_proto', default="", help='Output file to write the cp_model' 'proto to.')
        PARSER.add_argument('--params', default="", help='Sat solver parameters.')
        args, unknown = PARSER.parse_known_args()
        this = pd.DataFrame.from_dict(tc(args))
        talent_schedule = this.transpose()
        length = len(talent_schedule.columns)
        talent_schedule.columns=["M", "T", "W", "T", "F", "S","S","M", "T", "W", "T", "F", "S","S","M", "T", "W", "T", "F", "S","S","M", "T", "W", "T", "F", "S","S"]
        talent_schedule.rename(index={0:"Kate",1: 'Victor',2:"Jorge",3:"Regina",4:'Alvara',5:'Borja',6:'Ana',7:'Cris',8:'Lora',9:'Natalia',10:'Carles'},inplace = True)
        path = r'final/templates'
        talent_schedule.to_html('/home/ubuntu/workspace/final/templates/talent-schedule.html')
        filename2 = 'talent-schedule-for-'+ month + '.csv'
        talent_schedule.to_csv(os.path.join(r"/home/ubuntu/workspace/final/templates/",filename2))
        return render_template("template1.html", month = month)

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return sw
    return render_template("apology.html", top=code, bottom=escape(message)), code

if __name__ == "__main__":
    app.debug = True
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
