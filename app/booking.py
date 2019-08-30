from flask import Flask
from flask import jsonify
from flask import request
from flask import make_response
from flask_sqlalchemy import SQLAlchemy
import os
import json
import urllib

app = Flask('booking')
db = SQLAlchemy(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://{}/booking.db'.format(os.path.dirname(__file__))


class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer)
    menu_id = db.Column(db.Integer)
    items = db.Column(db.String(255))
    user_id = db.Column(db.Integer)


@app.route('/', methods=['POST'])
def make_reservation():
    data = request.json
    res = Reservation(
        restaurant_id=data['restaurant_id'],
        user_id=data['user_id'],
        menu_id=data['menu_id'],
        items=data['items']
    )
    db.session.add(res)
    db.session.commit()

    restaurant_id = data['restaurant_id']
    table_id = data['table_id']
    menu_id = data['menu_id']
    items = data['items']

    req = urllib.request.Request("http://127.0.0.1:5000/make_booking",
                                 data=json.dumps({
                                         "table_id": table_id,
                                         "menu_id": menu_id,
                                         "items": items,
                                         "restaurant_id": restaurant_id
                                     }).encode('utf8'), headers={'content-type': 'application/json'})
    res = urllib.request.urlopen(req)

    ress = json.loads(res.read().decode('utf8'))

    proxy_req = urllib.request.Request("http://127.0.0.1:5002/notify",
                                       data=json.dumps({
                                           "user_id": data['user_id']
                                       }).encode('utf8'),
                                       headers={'content-type': 'application/json'})

    proxy_res = urllib.request.urlopen(proxy_req)
    proxy_ress = json.loads(proxy_res.read().decode('utf8'))

    return make_response(ress, 201)


db.create_all()

if __name__ == '__main__':
    app.run(port="5001")
