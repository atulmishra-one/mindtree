from flask import Flask
from flask import jsonify
from flask import request
from flask import make_response
from flask_sqlalchemy import SQLAlchemy
import os
import json

app = Flask('restaurants')
db = SQLAlchemy(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}/restaurants.db'.format(os.path.dirname(__file__))


class Menu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    items = db.Column(db.String(255))

    @staticmethod
    def create():
        menu = Menu(items="pizza, coke")
        db.session.add(menu)
        db.session.commit()


Menu.create()


class Restaurant(db.Model):
    __tablename__ = 'restaurant'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32))
    tables = db.relationship('Table', backref='restaurant', lazy=True)
    menu_id = db.Column(db.Integer, db.ForeignKey('menu.id'), nullable=True)


class Table(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    avail = db.Column(db.Boolean, default=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=True)
    cost = db.Column(db.Integer)

    @staticmethod
    def create():
        table = Table(restaurant_id=1, cost=100)
        db.session.add(table)
        db.session.commit()


#Table.create()


@app.route('/')
def list_restaurants():
    q = request.args.get('q', None)  # json dict eg: ?q={"name": "x"}
    if q:
        q_json = json.loads(q)
        if q_json['name']:
            results = Restaurant.query.filter_by(name=q_json['name'])
        elif q_json['id']:
            results = Restaurant.query.filter_by(id=q_json['id'])
    else:
        results = Restaurant.query.all()
    data = []
    for result in results:
        data.append(dict(
            id=result.id,
            name=result.name,
            tables=[
                dict(id=t.id, avial=t.avail, cost=t.cost) for t in result.tables
            ],
            menus=dict(id=result.menu_id, items=Menu.query.filter_by(id=1).one().items)
        ))
    return jsonify(data)


@app.route('/', methods=['POST'])
def create():
    data = request.json
    try:
        success = True
        code = 201
        db.session.add(Restaurant(
            name=data['name'],
            tables=[Table(id=t['id'], cost=t['cost']) for t in data['tables']],
            menu_id=data['menu_id']
        ))
        db.session.commit()
    except Exception as e:
        print(e)
        success = False
        code = 401
    return make_response(jsonify(status=success), code)


@app.route('/<int:id>', methods=['PUT'])
def update(id):
    data = request.json
    try:
        success = True
        code = 201
        restaurant = Restaurant.query.filter_by(id=id)
        restaurant.name = data["name"]
        db.session.add(restaurant)
        db.session.commit()
    except:
        success = False
        code = 401
    return make_response(jsonify(status=success), code)


@app.route('/', methods=['DELETE'])
def delete():
    data = request.json
    try:
        success = True
        code = 201
        obj = Restaurant.query.filter_by(id=data['id']).one()
        db.session.delete(obj)
        db.session.commit()
    except Exception as e:
        print(e)
        success = False
        code = 401
    return make_response(jsonify(status=success), code)


@app.route('/tables', methods=['GET'])
def tables():
    results = [dict(id=t.id, avail=t.avail, restaurant_id=t.restaurant_id, cost=t.cost) for t in Table.query.all()]
    return jsonify(results)


@app.route('/menus', methods=['GET'])
def menus():
    results = [dict(id=m.id, items=m.items) for m in Menu.query.all()]
    return jsonify(results)


@app.route('/make_booking', methods=['POST'])
def make_booking():
    data = request.json
    table = Table.query.filter_by(id=data['table_id'], restaurant_id=data['restaurant_id']).one()
    cost = table.cost
    table.avail = False
    db.session.add(table)
    db.session.commit()

    return jsonify(success=True, cost=cost)

#db.drop_all()
db.create_all()

if __name__ == '__main__':
    app.run()
