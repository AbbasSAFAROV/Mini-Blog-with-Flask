from flask import Flask
from flask import redirect , render_template
from flask import request, url_for
from flask import flash , session , logging 
from flask_mysqldb import MySQL
from wtforms import Form , StringField , TextAreaField , PasswordField , validators
from passlib.hash import sha256_crypt
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("bu sayfayı görüntülemek için lütfen giriş yapınız ." , "danger")
            return redirect(url_for("login"))
    
    return decorated_function

class RegisterForm(Form):
    name  = StringField("Isim SoyIsim : ", validators=[validators.length(min=5 , max=25)])
    username  = StringField("Kullanici Adi : ", validators=[validators.length(min=5 , max=25)])
    email  = StringField("E-mail Adressi : " , validators=[validators.length(min=5 , max=25)])
    password  = PasswordField("Parola : ", validators=[
                            validators.DataRequired(message="lutfen bir parola belirleyin . . .") ,
                            validators.EqualTo(fieldname="confirm",message="Parolaniz Uyusmuyor . . .")])
    confirm = PasswordField("Parola Dogrula : ")

class LoginForm(Form):
    username = StringField("User Name : ")
    password = PasswordField("Password : ")

class AddArticle(Form):
    title  = StringField("Başlık Giriniz : ", validators=[validators.length(min=5)])
    created_date  = StringField("Oluşturma Tarihi Giriniz : ")
    content  = TextAreaField("İçeriği Giriniz : ", validators=[validators.length(min=10)])
    

app = Flask(__name__)

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "toor"
app.config["MYSQL_DB"] = "mywebpage"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)



@app.route("/")
def index():
    return render_template("index.html")

@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/register" , methods = ["GET", "POST"])
def register():

    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():

        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = form.password.data

        mycursor = mysql.connection.cursor()

        sorgu = "insert into users (name,email,username,password) values (%s,%s,%s,%s)" 

        mycursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()

        mycursor.close()

        flash("Başarıyla Kayıt Oldunuz . . .", "success")
        return redirect(url_for("login"))
    else :
        return render_template("register.html" , form = form)

@app.route("/login", methods = ["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()
        sorgu = "select * from users where username = %s"

        result = cursor.execute(sorgu,(username,))
        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if real_password == password_entered:
                flash("Başarıyla Giriş Yaptınız . . .", "success")

                session["logged_in"] = True
                session["username"] = username

                return redirect(url_for("home"))
            else:
                flash("Parola yanlış girdiniz . . ." , "danger")
                return redirect(url_for("login"))
        
        else:
            flash("Böyle bir kullanıcı bulunmuyor . . .","danger")
            return redirect(url_for("login"))
    else:
        return render_template("login.html",form = form)

@app.route("/logout")
def signout():
    session.clear()
    flash("başarıyla çıkış yapıldı . . .", "success")
    return redirect(url_for("home"))

@app.route("/article")
def article():

    cursor = mysql.connection.cursor()

    sorgu = "select * from articales"
    result = cursor.execute(sorgu)

    if result>0:
        articles = cursor.fetchall()

        return render_template("article.html" , articles = articles)
    else:
        return render_template("article.html")

@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()

    sorgu = "select * from articales where author = %s"

    result = cursor.execute(sorgu,(session["username"],))

    if result > 0:
        articles = cursor.fetchall()
        
        return render_template("dashboard.html",articles = articles)
    
    else:

        return render_template("dashboard.html")

@app.route("/addarticle" , methods = ["GET","POST"])
def addarticle():

    form = AddArticle(request.form)

    if request.method == "POST":

        title = form.title.data
        content = form.content.data
        created_date = form.created_date.data

        cursor = mysql.connection.cursor()
        sorgu = "insert into articales (title,content,author,created_date) values (%s,%s,%s,%s)"

        cursor.execute(sorgu,(title,content,session["username"],created_date))

        mysql.connection.commit()
        cursor.close()

        flash("başarıyla eklendi .","success")
        return redirect(url_for("dashboard"))

    return render_template("addarticle.html" , form = form)
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()

    sorgu = "select * from articales where author = %s and id = %s"

    result = cursor.execute(sorgu,(session["username"],id))

    if result > 0:
        sorgu2 = "delete from articales where id = %s"
        cursor.execute(sorgu2,(id,))

        mysql.connection.commit()

        return redirect(url_for("dashboard"))
    else:
        flash("böyle bir makale yok ve işleme yetkiniz yok " , "danger")
        return redirect(url_for("login"))

@app.route("/update/<string:id>" , methods = ["GET","POST"])
@login_required
def update(id):
    if request.method ==  "GET":
        cursor = mysql.connection.cursor()

        sorgu = "select * from articales where id = %s and author = %s"
        result = cursor.execute(sorgu,(id,session["username"]))

        if result == 0:
            flash("böyle bir makale yok veya böyle bir yetkiniz yok .", "danger")
            return redirect(url_for("login"))
        else:
            article = cursor.fetchone()
            form = AddArticle()

            form.title.data = article["title"]
            form.content.data = article["content"]
            form.created_date.data = article["created_date"]

            return render_template("/update.html",form = form)

    else:
        form = AddArticle(request.form)

        newTitle = form.title.data
        newContent = form.content.data
        newCreated_date = form.created_date.data

        sorgu2 = "update articales set title = %s , content = %s , created_date = %s where id = %s"
        cursor = mysql.connection.cursor()

        cursor.execute(sorgu2,(newTitle,newContent,newCreated_date,id))

        mysql.connection.commit()
        flash("makale başarıyla güncellendi .","success")

        return redirect(url_for("dashboard"))






if __name__=="__main__":
    app.run(debug=True)