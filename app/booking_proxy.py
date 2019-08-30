from flask import Flask
from flask import jsonify
from flask import request
from flask import make_response
import urllib
import json

from flask_mail import Mail
from flask_mail import Message


app = Flask('booking_proxy')
mail = Mail(app)


@app.route('/notify', methods=['POST'])
def notify():
    data = request.json

    user_request = urllib.request.urlopen("http://127.0.0.1:5003/{}".format(data['user_id']))
    user_data = json.loads(user_request.read().decode('utf8'))

    msg = Message("Booking confirmed",
                  sender="info@example.com",
                  recipients=[user_data['email']])
    msg.body = "Your booking is successfully confirmed"

    try:
        mail.send(msg)
        status = True
    except Exception as e:
        print(e)
        status = False

    return jsonify(success=status)


if __name__ == '__main__':
    app.run(port="5002")
