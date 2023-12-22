from flask import Flask, flash, render_template, g, request, redirect, url_for,  make_response
from html import escape
from flask_wtf.csrf import CSRFError
from flask_wtf import csrf
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from email.message import EmailMessage
import logging, psycopg2, smtplib, ssl

app = Flask(__name__)
app.config['SECRET_KEY'] = '1234'
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

@app.route("/")
def home():

    try:
        connection = create_connection()
        cursor = connection.cursor()

        query = "SELECT * FROM credenciais;"
        cursor.execute(query)
        data = cursor.fetchall()

        connection.close()

        return render_template('index.html', data=data)
    
    except Exception as e:
        print(f"Error in fetching data: {e}")

        return "Error in fetching data"

@app.route("/part1.html")
def login():
    return render_template("part1.html")

# FUNCTION TO CHECK IF USER EXIST IN DATABASE
def check_user_exists(username, password):
    connection = create_connection()
    cursor = connection.cursor()

    try:
        # CHECK CREDENTIALS IN DATABASE
        query = f"SELECT * FROM credenciais WHERE username = '{username}' AND password = '{password}';"
        cursor.execute(query)

        # SAVE DATA
        result = cursor.fetchall()

        return bool(result)

    except Exception as e:
        print(f"Erro ao verificar usuário: {e}")
        raise

    finally:
        connection.close()

@app.route("/part1_vulnerable", methods=['POST'])
def part1_vulnerable():
    connection = create_connection()
    cursor = connection.cursor()

    password = request.form['v_password']
    username = request.form['v_username']

    try:
        # CHECK IF DATA EXIST IN DATABASE
        credentials_exist = check_user_exists(username, password)

        if credentials_exist:
            # VALID MESSAGE
            success_message = "Login valid!"
        else:
            # ERROR MESSAGE
            success_message = "Login invalid, try again"

    except Exception as e:
        print(f"Erro ao verificar credenciais: {e}")
        connection.rollback()  # Desfazer alterações se ocorrer um erro
        success_message = "Erro ao verificar credenciais"

    return render_template("part1.html", success_message=success_message)
    


@app.route("/part1_correct", methods=['POST'])
def part1_correct():
    success_message = ""
    connection = create_connection()
    cursor = connection.cursor()

    try:
        # GET USERNAME AND PASSWORD
        username = request.form['c_username']
        password = request.form['c_password']

        # VALIDAÇÃO: CHECK IF DATA IS NOT EMPTY
        if not username or not password:
            flash("Username and password are required.", 'error')
            return redirect(url_for('login'))

        # VALIDATION
        query = "SELECT * FROM credenciais WHERE username = %s AND password = %s;"
        cursor.execute(query, (username, password))
        user_data = cursor.fetchone()

        if user_data and check_user_exists(username, password):
            # Gerar e enviar e-mail de confirmação
            user_email = user_data[2]

            if user_email:
                # Gerar token de confirmação
                token = serializer.dumps(user_email, salt='email-confirm')

                # Construir URL de confirmação
                confirmation_url = url_for('confirm_email', token=token, _external=True)

                # Enviar e-mail de confirmação
                send_email(user_email, confirmation_url)

                # VALID MESSAGE
                success_message = "Login valid! Check your email for confirmation."
            else:
                # ERROR MESSAGE
                success_message = "Login invalid, try again!"
                flash("Invalid username or password.", 'error')

    except CSRFError as e:
        print(f"CSRF error: {e}")
        connection.rollback()  # Desfazer alterações se ocorrer um erro
        success_message = "CSRF error"

    except Exception as e:
        print(f"Checking credential error: {e}")
        connection.rollback()  # Desfazer alterações se ocorrer um erro
        success_message = "Login invalid, try again"

    finally:
        connection.close()

    csrf_token = csrf.generate_csrf()
    return render_template("part1.html", success_message=success_message, csrf_token=csrf_token)


@app.route('/confirm_email/<token>')
def confirm_email(token):
    try:
        user_email = serializer.loads(token, salt='email-confirm', max_age=3600)  # Token valid for 1 hour
        # Perform any additional actions here, e.g., update user status in the database


        return render_template('email_sent.html', user_email=user_email)
    except Exception as e:
        return 'Invalid or expired token. Please try again.'


#21 de Dezembro
def send_email(user_email, confirmation_url):
    em = EmailMessage()
    em['From'] = 'projetocdss12@gmail.com'
    em['To'] = user_email
    em['Subject'] = 'Hello New User'
    em.set_content(f"Hello User, please confirm your email by clicking on the following link: {confirmation_url}")

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login('projetocdss12@gmail.com', 'mtbm dlmi fwgt ddrw')
        smtp.sendmail('projetocdss12@gmail.com', user_email, em.as_string())


@app.route("/part2.html", methods=['GET'])
def part2():

    return render_template("part2.html");


@app.route("/part2_vulnerable", methods=['GET', 'POST'])
def part2_vulnerable():
    
    return "/part2_vulnerable"


@app.route("/part2_correct", methods=['GET', 'POST'])
def part2_correct():

    return "/part2_correct"


@app.route("/part3.html", methods=['GET'])
def part3():

    return render_template("part3.html");


@app.route("/part3_vulnerable", methods=['GET', 'POST'])
def part3_vulnerable():
    
    return "/part3_vulnerable"


@app.route("/part3_correct", methods=['GET', 'POST'])
def part3_correct(): 

    return "/part3_correct"


@app.route("/demo", methods=['GET', 'POST'])
def demo():
    logger.info("\n DEMO \n");   

    conn = get_db()
    cur = conn.cursor()

    logger.info("---- users  ----")
    cur.execute("SELECT * FROM users")
    rows = cur.fetchall()

    for row in rows:
        logger.info(row)

    for row in rows:
        logger.info(row)

    logger.info("---- messages ----")
    cur.execute("SELECT * FROM messages")
    rows = cur.fetchall()
 
    for row in rows:
        logger.info(row)

    logger.info("---- books ----")
    cur.execute("SELECT * FROM books")
    rows = cur.fetchall()
 
    for row in rows:
        logger.info(row)

    conn.close ()
    logger.info("\n---------------------\n\n") 

    return "/demo"


##########################################################
## DATABASE ACCESS
##########################################################
# PostgreSQL database configuration
db_config = {
    'host': 'localhost',
    'dbname': 'ddss-database-assignment-2',
    'user': 'postgres',
    'password': 'postgres',
}

# FUNCTION TO CREATE A CONNECTION WITH DATABASE
def create_connection():
    try:
        connection = psycopg2.connect(**db_config)
        return connection
    except psycopg2.OperationalError as e:
        print(f"Error connecting to the database: {e}")
        raise  # re-raise the exception to terminate the program


##########################################################
## ORIGINAL FUNCTION
##########################################################
def get_db():
    db = psycopg2.connect(user = "postgres",
                password = "postgres",
                host = "postgres",
                port = "5432",
                database = "ddss-database-assignment-2")
    return db


##########################################################
## MAIN
##########################################################
if __name__ == "__main__":
    #logging.basicConfig(filename="log_file.log")

    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s:  %(message)s')

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)

    logger.info("\n---------------------\n\n")

    app.run(host="0.0.0.0", debug=True, threaded=True)
    
