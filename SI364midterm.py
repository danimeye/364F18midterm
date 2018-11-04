###############################
####### SETUP (OVERALL) #######
###############################

## Import statements
# Import statements
import os
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, ValidationError # Note that you may need to import more here! Check out examples that do what you want to figure out what.
from wtforms.validators import Required # Here, too
from flask_sqlalchemy import SQLAlchemy
import requests
import json
import random
import hashlib 
import calendar
import time

## App setup code
app = Flask(__name__)
app.debug = True

## All app.config values
app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string from si364'
## TODO 364: Create a database in postgresql in the code line below, and fill in your app's database URI. It should be of the format: postgresql://localhost/YOUR_DATABASE_NAME

## Your final Postgres database should be your uniqname, plus HW3, e.g. "jczettaHW3" or "maupandeHW3"
app.config["SQLALCHEMY_DATABASE_URI"] = "postgres://daniellemeyerson@localhost:5432/danimeye_midterm"
## Provided:
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

## Statements for db setup (and manager setup if using Manager)
db = SQLAlchemy(app)


######################################
######## HELPER FXNS (If any) ########
######################################




##################
##### MODELS #####
##################

class Character(db.Model): # Characters Table (the 'one')
    __tablename__ = "characters"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.String(500))
    char_api_id = db.Column(db.Integer)
    comics = db.relationship("Comic", backref = "Character") # establishes the one-to-many relationship with Comic

    def __repr__(self):
        return "{}: {}".format(self.name, self.description)

class Comic(db.Model): # Comics Table (the 'many')
    __tablename__ = "comics"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(100))
    # char_api_id
    char_id = db.Column(db.Integer, db.ForeignKey('characters.id')) # creates foreign key with character id 

    def __repr__(self):
        return "{}".format(self.name)

###################
###### FORMS ######
###################

class MarvelForm(FlaskForm):
    name = StringField("Please enter a Marvel character.",validators=[Required()])
    submit = SubmitField("Submit")

    def validate_name(self, field):
        name_len = len(field.data)
        if name_len > 20:
            raise ValidationError("This name is longer than 20 characters. Please enter a different name.")

class MarvelForm2(FlaskForm):
    comic_keyword = StringField("Enter a keyword to search for comics.")
    submit = SubmitField("Submit")
## Error handling routes - PROVIDED
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

#######################
###### VIEW FXNS ######
#######################

@app.route('/', methods=['GET', 'POST'])
def home():
    form = MarvelForm() # User should be able to enter name after name and each one will be saved, even if it's a duplicate! Sends data with GET
    if form.validate_on_submit():
        name = form.name.data

        entered_character = Character.query.filter_by(name = name).first()
        if not entered_character: #if a character hasn't been inputted, make a call to the API
            ts = str(calendar.timegm(time.gmtime()))
            priv_key = '357ac06e58c9b720d295a5c3623180a643a11eba'
            pub_key = '57cf9e503f7a88616af606035c5460dd'
            hash_string = ts + priv_key + pub_key
            m = hashlib.md5(hash_string.encode())
            api_hash = m.hexdigest()
            # api_hash = hash(priv_key+pub_key+ts)
            params_diction = {}
            params_diction['name'] = name 
            params_diction['ts'] = ts
            params_diction['apikey'] = pub_key
            params_diction['hash'] = api_hash
            print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            # print(params_diction)
            # params_diction['ts'] = ts
            base_url = "https://gateway.marvel.com/v1/public/characters"
            resp = requests.get(base_url, params = params_diction)
            text = resp.text
            # print(text)
            python_obj = json.loads(text)
            #print(python_obj)
            char_api_id = python_obj["data"]["results"][0]["id"]
            description = python_obj["data"]["results"][0]["description"]
            # print(char_api_id)
            # print(description)
            new_character = Character(name = name, description = description, char_api_id = char_api_id)
            db.session.add(new_character)
            db.session.commit()

            comic_list = []
            for comic in python_obj["data"]["results"][0]["comics"]["items"]:
                comic_list.append(comic["name"])
            print(comic_list)
            for comic in comic_list:
                new_comic = Comic(name = comic, char_id = new_character.id)
                db.session.add(new_comic)
                db.session.commit()
            return redirect(url_for('all_characters'))
        else: 
            flash('You have already searched for this Marvel chracter.')
            return redirect(url_for('home'))

    form2 = MarvelForm2(request.args)
    keyword_results = []
    keyword = None
    if form2.validate():
        keyword = form2.comic_keyword.data
        all_comics = Comic.query.all()
        for comic in all_comics:
            if keyword in comic.name:
                keyword_results.append(comic)
        if len(keyword_results) == 0 :
            flash("No comics found that match that keyword.")
    return render_template('home.html', form = form, form2 = form2, results = keyword_results, keyword = keyword)



    #     name = form.name.data
    #     newname = Name(name)
    #     db.session.add(newname)
    #     db.session.commit()
    #     return redirect(url_for('all_names'))
    # return render_template('base.html',form=form)

@app.route('/characters') # returns all searched for characters
def all_characters():
    form = MarvelForm()
    characters = Character.query.all()
    print(characters)
    return render_template('all_characters.html', form = form, all_characters = characters)

@app.route('/comics') # returns all comics categorized by character 
def all_comics():
    form = MarvelForm()
    comics = Comic.query.all()
    comic_dict = {}
    #characters = Character.query.all()
    for character in Character.query.all():
        current_id = character.id
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        print(current_id)
        comic_by_character_id = Comic.query.filter_by(char_id = current_id).all() # a list of all comics filtered by id 
        print(comic_by_character_id)
        comic_list = []
        for comic in comic_by_character_id:
            comic_list.append(comic)
        print(comic_list)
        comic_dict[character.name] = comic_list 
    print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
    print(comic_dict)
    return render_template('all_comics.html', form = form, comic_dict = comic_dict)












## Code to run the application...
if __name__ == '__main__':
    db.create_all() # Will create any defined models when you run the application
    app.run(use_reloader=True,debug=True) # The usual

# Put the code to do so here!
# NOTE: Make sure you include the code you need to initialize the database structure when you run the application!
