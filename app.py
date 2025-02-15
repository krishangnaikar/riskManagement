from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///construction_risk.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    job_number = db.Column(db.String(100), nullable=False)
    superintendent = db.Column(db.String(255))
    manager = db.Column(db.String(255))
    location = db.Column(db.String(255))
    bid_cost = db.Column(db.Numeric(15,2))
    bid_value = db.Column(db.Numeric(15,2))
    bid_cm = db.Column(db.Numeric(5,2))
    impact_threshold = db.Column(db.Numeric(5,2), nullable=True)
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
    cost_impact = db.Column(db.Numeric(15,2))
    most_likely_cost = db.Column(db.Numeric(15,2))
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
    # change_order_covered = db.Column(db.Boolean, default=False)
    # change_order_revenue = db.Column(db.Numeric(15,2), nullable=True)
    # opportunity = db.Column(db.Numeric(15,2), nullable=True)
    # contingency_total = db.Column(db.Numeric(15,2), nullable=True)
    # cost_impact_variance = db.Column(db.Numeric(15,2), nullable=True)

@app.route('/')
def index():
    projects = Project.query.all()
    return render_template('index.html', projects=projects)

@app.route('/project/<int:project_id>')
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    return render_template('project_detail.html', project=project)

@app.route('/add_project', methods=['POST'])
def add_project():
    data = request.form
    if data['impact_threshold'] == '':
        impact_threshold = -1
    else:
        impact_threshold = data['impact_threshold']
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


from datetime import datetime


@app.route('/add_risk/<int:project_id>', methods=['GET', 'POST'])
def add_risk(project_id):
    project = Project.query.get_or_404(project_id)

    if request.method == 'POST':
        data = request.form

        # Convert date from string to Python date object
        risk_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        most_likely_cost = float(data['cost_impact'])*(int(data['probability'])/5)
        try:
            actual_cost_impact = most_likely_cost - int(data["co_revenue"])
            variance_cost = actual_cost_impact-most_likely_cost
        except (TypeError, KeyError, ValueError):
            actual_cost_impact = 0  # Return an empty string if there's an error
            variance_cost = 0

        try:
            variance_days=int(data.get('actual_schedule_impact', None)) - int(data.get('most_likely_days', None))
        except:
            variance_days=0

        try:
            co_revenue = float(data["co_revenue"])
        except:
            co_revenue = 0

        try:
            actual_schedule_impact = float(data.get('actual_schedule_impact', None))
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
            overall_risk_value=int(data["impact"])*int(data["probability"]),
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
            actual_cost_impact = actual_cost_impact,
            actual_schedule_impact=actual_schedule_impact,
            variance_cost=variance_cost,
            variance_days=variance_days
            # change_order_covered=bool(data.get('change_order_covered', False)),

            #
            #
            #
            # opportunity=data.get('opportunity', None),
            # contingency_total=data.get('contingency_total', None),
            # cost_impact_variance=data.get('cost_impact_variance', None)
        )

        db.session.add(new_risk)
        db.session.commit()

        return redirect(url_for('project_detail', project_id=project.id))

    return render_template('add_risk.html', project_id=project.id, project=project)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
