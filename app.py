# Import the dependencies.
from sqlalchemy import create_engine, func
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from flask import Flask, jsonify
import datetime as dt

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save references to each table
Station = Base.classes.station
Measurement = Base.classes.measurement

# Create our session (link) from Python to the DB
session = Session(engine)

# Calculate the date 1 year ago from the last data point in the database
latest_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]
year_ago_date = (dt.datetime.strptime(latest_date, "%Y-%m-%d") - dt.timedelta(days=365)).strftime("%Y-%m-%d")

# Find the most active station
most_active_station = session.query(Measurement.station)\
    .group_by(Measurement.station)\
    .order_by(func.count(Measurement.station).desc()).first()[0]

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################
@app.route("/")
def welcome():
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation - Precipitation data for the last 12 months<br/>"
        f"/api/v1.0/stations - List of stations<br/>"
        f"/api/v1.0/tobs - Temperature observations of the most-active station for the last 12 months<br/>"
        f"/api/v1.0/&lt;start&gt; - Temperature stats from the start date (TMIN, TAVG, TMAX)<br/>"
        f"/api/v1.0/&lt;start&gt;/&lt;end&gt; - Temperature stats for dates between the start and end (inclusive)"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    session = Session(engine)
    
    # Query for the last 12 months of precipitation data (selecting date and prcp)
    results = session.query(Measurement.date, Measurement.prcp)\
        .filter(Measurement.date >= year_ago_date).all()
    session.close()
    
    # Convert the results into a dictionary: {date: prcp}
    precip_dict = {date: prcp for date, prcp in results}
    return jsonify(precip_dict)

@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)
    results = session.query(Station.station).all()
    session.close()
    
    # Convert list of tuples into a flat list
    station_list = [station for (station,) in results]
    return jsonify(station_list)

@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)
    results = session.query(Measurement.date, Measurement.tobs)\
        .filter(Measurement.station == most_active_station)\
        .filter(Measurement.date >= year_ago_date).all()
    session.close()
    
    # Format the results as a list of dictionaries
    tobs_list = [{"date": date, "tobs": temp} for date, temp in results]
    return jsonify(tobs_list)

@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def calc_temps(start, end=None):
    session = Session(engine)
    sel = [func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]
    
    if end:
        results = session.query(*sel)\
            .filter(Measurement.date >= start)\
            .filter(Measurement.date <= end).all()
    else:
        results = session.query(*sel)\
            .filter(Measurement.date >= start).all()
    session.close()
    
    # Unpack the results (returned as a list with a single tuple)
    temps = list(results[0])
    return jsonify({
        "TMIN": temps[0],
        "TAVG": temps[1],
        "TMAX": temps[2]
    })

if __name__ == '__main__':
    app.run(debug=True)