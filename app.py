# Import the dependencies.
import datetime
import numpy as np
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine, func
from flask import Flask, jsonify


#################################################
# Database Setup
#################################################


# reflect an existing database into a new model
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect the tables
Base = automap_base()
Base.prepare(engine, reflect=True)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
Session = sessionmaker(bind=engine)
session = Session()

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################
@app.route("/")
def home():
    return (
        f"Aloha! Please select from the following Honolulu climate analysis API Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start<br/>"
        f"/api/v1.0/start/end<br/>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    # Query for the dates and temp obs from last year.
    last_year = datetime.date(2017, 8, 23) - datetime.timedelta(days=365)
    precip = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date >= last_year).all()

    # Place results in dict with date as the key and tobs as the value.
    precip_dict = {date: prcp for date, prcp in precip}
    return jsonify(precip_dict)

@app.route("/api/v1.0/stations")
def stations():
    results = session.query(Station.station).all()

    # Prepare results and return in JSON format
    stations = list(np.ravel(results))
    return jsonify(stations=stations)

@app.route("/api/v1.0/tobs")
def tobs():
    # Determine the date from one year before
    query = session.query(func.max(Measurement.date))
    max_date = query.first()[0]
    date = datetime.datetime.strptime(max_date, "%Y-%m-%d")
    year_before = date - datetime.timedelta(days=365)

    # Find the station that is most active
    station_query = session.query(Measurement.station, func.count(Measurement.station).label('count')).group_by(Measurement.station).order_by(func.count(Measurement.station).desc()).limit(1)
    station = station_query.first()
    most_active = station[0]

    # Query the dates and temp obs data of the most active station over the year before
    temp_data = session.query(Measurement.date, Measurement.tobs).filter(Measurement.station == most_active).filter(Measurement.date >= year_before).all()
    temp_data = [dict(row) for row in temp_data]
    return jsonify(temp_data)

@app.route("/api/v1.0/<start>")
def start(start):
    # Determine min, avg, and max temps and return in JSON format
    eng = engine.connect()
    temp = eng.execute(f"SELECT MIN(tobs), AVG(tobs), MAX(tobs) FROM measurement WHERE date>='{start}'").fetchone()
    temps = {"TMIN": temp[0], "TAVG": temp[1], "TMAX": temp[2]}
    return jsonify(temps)

@app.route("/api/v1.0/<start>/<end>")
def start_end(start, end):
    # Determine min, avg, and max temps for the selected date range and return in JSON format
    eng = engine.connect()
    temp = eng.execute(f"SELECT MIN(tobs), AVG(tobs), MAX(tobs) FROM measurement WHERE date>='{start}' AND date<='{end}'").fetchone()
    temps = {"TMIN": temp[0], "TAVG": temp[1], "TMAX": temp[2]}
    return jsonify(temps)

if __name__ == "__main__":
    app.run(debug=True)

