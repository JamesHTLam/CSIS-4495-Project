import os
import flask
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
from flask_bcrypt import Bcrypt
import MySQLdb
import pandas as pd
import numpy as np
import plotly
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import dash
from dash import Dash, Input, Output, dash_table, dcc, ctx, no_update
from dash.dash_table import FormatTemplate
from dash.dash_table.Format import Format, Scheme
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from datetime import date
import stats_can
from keras.models import load_model
import cv2
from deepface import DeepFace

app = Flask(__name__)

app.secret_key = 'abc'

connection = MySQLdb.connect(host="localhost", user="root", passwd="", db="csis4495_user")

transaction_categories=['Auto & Transport', 'Bills & Utilities', 'Business Services', 'Education', 'Entertainment', 'Fees & Charges', 'Financial', 'Food & Dining', 'Gifts & Donations',
'Health & Fitness', 'Home', 'Kids', 'Loans', 'Personal Care', 'Pets', 'Shopping', 'Taxes', 'Travel', 'Uncategorized']

with app.app_context():
    '''cursor=connection.cursor()
    cursor.execute("""CREATE TABLE Users (
    UserID int AUTO_INCREMENT PRIMARY KEY,
    FirstName varchar(255) NOT NULL,
    LastName varchar(255) NOT NULL,
    Email varchar (255) NOT NULL,
    Password varchar(255) NOT NULL,
    Face BLOB
    ) """)
    cursor.execute("""CREATE TABLE Transactions (
    TransactID int AUTO_INCREMENT PRIMARY KEY,
    TransactDate date NOT NULL,
    Description varchar(255) NOT NULL,
    Category varchar(255) NOT NULL,
    Amount numeric (10, 2) NOT NULL,
    UserID int Not NULL,
    FOREIGN KEY (UserID) REFERENCES Users (UserID) ON DELETE CASCADE
    )""")
    connection.commit()
    cursor.close()'''
    dash_app1=Dash(__name__, server = app, external_stylesheets=[dbc.themes.BOOTSTRAP], url_base_pathname='/dash1/')
    dash_app1.layout=dash.html.Br()
    dash_app2=Dash(__name__, server = app, external_stylesheets=[dbc.themes.BOOTSTRAP], url_base_pathname='/dash2/')
    dash_app2.layout=dash.html.Br()
    cap = cv2.VideoCapture(0)

@app.route('/')
def index():
    return render_template ("index.html")

def gen_frames():  
    while True:
        success, frame = cap.read()  
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/register', methods=['GET', 'POST'])
def register(): 
    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        password = request.form['password']
        face_added = 'face' in request.form
        if not firstname or not lastname or not email or not password:
            flash("You Have Not Entered All Required Data")
        else:
            cursor=connection.cursor()
            cursor.execute('SELECT * FROM Users WHERE Email = %s', (email,))
            user=cursor.fetchone()
            if user:
                flash("An Account With This Email Already Exists!")
            else:
                bcrypt = Bcrypt()
                hashed_pw = bcrypt.generate_password_hash(password)
                if face_added:
                    ret, frame = cap.read()
                    cv2.imwrite('static/register_picture.jpg', frame)
                    try: 
                        face_objs = DeepFace.extract_faces('static/register_picture.jpg', detector_backend='mtcnn')
                        with open('static/register_picture.jpg', 'rb') as file:
                            face = file.read()
                        cursor.execute('INSERT INTO Users (FirstName, LastName, Email, Password, Face) VALUES (%s, %s, %s, %s, %s)', (firstname, lastname, email, hashed_pw, face))
                        connection.commit()
                        flash("You Have Created an Account")
                    except:
                        flash("No Valid Face Found. Please Adjust Angles To Provide A Valid Facial Image.")
                else:
                    cursor.execute('INSERT INTO Users (FirstName, LastName, Email, Password, Face) VALUES (%s, %s, %s, %s, NULL)', (firstname, lastname, email, hashed_pw))
                    connection.commit()
                    flash("You Have Created an Account")        
    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        face_login = 'face' in request.form
        if not email:
            flash("Failed To Login! Email Is Not Provided.")
        else:
            cursor=connection.cursor()
            cursor.execute('SELECT * FROM Users WHERE Email = %s', (email,))
            user=cursor.fetchone()
            if user:
                if not face_login:
                    bcrypt = Bcrypt()
                    true_password=user[4]
                    if bcrypt.check_password_hash(true_password, password):
                        session["user_id"]=user[0]
                        session["user_firstname"]=user[1]
                        session["user_lastname"]=user[2]
                        session["user_email"]=user[3]
                        return redirect(url_for('user_profile'))
                    else:
                        flash("Failed To Login! Password Is Not Correct.")
                else:
                    try:
                        face = user[5]
                        with open('static/user_face.jpg', 'wb') as file:
                            file.write(face)
                        ret, frame = cap.read()
                        cv2.imwrite('static/verify_picture.jpg', frame)
                        try:
                            ver_result=DeepFace.verify('static/user_face.jpg', 'static/verify_picture.jpg', model_name='SFace', distance_metric = 'cosine', detector_backend='mtcnn')
                            if ver_result['verified']==True:
                                session["user_id"]=user[0]
                                session["user_firstname"]=user[1]
                                session["user_lastname"]=user[2]
                                session["user_email"]=user[3]
                                return redirect(url_for('user_profile'))
                            else:
                                flash("Failed to Login! Facial Image Unverified.")
                        except:
                            flash("Failed to Login! No Valid Face Found. Please Adjust Angles To Provide A Valid Facial Image.")
                    except:
                        flash("Failed To Login! Your Account Was Not Registered With A Facial Image For Login.")        
            else:
                flash("Failed To Login! Email Is Not Correct")
    return render_template ("login.html")

@app.route('/user_profile', methods=['GET', 'POST'])
def user_profile():
    user_id=session["user_id"]
    user_firstname=session["user_firstname"]
    user_lastname=session["user_lastname"]
    user_email=session["user_email"]
    
    cursor=connection.cursor()
    cursor.execute('SELECT * FROM Transactions WHERE UserID = %s', (user_id,))
    transactions=cursor.fetchall()

    return render_template('user_profile.html', user_firstname=user_firstname, transactions=transactions)

@app.route('/add_individual_transaction', methods=['GET', 'POST'])
def add_individual_transaction():
    if request.method=='POST':
        date = request.form['date']
        description = request.form['description']
        category = request.form['category']
        amount = request.form['amount']
        user_id=session["user_id"]

        if not date or not description or not category or not amount:
            flash("You Have Not Entered All Required Data.")
        else:
            cursor=connection.cursor()
            cursor.execute('INSERT INTO Transactions (TransactDate, Description, Category, Amount, UserID) VALUES (%s, %s, %s, %s, %s)', (date, description, category, amount, user_id,))
            connection.commit()
            return redirect(url_for('user_profile'))
    return render_template('add_individual_transaction.html', transaction_categories=transaction_categories)

@app.route('/add_excel_transactions', methods=['GET', 'POST'])
def add_excel_transactions():
    if request.method=='POST':
        cursor=connection.cursor()
        user_id=session["user_id"]

        if not request.files['transaction_excel_file']:
            flash('No File Uploaded!')
        else:
            uploaded_file=request.files['transaction_excel_file']
            file_path="static/" + uploaded_file.filename
            uploaded_file.save(file_path)
            file_path=file_path.replace('"','')
            df=pd.read_csv(file_path)
            df['date_formatted']=pd.to_datetime(df['Date'], format = '%m/%d/%Y').dt.strftime("%Y-%m-%d")

            for row in df.iterrows():
                cursor.execute('INSERT INTO Transactions (TransactDate, Description, Category, Amount, UserID) VALUES (%s, %s, %s, %s, %s)', (row[1][9], row[1][1], row[1][5], row[1][3], user_id))

            cursor.execute("""DELETE FROM Transactions WHERE 
                Category = 'Income' OR Category = 'Bonus' OR Category = 'Interest Income' OR Category = 'Paycheck' OR Category = 'Reimbursement' OR Category = 'Rental Income' OR Category = 'Returned Purchase' OR
                Category = 'Investments' OR Category = 'Buy' OR Category = 'Deposit' OR Category = 'Dividend & Cap Gains' OR Category = 'Sell' OR Category = 'Withdrawal' OR
                Category = 'Transfer' OR Category = 'Credit Card Payment' OR Category = 'Transfer for Cash Spending'
                """)
            cursor.execute("""UPDATE Transactions SET Category = CASE  
                WHEN Category='Auto & Transport' OR Category='Auto Insurance' OR Category='Auto Payment' OR Category='Gas & Fuel' OR Category='Parking' OR Category='Public Transportation' OR Category='Ride Share' OR Category='Service & Parts' THEN 'Auto & Transport' 
                WHEN Category='Bills & Utilities' OR Category='Home Phone' OR Category='Internet' OR Category='Mobile Phone' OR Category='Television' OR Category='Utilities' THEN 'Bills & Utilities' 
                WHEN Category='Business Services' OR Category='Advertising' OR Category='Legal' OR Category='Office Supplies' OR Category='Printing' OR Category='Shipping' THEN 'Business Services' 
                WHEN Category='Education' OR Category='Books & Supplies' OR Category='Student Loan' OR Category='Tuition' THEN 'Education' 
                WHEN Category='Entertainment' OR Category='Amusement' OR Category='Arts' OR Category='Movies & DVDs' OR Category='Music' OR Category='Newspapers & Magazines' THEN 'Entertainment' 
                WHEN Category='Fees & Charges' OR Category='ATM Fee' OR Category='Bank Fee' OR Category='Finance Charge' OR Category='Late Fee' OR Category='Service Fee' OR Category='Trade Commissions' THEN 'Fees & Charges' 
                WHEN Category='Financial' OR Category='Financial Advisor' OR Category='Life Insurance' THEN 'Financial' 
                WHEN Category='Food & Dining' OR Category='Alcohol & Bars' OR Category='Coffee Shops' OR Category='Fast Food' OR Category='Food Delivery' OR Category='Groceries' OR Category='Restaurants' THEN 'Food & Dining' 
                WHEN Category='Gifts & Donations' OR Category='Charity' OR Category='Gift' THEN 'Gifts & Donations' 
                WHEN Category='Health & Fitness' OR Category='Dentist' OR Category='Doctor' OR Category='Eyecare' OR Category='Gym' OR Category='Health Insurance' OR Category='Pharmacy' OR Category='Sports' THEN 'Health & Fitness' 
                WHEN Category='Home' OR Category='Furnishings' OR Category='Home Improvement' OR Category='Home Insurance' OR Category='Home Services' OR Category='Home Supplies' OR Category='Lawn & Garden' OR Category='Mortgage & Rent' THEN 'Home' 
                WHEN Category='Kids' OR Category='Allowance' OR Category='Baby Supplies' OR Category='Babysitter & Daycare' OR Category='Child Support' OR Category='Kids Activities' OR Category='Toys' THEN 'Kids' 
                WHEN Category='Loans' OR Category='Loan Fees and Charges' OR Category='Loan Insurance' OR Category='Loan Interest' OR Category='Loan Payment' OR Category='Loan Principal' THEN 'Loans' 
                WHEN Category='Personal Care' OR Category='Hair' OR Category='Laundry' OR Category='Spa & Massage' THEN 'Personal Care' 
                WHEN Category='Pets' OR Category='Pet Food & Supplies' OR Category='Pet Grooming' OR Category='Veterinary' THEN 'Pets' 
                WHEN Category='Shopping' OR Category='Books' OR Category='Clothing' OR Category='Electronics & Software' OR Category='Hobbies' OR Category='Sporting Goods' THEN 'Shopping' 
                WHEN Category='Taxes' OR Category='Federal Tax' OR Category='Local Tax' OR Category='Property Tax' OR Category='Sales Tax' OR Category='State Tax' THEN 'Taxes' 
                WHEN Category='Travel' OR Category='Air Travel' OR Category='Hotel' OR Category='Rental Car & Taxi' OR Category='Vacation' THEN 'Travel' 
                ELSE 'Uncategorized' 
                END""")
            connection.commit()
            
            return redirect(url_for('user_profile'))
    return render_template('add_excel_transactions.html')

@app.route('/edit_transactions/<int:id>', methods=['GET', 'POST'])
def edit_transactions(id):
    cursor=connection.cursor()
    cursor.execute('SELECT * FROM Transactions WHERE TransactID = %s', (id,))
    edit_transaction=cursor.fetchone()
    user_id=session["user_id"]

    if request.method=='POST':
        date = request.form['date']
        description = request.form['description']
        category = request.form['category']
        amount = request.form['amount']

        cursor.execute('UPDATE Transactions SET TransactDate = %s, Description = %s, Category = %s, Amount = %s WHERE TransactID = %s AND UserID = %s', (date, description, category, amount, id, user_id, ))
        connection.commit()
        return redirect(url_for('user_profile'))
    return render_template('edit_transactions.html', transaction_categories=transaction_categories, edit_transaction=edit_transaction)

@app.route('/delete_transactions/<int:id>', methods=['GET', 'POST'])
def delete_transactions(id):
    user_id=session["user_id"]
    cursor=connection.cursor()
    cursor.execute('DELETE FROM Transactions WHERE TransactID = %s AND UserID = %s', (id, user_id, ))
    connection.commit()
    return redirect(url_for('user_profile'))

@app.route('/delete_all_transactions', methods=['GET', 'POST'])
def delete_all_transactions():
    user_id=session["user_id"]
    cursor=connection.cursor()
    cursor.execute('DELETE FROM Transactions WHERE UserID = %s ', (user_id,))
    connection.commit()
    return redirect(url_for('user_profile'))

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    message="You Have Logout Successfully"
    session.pop("user_id", None)
    session.pop("user_firstname", None)
    session.pop("user_lastname", None)
    session.pop("user_email", None)
    flash(message)
    return redirect(url_for('login'))

@app.route('/analysis', methods=['GET', 'POST'])
def analysis():
    user_id=session["user_id"]
    sql="SELECT * FROM Transactions WHERE UserID = {}".format(user_id)
    df_analysis = pd.read_sql(sql , connection)

    total_amount='${:0,.2f}'.format(df_analysis['Amount'].sum())

    df_analysis['date_formatted_monthly']=pd.to_datetime(df_analysis['TransactDate'], format = '%Y-%m-%d').dt.strftime("%Y-%m")

    monthly_amount=df_analysis.groupby('date_formatted_monthly')['Amount'].aggregate(['count', 'sum']).reset_index()
    monthly_amount.columns=['Date', 'Count', 'Amount']

    average_monthly='${:0,.2f}'.format(monthly_amount['Amount'].mean())
    max_monthly={'Amount':'${:0,.2f}'.format(monthly_amount['Amount'].max()), 'Month':monthly_amount[monthly_amount['Amount']==monthly_amount['Amount'].max()]['Date']}
    min_monthly={'Amount':'${:0,.2f}'.format(monthly_amount['Amount'].min()), 'Month':monthly_amount[monthly_amount['Amount']==monthly_amount['Amount'].min()]['Date']}

    category_amount=df_analysis.groupby('Category')['Amount'].aggregate(['count', 'sum']).reset_index()
    category_amount.columns=['Category','Count', 'Amount']

    max_category={'Amount':'${:0,.2f}'.format(category_amount['Amount'].max()), 'Category':category_amount[category_amount['Amount']==category_amount['Amount'].max()]['Category']}

    fig1 = make_subplots(specs=[[{"secondary_y": True}]])
    
    monthly_bar = px.bar(monthly_amount, x='Date', y='Count')
    monthly_bar.for_each_trace(lambda t: t.update(name = 'Count'))
    monthly_bar.update_traces(showlegend = True)
    
    monthly_line = px.line(monthly_amount, x='Date', y='Amount')
    monthly_line.for_each_trace(lambda t: t.update(name = 'Amount'))
    monthly_line.update_traces(yaxis='y2', line_color='red', line_width=10, showlegend = True)

    fig1.add_traces(monthly_line.data+monthly_bar.data)

    fig2 = px.pie(category_amount, values='Amount', names='Category', hover_data=['Count'], labels={'Count':'Count'})

    dash_app1.layout=dash.html.Div([
        dash.html.Div(className='row', style = {'display' : 'grid', 'grid-template-columns': '1fr 1fr'}, 
        children=[
            dcc.DatePickerRange(
            id='chosen-date-range',
            start_date=df_analysis["TransactDate"].min(),
            end_date=df_analysis["TransactDate"].max(),
            display_format='MMM/DD/YYYY',
            style = {'grid-column': '1', 'grid-row':'1'}
        ),
        dcc.Dropdown(
           options=[{'label': cat, 'value': cat} for cat in transaction_categories],
            id='chosen-category',
            multi=True,
            value=transaction_categories,
            style = {'grid-column': '2', 'grid-row':'1'}
        )]),
        dash.html.Button('Reset', id='btn-reset', n_clicks=0),
        dash.html.Br(),
        dash.html.Br(),
        dash.html.Div(className="p-3 mb-2 bg-info text-white",
        children=[
            dash.html.P('Total Expense: ', className="text-center font-weight-bold", style={'fontWeight': 'bold'}),
        ]),
        dash.html.P(total_amount, className="text-center font-weight-bold", style={'fontWeight': 'bold', 'font-size': '20px'}, id='total_expense'),

        dash.html.Div(className="p-3 mb-2 bg-info text-white",
        children=[
            dash.html.P('Expense by Month', className="text-center font-weight-bold", style={'fontWeight': 'bold'})
        ]),
        dash_table.DataTable(
        data=monthly_amount.to_dict('rows'), 
        columns=[           
        dict(id='Date', name='Date'),
        dict(id='Amount', name='Amount', type='numeric', format=FormatTemplate.money(2))
        ],        
        sort_action='native', 
        filter_action='native',
        style_cell={'textAlign':'left', 'font-size': '20px'},
        style_data={'color': 'black', 'backgroundColor': 'rgb(230, 247, 255)'},
        style_header={'backgroundColor': 'rgb(242, 242, 242)', 'color': 'black', 'fontWeight': 'bold'},
        style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(204, 239, 255)',}],
        id='monthly_expense_data'),
        dcc.Graph(figure=fig1, id='fig1'),
                
        dash.html.Div(className='row', style = {'display' : 'grid', 'grid-template-columns': '1fr 1fr 1fr'},
        children=[
        dash.html.Div(dash.html.Div(children=[
            dash.html.Div(className="p-3 mb-2 bg-info", children=[
                            dash.html.P('Average Monthly Expenditure: ', className="text-center text-white font-weight-bold", style={'fontWeight': 'bold'})]),
            dash.html.P(average_monthly, className="text-center font-weight-bold", style={'fontWeight': 'bold'}, id='average_expense')]), style = {'grid-column': '1', 'grid-row':'1'}),
        dash.html.Div(dash.html.Div(children=[
            dash.html.Div(className="p-3 mb-2 bg-info", children=[
                            dash.html.P('The Month with Highest Expenditure: ', className="text-center text-white font-weight-bold", style={'fontWeight': 'bold'})]),
            dash.html.P(max_monthly['Month'], className="text-center font-weight-bold", style={'fontWeight': 'bold', 'display':'inline-block'}, id='max_month'),
            dash.html.P(', which spend ', className="text-center font-weight-bold", style={'fontWeight': 'bold', 'display':'inline-block'}),
            dash.html.P(max_monthly['Amount'], className="text-center font-weight-bold", style={'fontWeight': 'bold', 'display':'inline-block', 'margin-left': '5px'}, id='max_month_amount')])
            ,style = {'grid-column': '2', 'grid-row':'1', 'text-align': 'center'}),
        dash.html.Div(dash.html.Div(children=[
            dash.html.Div(className="p-3 mb-2 bg-info", children=[
                            dash.html.P('The Month with Lowest Expenditure: ', className="text-center text-white font-weight-bold", style={'fontWeight': 'bold'})]),
            dash.html.P(min_monthly['Month'], className="text-center font-weight-bold", style={'fontWeight': 'bold', 'display':'inline-block'}, id='min_month'),
            dash.html.P(', which spend ', className="text-center font-weight-bold", style={'fontWeight': 'bold', 'display':'inline-block'}),
            dash.html.P(min_monthly['Amount'], className="text-center font-weight-bold", style={'fontWeight': 'bold', 'display':'inline-block', 'margin-left': '5px'}, id='min_month_amount')])
            ,style = {'grid-column': '3', 'grid-row':'1', 'text-align': 'center'})
        ]),
        dash.html.Br(),
        dash.html.Br(),
        
        dash.html.Div(className="p-3 mb-2 bg-info text-white",
        children=[
            dash.html.P('Expense by Category', className="text-center font-weight-bold", style={'fontWeight': 'bold'})
        ]),
        dash_table.DataTable(
        data=category_amount.to_dict('rows'), 
        columns=[           
        dict(id='Category', name='Category'),
        dict(id='Amount', name='Amount', type='numeric', format=FormatTemplate.money(2))
        ],
        sort_action='native', 
        filter_action='native',
        style_cell={'textAlign':'left', 'font-size': '20px'},
        style_data={'color': 'black', 'backgroundColor': 'rgb(230, 247, 255)'},
        style_header={'backgroundColor': 'rgb(242, 242, 242)', 'color': 'black', 'fontWeight': 'bold'},
        style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(204, 239, 255)',}],
        id='category_expense_data'
        ),
        dcc.Graph(figure=fig2, id='fig2'),
        dash.html.Div(dash.html.Div(children=[
            dash.html.Div(className="p-3 mb-2 bg-info", children=[dash.html.P('The Category with Highest Expenditure: ', className="text-center text-white font-weight-bold", style={'fontWeight': 'bold'})]),
        dash.html.P(max_category['Category'], className="text-center font-weight-bold", style={'fontWeight': 'bold', 'display':'inline-block'}, id='max_category'),
        dash.html.P(', which spend ', className="text-center font-weight-bold", style={'fontWeight': 'bold', 'display':'inline-block'}),
        dash.html.P(max_category['Amount'], className="text-center font-weight-bold", style={'fontWeight': 'bold', 'display':'inline-block', 'margin-left': '5px'}, id='max_category_amount')])
        , style={'text-align': 'center'}),
        dcc.Store(id='df_new')
    ])
    return render_template('analysis.html')

@dash_app1.callback([Output('df_new', 'data'), Output('chosen-date-range', 'start_date'), Output('chosen-date-range', 'end_date'), Output('chosen-category','value')],
    [Input('chosen-date-range', 'start_date'),
    Input('chosen-date-range', 'end_date'),
    Input('chosen-category','value'),
    Input('btn-reset', 'n_clicks')])
def update_analysis_data(start_date, end_date, search_value, btn):
    user_id=session["user_id"]
    sql="SELECT * FROM Transactions WHERE UserID = {}".format(user_id)
    df = pd.read_sql(sql , connection)

    if 'btn-reset' == ctx.triggered_id:
        org_start_date=pd.to_datetime(df["TransactDate"].min())
        org_end_date=pd.to_datetime(df["TransactDate"].max())
        df_new=df
        return json.dumps(df_new.to_json(orient='split', date_format='iso')), org_start_date, org_end_date, transaction_categories
    else:
        if not start_date and not end_date and not search_value:
            raise PreventUpdate
        elif search_value and start_date and end_date:
            start_date=date.fromisoformat(start_date)
            end_date=date.fromisoformat(end_date)
            df_new=df[(df['TransactDate']>=start_date)&(df['TransactDate']<=end_date)&(df['Category'].isin(search_value))]

            return json.dumps(df_new.to_json(orient='split', date_format='iso')), no_update, no_update, no_update
        else:
            raise PreventUpdate
            
@dash_app1.callback(Output('total_expense', 'children'), Output('monthly_expense_data', 'data'), Output('average_expense', 'children'), 
dict(x=Output('max_month', 'children'), y=Output('max_month_amount', 'children')), dict(x=Output('min_month', 'children'), y=Output('min_month_amount', 'children')), 
Output('category_expense_data', 'data'), dict(x=Output('max_category', 'children'), y=Output('max_category_amount', 'children')), Output('fig1', 'figure'), Output('fig2', 'figure'),
Input('df_new', 'data'))
def update_analysis_page(json_df_new):
    data=json.loads(json_df_new)
    df_new=pd.read_json(data, orient='split')

    df_new['date_formatted_monthly']=pd.to_datetime(df_new['TransactDate'], format = '%Y-%m-%d').dt.strftime("%Y-%m")
        
    total_expense='${:0,.2f}'.format(df_new['Amount'].sum())
       
    monthly_amount=df_new.groupby('date_formatted_monthly')['Amount'].aggregate(['count', 'sum']).reset_index()
    monthly_amount.columns=['Date', 'Count', 'Amount']

    fig1 = make_subplots(specs=[[{"secondary_y": True}]])
    
    monthly_bar = px.bar(monthly_amount, x='Date', y='Count')
    monthly_bar.for_each_trace(lambda t: t.update(name = 'Count'))
    monthly_bar.update_traces(showlegend = True)
    
    monthly_line = px.line(monthly_amount, x='Date', y='Amount')
    monthly_line.for_each_trace(lambda t: t.update(name = 'Amount'))
    monthly_line.update_traces(yaxis='y2', line_color='red', line_width=10, showlegend = True)

    fig1.add_traces(monthly_line.data+monthly_bar.data)

    max_month={'Amount':'${:0,.2f}'.format(monthly_amount['Amount'].max()), 'Month':monthly_amount[monthly_amount['Amount']==monthly_amount['Amount'].max()]['Date']}
    min_month={'Amount':'${:0,.2f}'.format(monthly_amount['Amount'].min()), 'Month':monthly_amount[monthly_amount['Amount']==monthly_amount['Amount'].min()]['Date']}

    average_expense='${:0,.2f}'.format(monthly_amount['Amount'].mean())

    category_amount=df_new.groupby('Category')['Amount'].aggregate(['count', 'sum']).reset_index()
    category_amount.columns=['Category', 'Count', 'Amount']
        
    fig2 = px.pie(category_amount, values='Amount', names='Category', hover_data=['Count'], labels={'Count':'Count'})

    max_category={'Amount':'${:0,.2f}'.format(category_amount['Amount'].max()), 'Category':category_amount[category_amount['Amount']==category_amount['Amount'].max()]['Category']}

    return total_expense, monthly_amount.to_dict('rows'), average_expense, dict(x=max_month['Month'], y=max_month['Amount']), dict(x=min_month['Month'], y=min_month['Amount']), category_amount.to_dict('rows'), dict(x=max_category['Category'], y=max_category['Amount']), fig1, fig2


geo_location=['Canada', 'Alberta', 'British Columbia', 'Manitoba', 'New Brunswick', 'Newfoundland and Labrador', 'Nova Scotia', 'Ontario', 'Prince Edward Island', 'Quebec', 'Saskatchewan',
 'Yellowknife, Northwest Territories', 'Iqaluit, Nunavut', 'Whitehorse, Yukon']

product_category=['All-items', 'Food', 'Shelter', 'Household operations, furnishings and equipment', 'Clothing and footwear', 'Clothing', 'Transportation', 'Gasoline', 'Health and personal care',
 'Recreation, education and reading', 'Alcoholic beverages, tobacco products and recreational cannabis', 'Energy', 'Services']

model=load_model('model.hdf5')

@app.route('/projection', methods=['GET', 'POST'])
def projection():
    user_id=session["user_id"]

    df=stats_can.sc.table_to_df('18-10-0004-01')
    df=df[(df['UOM']=='2002=100')]
    df=df.iloc[:,[0,1,3,4,10]]
    df['REF_DATE']=pd.to_datetime(df['REF_DATE'], format = '%Y-%m-%d').dt.strftime("%Y-%m-%d")

    df_table=df[(df['REF_DATE']>='2022-01-01')&(df['REF_DATE']<='2023-01-01')&(df['GEO']=='Canada') & (df['Products and product groups']=='All-items')]

    df_for_prediction=df[(df['GEO']=='Canada') & (df['Products and product groups']=='All-items')]
    value=df_for_prediction['VALUE'].values.astype('float64')
    num_month_prediction=24
    n_for_predict=3
    predict_period_dates = pd.date_range(start='2023-02-01', periods=num_month_prediction, freq='MS').strftime("%Y-%m-%d")
    prediction_list = value[-n_for_predict:]
    for _ in range(num_month_prediction):
        x = prediction_list[-n_for_predict:]
        x = x.reshape((1, 1, n_for_predict))
        pred = model.predict(x)[0][0]
        prediction_list = np.append(prediction_list, pred)
    prediction_list=prediction_list[n_for_predict:]
    pred_result=pd.DataFrame(zip(predict_period_dates, prediction_list), columns=['REF_DATE', 'VALUE'])

    df_table1=df[(df['GEO']=='Canada') & (df['Products and product groups']=='All-items')]
    df_table1['Status']='Current CPI'
    pred_result['Status']='Project CPI'

    df_graph=df_table1.append(pred_result, ignore_index = True)
    line_chart=px.line(df_graph, x='REF_DATE', y='VALUE', color='Status', labels={"REF_DATE": "Month", "VALUE": "CPI Level"})

    dash_app2.layout=dash.html.Div([
        dash.html.Div(className='row', style = {'display' : 'grid', 'grid-template-columns': '1fr 1fr 1fr'}, 
        children=[
        dcc.DatePickerRange(
            id='chosen-date-range',
            start_date=pd.to_datetime('2022-01-01'),
            end_date=pd.to_datetime('2023-01-01'),
            display_format='MMM/DD/YYYY',
            style = {'grid-column': '1', 'grid-row':'1'}
        ),
        dcc.Dropdown(
           options=[{'label': geo, 'value': geo} for geo in geo_location],
            id='chosen-location',
            value='Canada',
            style = {'grid-column': '2', 'grid-row':'1'}
        ),
        dcc.Dropdown(
           options=[{'label': product, 'value': product} for product in product_category],
            id='chosen-product',
            value='All-items',
            style = {'grid-column': '3', 'grid-row':'1'}
        ),
        ]),
        dash.html.Button('Reset', id='btn-reset', n_clicks=0),
        dash.html.Br(),
        dash.html.Br(),
        dash.html.Div(className="p-3 mb-2 bg-info text-white",
        children=[
            dash.html.P('CPI DATA', className="text-center font-weight-bold", style={'fontWeight': 'bold'}),  
        ]),
        dash_table.DataTable(
        data=df_table.to_dict('rows'), 
        columns=[           
        dict(id='REF_DATE', name='Month'),
        dict(id='VALUE', name='Price Level', type='numeric', format=Format())
        ],        
        sort_action='native', 
        filter_action='native',
        style_cell={'textAlign':'left', 'font-size': '20px'},
        style_data={'color': 'black', 'backgroundColor': 'rgb(230, 247, 255)'},
        style_header={'backgroundColor': 'rgb(242, 242, 242)', 'color': 'black', 'fontWeight': 'bold'},
        style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(204, 239, 255)',}],
        id='CPI_dataframe'),
        dcc.Graph(figure=line_chart, id='line_chart'),
        dash.html.Br(),
        dash.html.Div(className="p-3 mb-2 bg-info text-white",
        children=[
            dash.html.P('Projection', className="text-center font-weight-bold", style={'fontWeight': 'bold'}),  
        ]),
        dash_table.DataTable(
        data=pred_result.to_dict('rows'), 
        columns=[           
        dict(id='REF_DATE', name='Month'),
        dict(id='VALUE', name='Prediction', type='numeric', format=Format(precision=2, scheme=Scheme.fixed))
        ],        
        sort_action='native', 
        filter_action='native',
        style_cell={'textAlign':'left', 'font-size': '20px'},
        style_data={'color': 'black', 'backgroundColor': 'rgb(230, 247, 255)'},
        style_header={'backgroundColor': 'rgb(242, 242, 242)', 'color': 'black', 'fontWeight': 'bold'},
        style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(204, 239, 255)',}],
        id='Prediction_dataframe'),
        dcc.Store(id='df_new'),
        dcc.Store(id='df_new1')
    ])
    return render_template('projection.html')

@dash_app2.callback([Output('df_new', 'data'), Output('df_new1', 'data'), Output('chosen-date-range', 'start_date'), Output('chosen-date-range', 'end_date'), Output('chosen-location','value'), Output('chosen-product','value')],
    [Input('chosen-date-range', 'start_date'),
    Input('chosen-date-range', 'end_date'),
    Input('chosen-location','value'),
    Input('chosen-product','value'),
    Input('btn-reset', 'n_clicks')])
def update_project_data(start_date, end_date, location, product, btn):
    user_id=session["user_id"]
    df=stats_can.sc.table_to_df('18-10-0004-01')
    df=df[(df['UOM']=='2002=100')]
    df=df.iloc[:,[0,1,3,4,10]]
    df['REF_DATE']=pd.to_datetime(df['REF_DATE'], format = '%Y-%m-%d').dt.strftime("%Y-%m-%d")

    if 'btn-reset' == ctx.triggered_id:
        df_table=df[(df['REF_DATE']>='2022-01-01')&(df['REF_DATE']<='2023-01-01')&(df['GEO']=='Canada') & (df['Products and product groups']=='All-items')]
        df_table1=df[(df['REF_DATE']<='2023-01-01')&(df['GEO']=='Canada') & (df['Products and product groups']=='All-items')]
        org_start_date=pd.to_datetime(df_table["REF_DATE"].min())
        org_end_date=pd.to_datetime(df_table["REF_DATE"].max())
        return json.dumps(df_table.to_json(orient='split', date_format='iso')), json.dumps(df_table1.to_json(orient='split', date_format='iso')), org_start_date, org_end_date, 'Canada', 'All-items'
    else:
        if not start_date and not end_date and not location and not product:
            raise PreventUpdate
        elif location and product and start_date and end_date:
            df_table=df[(df['REF_DATE']>=start_date)&(df['REF_DATE']<=end_date)&(df['GEO']==location)&(df['Products and product groups']==product)]
            df_table1=df[(df['REF_DATE']<='2023-01-01')&(df['GEO']==location)&(df['Products and product groups']==product)]
            return json.dumps(df_table.to_json(orient='split', date_format='iso')), json.dumps(df_table1.to_json(orient='split', date_format='iso')), no_update, no_update, no_update, no_update
        else:
            raise PreventUpdate

@dash_app2.callback([Output('CPI_dataframe', 'data'), Output('Prediction_dataframe','data'), Output('line_chart', 'figure')],
                     [Input('df_new', 'data'), Input('df_new1', 'data')])
def update_projection_page(json_df_new, json_df_new1):
    data=json.loads(json_df_new)
    df_new=pd.read_json(data, orient='split')

    df_new['REF_DATE']=pd.to_datetime(df_new['REF_DATE'], format = '%Y-%m-%d').dt.strftime("%Y-%m-%d")

    data1=json.loads(json_df_new1)
    df_for_prediction=pd.read_json(data1, orient='split')
    value=df_for_prediction['VALUE'].values.astype('float64')
    num_month_prediction=24
    n_for_predict=3
    predict_period_dates = pd.date_range(start='2023-02-01', periods=num_month_prediction, freq='MS').strftime("%Y-%m-%d")
    prediction_list = value[-n_for_predict:]
    for _ in range(num_month_prediction):
        x = prediction_list[-n_for_predict:]
        x = x.reshape((1, 1, n_for_predict))
        pred = model.predict(x)[0][0]
        prediction_list = np.append(prediction_list, pred)
    prediction_list=prediction_list[n_for_predict:]
    pred_result=pd.DataFrame(zip(predict_period_dates, prediction_list), columns=['REF_DATE', 'VALUE'])

    df_for_prediction['Status']='Current CPI'
    pred_result['Status']='Project CPI'

    df_graph=df_for_prediction.append(pred_result, ignore_index = True)
    line_chart=px.line(df_graph, x='REF_DATE', y='VALUE', color='Status', labels={"REF_DATE": "Month", "VALUE": "CPI Level"})
        
    return df_new.to_dict('rows'), pred_result.to_dict('rows'), line_chart

@app.route('/dash1/', methods=['GET', 'POST'])
def dash1():
    return dash_app1.index()

@app.route('/dash2/', methods=['GET', 'POST'])
def dash2():
    return dash_app2.index()

if __name__ == '__main__':
   app.debug=True   
   app.run()
