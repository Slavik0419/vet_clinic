from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Ініціалізація бази даних
def init_db():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Таблиця користувачів
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    
    # Таблиця записів
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            entered_username TEXT,
            pet_name TEXT NOT NULL,
            doctor TEXT NOT NULL,
            date TEXT NOT NULL,
            status TEXT DEFAULT "Pending",
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    username = session.get('username')  # Отримуємо ім'я користувача з сесії
    return render_template('index.html', username=username)

# Реєстрація користувачів
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
            flash('Реєстрація успішна! Увійдіть у свій акаунт.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Ім’я користувача вже існує.')
        conn.close()
    return render_template('register.html')

# Вхід користувачів
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash('Вхід успішний!')
            return redirect(url_for('index'))
        else:
            flash('Неправильне ім’я користувача або пароль.')
    return render_template('login.html')

# Вихід користувачів
@app.route('/logout')
def logout():
    session.clear()
    flash('Ви вийшли з акаунту.')
    return redirect(url_for('index'))

# Запис на прийом
@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if 'user_id' not in session:
        flash('Будь ласка, увійдіть для запису на прийом.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        entered_username = request.form['username']  # Отримуємо ім'я, яке вводить користувач
        pet_name = request.form['pet_name']
        doctor = request.form['doctor']
        date = request.form['date']
        user_id = session['user_id']

        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO appointments (user_id, entered_username, pet_name, doctor, date)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, entered_username, pet_name, doctor, date))
        conn.commit()
        conn.close()
        flash('Запис успішно створено!')
        return redirect(url_for('history'))

    return render_template('booking.html')


# Історія записів
@app.route('/history')
def history():
    if 'user_id' not in session:
        flash('Будь ласка, увійдіть для перегляду історії.')
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    # Запит з урахуванням `entered_username`
    cursor.execute('''
        SELECT a.entered_username, a.pet_name, a.doctor, a.date, a.status
        FROM appointments a
        WHERE a.user_id = ?
    ''', (user_id,))
    appointments = cursor.fetchall()
    conn.close()

    return render_template('history.html', appointments=appointments)



@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/news')
def news():
    return render_template('news.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
