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

    # Convert project objects to dictionaries
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
            "overall_risk_value": sum(risk.overall_risk_value for risk in project.risks) / len(project.risks) if project.risks else 0,
            "cost_impact": sum(risk.cost_impact for risk in project.risks if risk.cost_impact) if project.risks else 0,
            "most_likely_cost": sum(risk.most_likely_cost for risk in project.risks if risk.most_likely_cost) if project.risks else 0,
            "most_likely_days": sum(risk.most_likely_days for risk in project.risks if risk.most_likely_days) if project.risks else 0,
            "variance_cost": sum(risk.variance_cost for risk in project.risks if risk.variance_cost) if project.risks else 0,
            "variance_days": sum(risk.variance_days for risk in project.risks if risk.variance_days) if project.risks else 0
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
    else:
        return render_template('add_project.html')


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
    project_id = risk.project_id  # Store project_id before deleting

    db.session.delete(risk)
    db.session.commit()

    return redirect(url_for('project_detail', project_id=project_id))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
