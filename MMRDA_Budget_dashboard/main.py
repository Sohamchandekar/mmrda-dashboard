from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import os
import plotly.express as px


from backfunctions import (total_revenue_card,total_expense_card,proportion_expense_card, proportion_revenue_card,
                           excel_processing_to_dataframe, feature_engineering, rename_date_columns, insights_calculation)

from backfunctions import (revenue_gauge, expense_gauge, revenue_distribution_donut, expense_distribution_donut, growth_bar_chart,
                           average_revenue_per_expense_card, position_card, cash_inhand_card, date_time_card)
from plotly.io import to_html

from backfunction2 import read_excel_and_process, generate_table_from_dataframe

from backfunction3 import ADB_NDB_loanstructure_processing
app = Flask(__name__, static_folder="static")
app.config['UPLOAD_FOLDER'] = 'uploads/'

# Define the global DataFrames
receipt_data = None
receipt_backdata = None
expense_data = None
expense_backdata = None

insight_dataframe = None
key_insights = {}
predicted_revenue = {}

# Define the global DataFrames
engineering_division = None
town_country_division = None
transport_communication_division = None
metro_projects_division = None
mono_piu_division = None

adb_ndb_dict = {}

# Sample DataFrame
from flask import Flask, render_template, jsonify, request






# Route for the main upload page
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        receipts_file = request.files['receipts_data']
        expenditure_file = request.files['expenditure_data']
        project_breakdown_file = request.files['project_breakdown']
        loan_breakdown_file = request.files['loan_breakdown']  # Added loan breakdown file

        if receipts_file and expenditure_file and project_breakdown_file and loan_breakdown_file:
            # Save the uploaded files
            receipts_path = os.path.join(app.config['UPLOAD_FOLDER'], receipts_file.filename)
            expenditure_path = os.path.join(app.config['UPLOAD_FOLDER'], expenditure_file.filename)
            project_breakdown_path = os.path.join(app.config['UPLOAD_FOLDER'], "project_breakdown.xlsx")
            loan_breakdown_path = os.path.join(app.config['UPLOAD_FOLDER'], "loan_breakdown.xlsx")  # Loan breakdown path

            receipts_file.save(receipts_path)
            expenditure_file.save(expenditure_path)
            project_breakdown_file.save(project_breakdown_path)
            loan_breakdown_file.save(loan_breakdown_path)  # Save loan breakdown file

            # Process the receipts and expenditure files
            global receipt_data, receipt_backdata, expense_data, expense_backdata
            global insight_dataframe, key_insights
            (receipt_data, receipt_backdata, expense_data, expense_backdata) = excel_processing_to_dataframe(
                receipts_path, expenditure_path
            )
            receipt_backdata = feature_engineering(receipt_backdata, 'Sept 2024')
            expense_backdata = feature_engineering(expense_backdata, 'Sept 2024')

            receipt_backdata = rename_date_columns(receipt_backdata)
            expense_backdata = rename_date_columns(expense_backdata)

            insight_dataframe, key_insights = insights_calculation(receipt_backdata, expense_backdata)

            # Process the project breakdown file
            global engineering_division, town_country_division, transport_communication_division,metro_projects_division,mono_piu_division
            (engineering_division,
             town_country_division,
             transport_communication_division,
             metro_projects_division,
             mono_piu_division) = read_excel_and_process(project_breakdown_path)

            global adb_ndb_dict
            adb_ndb_dict = ADB_NDB_loanstructure_processing(loan_breakdown_path)
            print(adb_ndb_dict)




            # Redirect to the home page after processing
            return redirect(url_for('home'))

    return render_template("index.html")


@app.route("/home")
def home():
    return render_template("home.html", key_insights=key_insights)

# Route for the dashboard page
@app.route("/level1")
def level1():

    # # Generate the Plotly figure
    revenue_gauge_chart = revenue_gauge(receipt_backdata)
    expense_gauge_chart = expense_gauge(expense_backdata)

    revenue_distribution_donut_chart = revenue_distribution_donut(receipt_backdata)
    expense_distribution_donut_chart = expense_distribution_donut(expense_backdata)

    growth_bar_chart_chart = growth_bar_chart(receipt_backdata, expense_backdata)




    # # Convert the figure to HTML for embedding

    revenue_gauge_chart_html = to_html(revenue_gauge_chart, full_html=False)
    expense_gauge_chart_html = to_html(expense_gauge_chart, full_html= False)
    revenue_distribution_donut_chart_html = to_html(revenue_distribution_donut_chart, full_html= False)
    expense_distribution_donut_chart_html = to_html(expense_distribution_donut_chart, full_html= False)
    growth_bar_chart_chart_html = to_html(growth_bar_chart_chart, full_html=False)



    #
    # # Card
    date_card_html  = date_time_card()

    total_revenue_card_html = total_revenue_card(receipt_backdata)
    total_expense_card_html = total_expense_card(expense_backdata)

    proportion_revenue_card_html = proportion_revenue_card(receipt_backdata)
    proportion_expense_card_html = proportion_expense_card(expense_backdata)

    utility_card_html = average_revenue_per_expense_card(insight_dataframe, as_on_month = 'Sep 2024')
    position_card_html = position_card(receipt_backdata,expense_backdata)
    cash_inhand_card_html = cash_inhand_card(receipt_backdata,expense_backdata, previous_closing= 500)



    # Pass the HTML to your dashboard template
    return render_template("dashboard1.html",

                           date_card_html = date_card_html,

                           total_revenue_card_html = total_revenue_card_html,
                           total_expense_card_html = total_expense_card_html,
                           proportion_revenue_card_html = proportion_revenue_card_html,
                           proportion_expense_card_html = proportion_expense_card_html,
                           position_card_html = position_card_html,


                           revenue_gauge_chart_html = revenue_gauge_chart_html,
                           expense_gauge_chart_html = expense_gauge_chart_html,

                           revenue_distribution_donut_chart_html = revenue_distribution_donut_chart_html,
                           expense_distribution_donut_chart_html = expense_distribution_donut_chart_html,

                           utility_card_html= utility_card_html,
                           growth_bar_chart_chart_html =growth_bar_chart_chart_html,
                           cash_inhand_card_html = cash_inhand_card_html
                           )

@app.route("/level2")
def level2():
    return render_template("dashboard2.html")

@app.route('/engineering')
def engineering():
    if engineering_division is not None:
        # Generate the table for the Engineering Division
        table_html = generate_table_from_dataframe(engineering_division, 'Oct 2024')
        return render_template("dashboard2.html", table_html=table_html)
    return jsonify({"error": "Engineering division data not found"}), 404

@app.route('/town')
def town():
    if town_country_division is not None:
        table_html = generate_table_from_dataframe(town_country_division,cutoff_month='Oct 2024')
        return render_template("dashboard2.html", table_html=table_html)
    return jsonify({"error": "Town & Country Planning data not found"}), 404

@app.route('/transportCommunication')
def transportCommunication():
    if transport_communication_division is not None:
        table_html = generate_table_from_dataframe(transport_communication_division,cutoff_month='Oct 2024')
        return render_template("dashboard2.html", table_html=table_html)
    return jsonify({"error": "Town & Country Planning data not found"}), 404

@app.route('/metroProjects')
def metroProjects():
    if metro_projects_division is not None:
        table_html = generate_table_from_dataframe(metro_projects_division,cutoff_month='Oct 2024')
        return render_template("dashboard2.html", table_html=table_html)
    return jsonify({"error": "Town & Country Planning data not found"}), 404

@app.route('/monoPiu')
def monoPiu():
    if mono_piu_division is not None:
        table_html = generate_table_from_dataframe(mono_piu_division,cutoff_month='Oct 2024')
        return render_template("dashboard2.html", table_html=table_html)
    return jsonify({"error": "mono_piu_division data not found"}), 404


from backfunction3 import ADB_NDB_loanstructure_processing
from backfunction3 import project_loan_card, plot_repayment_trend

@app.route("/level3")
def level3():
    return render_template("dashboard3.html")


@app.route("/page1")
def adb_ndb_dashboard():
    # Fetch data specific to ADB/NDB
    loan_name = "ADB/NDB"
    loan_cards_html = project_loan_card(adb_ndb_dict)

    repayment_chart = plot_repayment_trend(adb_ndb_dict)


    repayment_chart_html = to_html(repayment_chart, full_html= False)

    return render_template("loan_dashboard.html",
                           loan_cards_html=loan_cards_html,
                           repayment_chart_html = repayment_chart_html)


