from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

#now connect to the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/Shawn/application/stats.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable tracking to save resources

# Initialize the SQLAlchemy extension
db = SQLAlchemy(app)
db.metadata.clear()
class Runners(db.Model):
    __tablename__ = "top_running_backs"
    player = db.Column(db.String(20), primary_key=True)
    team = db.Column(db.String(100), nullable=False)
    fantpos = db.Column(db.String(5), nullable=False)
    rushing_yards_23 = db.Column(db.String(20), nullable=False)
    rushing_tds_22 = db.Column(db.String(10), nullable=False)
    rushing_yards_23 = db.Column(db.String(20), nullable=False)
    rushing_tds_22 = db.Column(db.String(10), nullable=False)
    rushing_yards_21 = db.Column(db.String(20), nullable=False)
    rushing_tds_21 = db.Column(db.String(10), nullable=False)

# class Item(db.Model):
#     __tablename__ = "fantasy_football_stats_2024"
#     player = db.Column(db.String(20), primary_key=True)
#     team = db.Column(db.String(100), nullable=False)
#     fantpos = db.Column(db.String(5), nullable=False)
#     age = db.Column(db.String(5), nullable=False)
#     games = db.Column(db.String(5), nullable=False)
#     games_started = db.Column(db.String(5), nullable=False)
#     completions = db.Column(db.String(20), nullable=False)
#     passing_att = db.Column(db.String(20), nullable=False)
#     passing_yards = db.Column(db.String(20), nullable=False)
#     passing_td = db.Column(db.String(20), nullable=False)
#     int = db.Column(db.String(10), nullable=False)
#     rushing_att = db.Column(db.String(20), nullable=False)
#     rushing_yrds = db.Column(db.String(20), nullable=False)
#     yars_per_attempt = db.Column(db.String(20), nullable=False)
#     rushing_td = db.Column(db.String(10), nullable=False)
#     targets = db.Column(db.String(20), nullable=False)
#     receptions = db.Column(db.String(20), nullable=False)
#     yards_receiving = db.Column(db.String(20), nullable=False)
#     yards_per_reception = db.Column(db.String(20), nullable=False)
#     receiving_td = db.Column(db.String(20), nullable=False)
#     fumble = db.Column(db.String(20), nullable=False)
#     fumble_lost = db.Column(db.String(20), nullable=False)
#     misc_td = db.Column(db.String(20), nullable=False)
#     two_pm = db.Column(db.String(20), nullable=False)
#     two_pp = db.Column(db.String(20), nullable=False)
#     fant_points = db.Column(db.String(20), nullable=False)
#     ppr = db.Column(db.String(20), nullable=False)
#     dkpt = db.Column(db.String(20), nullable=False)
#     fdpt = db.Column(db.String(20), nullable=False)
#     vbd = db.Column(db.String(20), nullable=False)
#     position_rank = db.Column(db.String(20), nullable=False)
#     overall_rank = db.Column(db.String(20), nullable=False)


@app.route('/')
def index():

    data = Runners.query.all()  # Query all items from the database
    return data

#def hello():
#    return ("<h>Hello</h>"
#            "let me try to write a little more stuff")

@app.route('/receivers')
def receivers():
    return "Fantasy Football receivers"

@app.route('/tight_ends')
def tight_ends():
    return "Fantasy Football tight ends"

@app.route('/running_backs')
def running_backs():
    return "Running backs"

with app.app_context():
    db.metadata.clear()

if __name__ == '__main__':
    app.run(debug=True)