from flask import Flask
from flask import request
from flask_cors import CORS, cross_origin
import os

from services.home_activities import *
from services.notifications_activities import *
from services.user_activities import *
from services.create_activity import *
from services.create_reply import *
from services.search_activities import *
from services.message_groups import *
from services.messages import *
from services.create_message import *
from services.show_activity import *
from libs.cognito_jwt_token import CognitoJwtToken, extract_access_token, TokenVerifyError

# HoneyComb
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

# X Ray
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.ext.flask.middleware import XRayMiddleware

# CloudWatch
import watchtower
import logging
from time import strftime

# Rollbar
import rollbar
import rollbar.contrib.flask
from flask import got_request_exception

# Configuring Logger to Use CloudWatch
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
cw_handler = watchtower.CloudWatchLogHandler(log_group='cruddur')
LOGGER.addHandler(console_handler)

if os.getenv("ENABLE_CLOUDWATCH_LOG"):
    LOGGER.info("Cloudwatch logger enabled")
    LOGGER.addHandler(cw_handler)

# HoneyComb
# Initialize tracing and an exporter that can send data to Honeycomb
if os.getenv("ENABLE_HONEYCOMB_LOG"):
    LOGGER.info("Honeycomb logger enabled")
    provider = TracerProvider()
    processor = BatchSpanProcessor(OTLPSpanExporter())
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    tracer = trace.get_tracer(__name__)

# Show this in the logs within the backend flask app (STDOUT)
#simple_processor = SimpleSpanProcessor(ConsoleSpanExporter())
#provider.add_span_processor(simple_processor)

if os.getenv("ENABLE_XRAY_LOG"):
    LOGGER.info("X-Ray logger enabled")
    xray_url = os.getenv("AWS_XRAY_URL")
    xray_recorder.configure(service='backend-flask', dynamic_naming=xray_url)

app = Flask(__name__)

cognito_jwt_token = CognitoJwtToken(
    user_pool_id = os.getenv("AWS_COGNITO_USER_POOL_ID"),
    user_pool_client_id = os.getenv("AWS_COGNITO_USER_POOL_CLIENT_ID"),
    region = os.getenv("AWS_DEFAULT_REGION"),
    request_client=None
)

# X Ray
if os.getenv("ENABLE_XRAY_LOG"):
    XRayMiddleware(app, xray_recorder)

# HoneyComb
# Initialize automatic instrumentation with Flask
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

# Rollbar
rollbar_access_token = os.getenv('ROLLBAR_ACCESS_TOKEN')
# Other env variables
frontend = os.getenv("FRONTEND_URL")
backend = os.getenv("BACKEND_URL")
origins = [frontend, backend]
cors = CORS(
    app, 
    resources={r"/api/*": {"origins": origins}},
    headers=['Content-Type', 'Authorization'], 
    expose_headers='Authorization',
    methods="OPTIONS,GET,HEAD,POST"
)

@app.before_first_request
@cross_origin()
def init_rollbar():
    """init rollbar module"""
    if os.getenv("ENABLE_ROLLBAR_LOG"):
        LOGGER.info("Rollbar logger enabled")
        rollbar.init(
            # access token
            rollbar_access_token,
            # environment name
            'production',
            # server root directory, makes tracebacks prettier
            root=os.path.dirname(os.path.realpath(__file__)),
            # flask already sets up logging
            allow_logging_basic_config=False)

        # send exceptions from `app` to rollbar, using flask's signal system.
        got_request_exception.connect(rollbar.contrib.flask.report_exception, app)
        return 'Hello World!'
    else:
        return 'Hello World!'

@app.after_request
@cross_origin()
def after_request(response):
    timestamp = strftime('[%Y-%b-%d %H:%M]')
    LOGGER.error('%s %s %s %s %s %s', timestamp, request.remote_addr, request.method, request.scheme, request.full_path, response.status)
    return response

@app.route('/rollbar/test')
@cross_origin()
def rollbar_test():
    if os.getenv("ENABLE_ROLLBAR_LOG"):
        rollbar.report_message('Hello World!', 'warning')
        return "Rollbar: Hello World!"
    else:
        return "Hello World!"

@app.route("/api/message_groups", methods=["GET"])
@cross_origin()
def data_message_groups():
    user_handle = "armandodiaz"
    model = MessageGroups.run(user_handle=user_handle)
    if model["errors"] is not None:
        return model["errors"], 422
    else:
        return model["data"], 200


@app.route("/api/messages/@<string:handle>", methods=["GET"])
@cross_origin()
def data_messages(handle):
    user_sender_handle = "armandodiaz"
    user_receiver_handle = request.args.get("user_reciever_handle")

    model = Messages.run(
        user_sender_handle=user_sender_handle, user_receiver_handle=user_receiver_handle
    )
    if model["errors"] is not None:
        return model["errors"], 422
    else:
        return model["data"], 200


@app.route("/api/messages", methods=["POST", "OPTIONS"])
@cross_origin()
def data_create_message():
    user_sender_handle = "armandodiaz"
    user_receiver_handle = request.json["user_receiver_handle"]
    message = request.json["message"]

    model = CreateMessage.run(
        message=message,
        user_sender_handle=user_sender_handle,
        user_receiver_handle=user_receiver_handle,
    )
    if model["errors"] is not None:
        return model["errors"], 422
    else:
        return model["data"], 200

# @xray_recorder.capture("home-activities")
@app.route("/api/activities/home", methods=["GET"])
@cross_origin()
def data_home():    
    try:
        # authenticated request
        access_token = extract_access_token(request.headers)
        claims = cognito_jwt_token.verify(access_token)
        app.logger.debug("authenticated")
        app.logger.debug(claims)
        data = HomeActivities.run(logger=LOGGER, request=request, xray_recorder=xray_recorder, cognito_user_id=claims["username"])
    except TokenVerifyError as e:
        # unauthenticated request
        app.logger.debug("unauthenticated")
        app.logger.debug(e)
        data = HomeActivities.run(logger=LOGGER, request=request, xray_recorder=xray_recorder)
    return data, 200


@app.route("/api/activities/notifications", methods=["GET"])
@cross_origin()
def data_notifications():
    data = NotificationsActivities.run()
    return data, 200


@app.route("/api/activities/@<string:handle>", methods=["GET"])
@cross_origin()
def data_handle(handle):
    model = UserActivities.run(handle)
    if model["errors"] is not None:
        return model["errors"], 422
    else:
        return model["data"], 200


@app.route("/api/activities/search", methods=["GET"])
@cross_origin()
def data_search():
    term = request.args.get("term")
    model = SearchActivities.run(term)
    if model["errors"] is not None:
        return model["errors"], 422
    else:
        return model["data"], 200


@app.route("/api/activities", methods=["POST", "OPTIONS"])
@cross_origin()
def data_activities():
    user_handle = "armandodiaz"
    message = request.json["message"]
    ttl = request.json["ttl"]
    model = CreateActivity.run(message, user_handle, ttl)
    if model["errors"] is not None:
        return model["errors"], 422
    else:
        return model["data"], 200


@app.route("/api/activities/<string:activity_uuid>", methods=["GET"])
@cross_origin()
def data_show_activity(activity_uuid):
    data = ShowActivity.run(activity_uuid=activity_uuid)
    return data, 200


@app.route("/api/activities/<string:activity_uuid>/reply", methods=["POST", "OPTIONS"])
@cross_origin()
def data_activities_reply(activity_uuid):
    user_handle = "armandodiaz"
    message = request.json["message"]
    model = CreateReply.run(message, user_handle, activity_uuid)
    if model["errors"] is not None:
        return model["errors"], 422
    else:
        return model["data"], 200


if __name__ == "__main__":
    app.run(debug=True)
