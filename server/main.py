from flask import Flask
from flask_cors import CORS

from controller.volunteer_controller import volunteer_bp
from controller.recipient_request_controller import recipient_request_bp
from controller.recipient_controller import  recipient_bp
from controller.permission_controller import permission_bp
from controller.dc_request_controller import dc_request_bp
from controller.vehicle_controller import vehicle_bp
from controller.staff_member_controller import staff_bp
from controller.delivery_assignment_controller import delivery_assignment_bp
from controller.distribution_center_controller import distribution_center_bp
from controller.volunteer_request_controller import volunteer_request_bp
from controller.auth_controller import auth_bp

app = Flask(__name__)

CORS(app)
app.register_blueprint(volunteer_bp)
app.register_blueprint(dc_request_bp)
app.register_blueprint(recipient_request_bp)
app.register_blueprint(recipient_bp)
app.register_blueprint(permission_bp)
app.register_blueprint(vehicle_bp)
app.register_blueprint(staff_bp)
app.register_blueprint(delivery_assignment_bp)
app.register_blueprint(distribution_center_bp)
app.register_blueprint(volunteer_request_bp)
app.register_blueprint(auth_bp)
@app.route('/')
def home():
    return "Server is running!"



if __name__ == '__main__':
    app.run(debug=True)




