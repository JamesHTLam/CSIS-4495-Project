# Flask-Spending-Record-WebApp
## This is a web application that allow user to register and login to their account, and add expenditure record to it. Users can also see data visualization result generated from their expenditure records in the web application.  

## 1. Image of the WebApp
### 1.1. Account Creation
![image](https://github.com/JamesHTLam/Flask-Spending-Record-WebApp/assets/98861373/bebf7d13-65f7-4c27-97fc-e136b4fc93e1)
### 1.2. Account Login
![image](https://github.com/JamesHTLam/Flask-Spending-Record-WebApp/assets/98861373/25a4c9dc-7a95-4c90-a07a-f21510279c57)
### 1.3. Home Page to perform CRUD opertion
![image](https://github.com/JamesHTLam/Flask-Spending-Record-WebApp/assets/98861373/c37c238a-6b95-455f-b239-187c4e710842)
### 1.4. Data visualization
![image](https://github.com/JamesHTLam/Flask-Spending-Record-WebApp/assets/98861373/28575ba7-5a9b-4ca8-b557-50513ab2bd38)


## 2. Setup of the WebApp
### 2.1. Download and open the project folder in VS Code
![image](https://github.com/JamesHTLam/Flask-Spending-Record-WebApp/assets/98861373/fae7c30a-c5ed-4a94-8c05-b015c80ca8fe)
- app.py is the main Flask program to be run
- requirements.txt contains all the dependencies required by this program
- templates folder contains html webpages to be loaded by the Flask program
- static folder contains temporary files to be used by the main program
- The jupyter source file is how the LSTM model for inflation projection is trained, model.hdf5 is the trained model file
### 2.2. Create a Virtual Environment
- In VS Code, select “View”->”Command Palette”, then search and select “Python: Create Environment”. Choose the first option to create a `.venv` virtual environment
![image](https://github.com/JamesHTLam/Flask-Spending-Record-WebApp/assets/98861373/9607a929-0796-4001-990e-6d8d19f47951)
- After that, choose the suitable Python Interpreter (recommend to be at least Python 3.10)
![image](https://github.com/JamesHTLam/Flask-Spending-Record-WebApp/assets/98861373/82b656a4-ef3d-43ee-b9fb-3c1a97aed317)
- Python will start creating the virtual environment and install required dependencies listed in requirements.txt (it would take a while as number of dependencies is large; if dependencies are not loaded automatically, run “python -m pip install -r requirements.txt” in the integrated terminal after the virtual environment is created and activated)
![image](https://github.com/JamesHTLam/Flask-Spending-Record-WebApp/assets/98861373/b79397bd-37f5-410d-bf76-f451f6b69ed3)
- After the virtual environment is created, start a new terminal. It will automatically activate the `.venv` virtual environment:
![image](https://github.com/JamesHTLam/Flask-Spending-Record-WebApp/assets/98861373/c713fcc0-405a-4aa3-b408-e0d56eca74be)

### 2.3. After the above steps, the setup of the application is finished in this local machine. Only 2 steps are needed every time to launch the application.
- Launch Apache and MySQL in XAMPP
![image](https://github.com/JamesHTLam/Flask-Spending-Record-WebApp/assets/98861373/f0865dd2-f83a-4fee-b70e-bd3138e6a6bd)
- Run the program
In the integrated terminal of VS Studio Code, type “python -m flask run” in the terminal:
![image](https://github.com/JamesHTLam/Flask-Spending-Record-WebApp/assets/98861373/3b05e064-1b90-43b9-861e-e3d91b489412)

Finally, just click on the link in the terminal to access the program.
