from flask import Flask, flash, render_template, request
from wtforms import Form, StringField, SubmitField, TextAreaField, TextField, validators
from wtforms.validators import URL, DataRequired, Email, EqualTo, Length

# App config.
DEBUG = True
app = Flask(__name__)
app.config.from_object(__name__)
app.config["SECRET_KEY"] = "7d441f27d441f27567d441f2b6176a"


class ReusableForm(Form):
    name = StringField("Name:", validators=[validators.required()])
    email = StringField("Email:", validators=[validators.required(), validators.Length(min=6, max=35)])

    password = StringField("Password:", validators=[validators.required(), validators.Length(min=3, max=35)])

    @app.route("/", methods=["GET", "POST"])
    def hello():
        form = ReusableForm(request.form)

        print(form.errors)
        if request.method == "POST":
            name = request.form["name"]
            password = request.form["password"]
            email = request.form["email"]
            print(name + " " + email + " " + password)

        if form.validate():
            # Save the comment here.
            flash("Thanks for registration " + name)
        else:
            flash("Error: All the form fields are required. ")

        return render_template("hello.html", form=form)


if __name__ == "__main__":
    app.run()

    # next tutorial: https://hackersandslackers.com/flask-wtforms-forms/
