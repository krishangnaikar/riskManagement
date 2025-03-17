from flask import Flask, render_template, request, redirect, url_for, jsonify, session, render_template_string
import msal
import uuid
from flask_sqlalchemy import SQLAlchemy
import psycopg2
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = (
    'postgresql://zentroq_pg_dev_app_user:Zen%23%244Api%25%5EDatapull%40%26Data%28%21Aggregate'
    '@fintentive-postgres-dev-server.postgres.database.azure.com:5432/zentroq'
    '?options=-csearch_path%3Ddev_final'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'YOUR_SECRET_KEY'  # Replace with a secure key

# Azure AD configuration
CLIENT_ID = '8953e54d-afe6-41b4-8546-bc2db45b9d8b'
CLIENT_SECRET = 'hI88Q~R6EiLHY32mc_uwLQXcYoQRbNDlhMPkWcRc'
AUTHORITY = 'https://login.microsoftonline.com/6dd289b3-24f2-4b19-9a3c-a02e4948c5a5'
REDIRECT_PATH = '/getAToken'
SCOPE = ['User.Read']

db = SQLAlchemy(app)


###############################
# Microsoft Login Integration #
###############################

@app.route('/login')
def login():
    session["state"] = str(uuid.uuid4())
    auth_url = _build_auth_url(scopes=SCOPE, state=session["state"])
    return redirect(auth_url)


@app.route(REDIRECT_PATH)
def authorized():
    if request.args.get('state') != session.get("state"):
        return redirect(url_for("index"))

    if "error" in request.args:
        error = request.args.get('error')
        description = request.args.get('error_description')
        return f"Error: {error} - {description}"

    if request.args.get('code'):
        cache = _load_cache()
        result = _build_msal_app(cache=cache).acquire_token_by_authorization_code(
            request.args['code'],
            scopes=SCOPE,
            redirect_uri=url_for('authorized', _external=True)
        )
        if "error" in result:
            return f"Login failure: {result.get('error')} - {result.get('error_description')}"
        session["user"] = result.get("id_token_claims")
        _save_cache(cache)
    return redirect(url_for("index"))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(
        'https://login.microsoftonline.com/common/oauth2/v2.0/logout' +
        '?post_logout_redirect_uri=' + url_for('index', _external=True)
    )


def _build_msal_app(cache=None, authority=None):
    return msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=authority or AUTHORITY,
        client_credential=CLIENT_SECRET,
        token_cache=cache
    )


def _build_auth_url(scopes=None, state=None):
    return _build_msal_app().get_authorization_request_url(
        scopes or [],
        state=state or str(uuid.uuid4()),
        redirect_uri=url_for('authorized', _external=True)
    )


def _load_cache():
    # Implement token cache loading if necessary (e.g., from session or a database)
    return None


def _save_cache(cache):
    # Implement token cache saving if necessary
    pass


##################################
# Optional: Create DB Tables     #
##################################

def create_tables():
    conn_string = (
        "postgresql://denjjdlzzm:zenriskmgmt-dev%23100@"
        "zentroq-webapp-1-server.postgres.database.azure.com:5432/construction_risk?sslmode=require"
    )
    conn = psycopg2.connect(conn_string)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS project (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            job_number VARCHAR(100) NOT NULL,
            superintendent VARCHAR(255),
            manager VARCHAR(255),
            location VARCHAR(255),
            bid_cost NUMERIC(15,2),
            bid_value NUMERIC(15,2),
            bid_cm NUMERIC(5,2),
            impact_threshold NUMERIC(5,2)
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS risk (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL REFERENCES project(id),
            date DATE NOT NULL,
            classification VARCHAR(100),
            type VARCHAR(100),
            risk_type VARCHAR(100),
            name VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,
            root_cause VARCHAR(100),
            wbs VARCHAR(255),
            probability INTEGER NOT NULL,
            impact INTEGER NOT NULL,
            overall_risk_value INTEGER NOT NULL,
            cost_impact NUMERIC(15,2),
            most_likely_cost NUMERIC(15,2),
            most_likely_days INTEGER,
            response_category VARCHAR(100),
            response TEXT,
            owner VARCHAR(255),
            contingency_plan TEXT,
            status VARCHAR(50) DEFAULT 'Open',
            last_updated DATE,
            tracking_comments TEXT,
            change_order_revenue NUMERIC(15,2),
            actual_cost_impact NUMERIC(15,2),
            actual_schedule_impact INTEGER,
            variance_cost NUMERIC(15,2),
            variance_days INTEGER
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("Tables created successfully if they did not exist.")


###############################
# SQLAlchemy Models           #
###############################

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    job_number = db.Column(db.String(100), nullable=False)
    superintendent = db.Column(db.String(255))
    manager = db.Column(db.String(255))
    location = db.Column(db.String(255))
    bid_cost = db.Column(db.Numeric(15, 2))
    bid_value = db.Column(db.Numeric(15, 2))
    bid_cm = db.Column(db.Numeric(5, 2))
    impact_threshold = db.Column(db.Numeric(5, 2), nullable=True)
    risks = db.relationship('Risk', backref='project', cascade='all, delete', lazy=True)


class Risk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    classification = db.Column(db.String(100))
    type = db.Column(db.String(100))
    risk_type = db.Column(db.String(100))
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    root_cause = db.Column(db.String(100))
    wbs = db.Column(db.String(255))
    probability = db.Column(db.Integer, nullable=False)
    impact = db.Column(db.Integer, nullable=False)
    overall_risk_value = db.Column(db.Integer, nullable=False)
    cost_impact = db.Column(db.Numeric(15, 2))
    most_likely_cost = db.Column(db.Numeric(15, 2))
    most_likely_days = db.Column(db.Integer)
    response_category = db.Column(db.String(100))
    response = db.Column(db.Text)
    owner = db.Column(db.String(255))
    contingency_plan = db.Column(db.Text)
    status = db.Column(db.Enum('Open', 'Closed', 'Ongoing', name='status_enum'), default='Open')
    last_updated = db.Column(db.Date)
    tracking_comments = db.Column(db.Text)
    change_order_revenue = db.Column(db.Numeric(15, 2), nullable=True)
    actual_cost_impact = db.Column(db.Numeric(15, 2), nullable=True)
    actual_schedule_impact = db.Column(db.Integer, nullable=True)
    variance_cost = db.Column(db.Numeric(15, 2), nullable=True)
    variance_days = db.Column(db.Integer, nullable=True)


#####################################
# Ensure Login for Protected Routes #
#####################################

@app.before_request
def require_login():
    allowed_routes = ['login', 'authorized', 'static']
    if request.endpoint not in allowed_routes and 'user' not in session:
        return redirect(url_for('login'))


#####################################
# Project & Risk Management Routes  #
#####################################

@app.route('/')
def index():
    projects = Project.query.all()
    project_list = []
    for project in projects:
        project_list.append({
            "id": project.id,
            "name": project.name,
            "job_number": project.job_number,
            "location": project.location,
            "bid_cost": float(project.bid_cost) if project.bid_cost else None,
            "bid_value": float(project.bid_value) if project.bid_value else None,
            "bid_cm": float(project.bid_cm) if project.bid_cm else None,
            "impact_threshold": float(project.impact_threshold) if project.impact_threshold else None,
            "overall_risk_value": sum(risk.overall_risk_value for risk in project.risks) / len(
                project.risks) if project.risks else 0,
            "cost_impact": sum(risk.cost_impact for risk in project.risks if risk.cost_impact) if project.risks else 0,
            "most_likely_cost": sum(
                risk.most_likely_cost for risk in project.risks if risk.most_likely_cost) if project.risks else 0,
            "most_likely_days": sum(
                risk.most_likely_days for risk in project.risks if risk.most_likely_days) if project.risks else 0,
            "variance_cost": sum(
                risk.variance_cost for risk in project.risks if risk.variance_cost) if project.risks else 0,
            "variance_days": sum(
                risk.variance_days for risk in project.risks if risk.variance_days) if project.risks else 0
        })
    return render_template('index.html', projects=project_list)


@app.route('/project/<int:project_id>')
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    return render_template('project_detail.html', project=project)


@app.route('/add_project', methods=['POST', 'GET'])
def add_project():
    if request.method == "POST":
        data = request.form
        impact_threshold = data['impact_threshold'] if data['impact_threshold'] != '' else -1
        new_project = Project(
            name=data['name'],
            job_number=data['job_number'],
            superintendent=data['superintendent'],
            manager=data['manager'],
            location=data['location'],
            bid_cost=data['bid_cost'],
            bid_value=data['bid_value'],
            bid_cm=data['bid_cm'],
            impact_threshold=impact_threshold
        )
        db.session.add(new_project)
        db.session.commit()
        return redirect(url_for('index'))
    else:
        return render_template('add_project.html')


@app.route('/add_risk/<int:project_id>', methods=['GET', 'POST'])
def add_risk(project_id):
    project = Project.query.get_or_404(project_id)
    if request.method == 'POST':
        data = request.form
        risk_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        most_likely_cost = float(data['cost_impact']) * (int(data['probability']) / 5)
        try:
            actual_cost_impact = most_likely_cost - int(data["co_revenue"])
            variance_cost = actual_cost_impact - most_likely_cost
        except (TypeError, KeyError, ValueError):
            actual_cost_impact = 0
            variance_cost = 0
        try:
            variance_days = int(data.get('actual_schedule_impact', 0)) - int(data.get('most_likely_days', 0))
        except:
            variance_days = 0
        try:
            co_revenue = float(data["co_revenue"])
        except:
            co_revenue = 0
        try:
            actual_schedule_impact = float(data.get('actual_schedule_impact', 0))
        except:
            actual_schedule_impact = 0
        new_risk = Risk(
            project_id=project.id,
            date=risk_date,
            classification=data['classification'],
            type=data['type'],
            risk_type=data['risk_type'],
            name=data['name'],
            description=data['description'],
            root_cause=data['root_cause'],
            wbs=data['wbs'],
            probability=int(data['probability']),
            impact=int(data['impact']),
            overall_risk_value=int(data["impact"]) * int(data["probability"]),
            cost_impact=data['cost_impact'],
            most_likely_cost=most_likely_cost,
            most_likely_days=data.get('most_likely_days', None),
            response_category=data['response_category'],
            response=data['response_category'],
            owner=data['owner'],
            contingency_plan=data['contingency_plan'],
            status=data['status'],
            last_updated=datetime.utcnow().date(),
            tracking_comments=data['tracking_comments'],
            change_order_revenue=co_revenue,
            actual_cost_impact=actual_cost_impact,
            actual_schedule_impact=actual_schedule_impact,
            variance_cost=variance_cost,
            variance_days=variance_days
        )
        db.session.add(new_risk)
        db.session.commit()
        return redirect(url_for('project_detail', project_id=project.id))
    return render_template('add_risk.html', project_id=project.id, project=project)


@app.route('/risk/<int:risk_id>', methods=['GET', 'POST'])
def update_risk(risk_id):
    risk = Risk.query.get_or_404(risk_id)
    if request.method == 'POST':
        data = request.form
        risk.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        risk.classification = data['classification']
        risk.type = data['type']
        risk.risk_type = data['risk_type']
        risk.name = data['name']
        risk.description = data['description']
        risk.root_cause = data['root_cause']
        risk.wbs = data['wbs']
        risk.probability = int(data['probability'])
        risk.impact = int(data['impact'])
        risk.overall_risk_value = risk.probability * risk.impact
        risk.cost_impact = float(data['cost_impact'])
        risk.most_likely_cost = float(data['most_likely_cost'])
        risk.most_likely_days = int(data['most_likely_days'])
        risk.response_category = data['response_category']
        risk.response = data['response_category']
        risk.owner = data['owner']
        risk.contingency_plan = data['contingency_plan']
        risk.status = data['status']
        risk.last_updated = datetime.utcnow().date()
        risk.tracking_comments = data['tracking_comments']
        try:
            risk.change_order_revenue = float(data.get('change_order_revenue', 0))
            risk.actual_cost_impact = float(data.get('actual_cost_impact', 0))
            risk.actual_schedule_impact = int(data.get('actual_schedule_impact', 0))
            risk.variance_cost = float(data.get('variance_cost', 0))
            risk.variance_days = int(data.get('variance_days', 0))
        except ValueError:
            pass
        db.session.commit()
        return redirect(url_for('project_detail', project_id=risk.project_id))
    return render_template('risk_register.html', risk=risk)


@app.route('/edit_project/<int:project_id>', methods=['GET'])
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    return render_template('edit_project.html', project=project)


@app.route('/update_project/<int:project_id>', methods=['POST'])
def update_project(project_id):
    project = Project.query.get_or_404(project_id)
    data = request.form
    project.name = data['name']
    project.job_number = data['job_number']
    project.superintendent = data['superintendent']
    project.manager = data['manager']
    project.location = data['location']
    project.bid_cost = float(data['bid_cost']) if data['bid_cost'] else None
    project.bid_value = float(data['bid_value']) if data['bid_value'] else None
    project.bid_cm = float(data['bid_cm']) if data['bid_cm'] else None
    project.impact_threshold = float(data['impact_threshold']) if data['impact_threshold'] else None
    db.session.commit()
    return redirect(url_for('project_detail', project_id=project.id))


@app.route('/delete_project/<int:project_id>', methods=['POST'])
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/delete_risk/<int:risk_id>', methods=['POST'])
def delete_risk(risk_id):
    risk = Risk.query.get_or_404(risk_id)
    project_id = risk.project_id
    db.session.delete(risk)
    db.session.commit()
    return redirect(url_for('project_detail', project_id=project_id))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='localhost', debug=True)
