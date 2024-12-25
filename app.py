from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user, LoginManager
from models import db, Customer, ServiceProfessional, Admin, Service, ServiceRequest, Review
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash
from forms import (
    CustomerLoginForm,
    ServiceProfessionalLoginForm,
    CustomerRegistrationForm,
    ServiceProfessionalRegistrationForm,
    AdminLoginForm
)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'theonepieceisreal'

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    # Try to load user from all user models
    user = Admin.query.get(int(user_id)) or \
           Customer.query.get(int(user_id)) or \
           ServiceProfessional.query.get(int(user_id))
    return user

# Initialize the database
db.init_app(app)
with app.app_context():
    db.create_all()
    print("Database created successfully!")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login/<user_type>', methods=['GET', 'POST'])
def login(user_type):
    if user_type == 'customer':
        form = CustomerLoginForm()
    elif user_type == 'service_professional':
        form = ServiceProfessionalLoginForm()
    elif user_type == 'admin':
        form = AdminLoginForm()
    else:
        flash('Invalid user type.', 'danger')
        return redirect(url_for('index'))

    if form.validate_on_submit():
        if user_type == 'customer':
            user = Customer.query.filter_by(email=form.email.data).first()
        elif user_type == 'service_professional':
            user = ServiceProfessional.query.filter_by(email=form.email.data).first()
        else:  # Admin login
            user = Admin.query.filter_by(username=form.username.data).first()

        if user :
            login_user(user)
            flash('Logged in successfully.', 'success')
            if user_type == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('dashboard', user_type=user_type))
        else:
            flash('Invalid credentials.', 'danger')

    return render_template(f'{user_type}_login.html', form=form, user_type=user_type)

#-----------------Admin Dashboard-----------------
# Fetch all services to display on the admin dashboard
@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if not isinstance(current_user, Admin):
        flash('Access denied: Only admins can access this page.', 'danger')
        return redirect(url_for('index'))

    customers = Customer.query.all()
    professionals = ServiceProfessional.query.all()
    services = Service.query.all()
    reviews = Review.query.all()

    return render_template(
        'admin_dashboard.html',
        customers=customers,
        professionals=professionals,
        services=services,
        reviews=reviews
    )
    
@app.route('/edit_service/<int:service_id>', methods=['POST'])
@login_required
def edit_service(service_id):
    service = Service.query.get_or_404(service_id)
    service.name = request.form.get('name', service.name)
    service.description = request.form.get('description', service.description)
    service.base_price = float(request.form.get('base_price', service.base_price))
    service.time_required = request.form.get('time_required', service.time_required)

    db.session.commit()
    flash(f'Service "{service.name}" updated successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/remove_service/<int:service_id>', methods=['POST'])
@login_required
def remove_service(service_id):
    service = Service.query.get_or_404(service_id)
    db.session.delete(service)
    db.session.commit()
    flash(f'Service "{service.name}" deleted successfully.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/approve_professional/<int:professional_id>', methods=['POST'])
@login_required
def approve_professional(professional_id):
    if not isinstance(current_user, Admin):
        flash('Access denied: Only admins can perform this action.', 'danger')
        return redirect(url_for('index'))

    professional = ServiceProfessional.query.get_or_404(professional_id)
    professional.profile_verified = True
    db.session.commit()
    flash(f'Service professional {professional.name} approved successfully.', 'success')

    return redirect(url_for('admin_dashboard'))


@app.route('/block_user/<user_type>/<int:user_id>', methods=['POST'])
@login_required
def block_user(user_type, user_id):
    if not isinstance(current_user, Admin):
        flash('Access denied: Only admins can perform this action.', 'danger')
        return redirect(url_for('index'))

    if user_type == 'customer':
        user = Customer.query.get_or_404(user_id)
    elif user_type == 'service_professional':
        user = ServiceProfessional.query.get_or_404(user_id)
    else:
        flash('Invalid user type.', 'danger')
        return redirect(url_for('admin_dashboard'))

    user.is_active = False
    db.session.commit()
    flash(f'{user_type.capitalize()} {user.name} has been blocked.', 'success')

    return redirect(url_for('admin_dashboard'))



# Add a new service
@app.route('/add_service', methods=['POST'])
@login_required
def add_service():
    if not isinstance(current_user, Admin):
        flash('Access denied: Only admins can perform this action.', 'danger')
        return redirect(url_for('index'))

    name = request.form.get('name', '')
    description = request.form.get('description', '')
    base_price = request.form.get('base_price')
    time_required = request.form.get('time_required')

    if not name or not base_price or not time_required:
        flash('All fields except description are required.', 'danger')
        return redirect(url_for('admin_dashboard'))

    new_service = Service(
        name=name,
        description=description,
        base_price=float(base_price),
        time_required=time_required
    )
    db.session.add(new_service)
    db.session.commit()
    flash(f'Service "{name}" added successfully.', 'success')

    return redirect(url_for('admin_dashboard'))


# Update an existing service
@app.route('/update_service/<int:service_id>', methods=['POST'])
@login_required
def update_service(service_id):
    if not isinstance(current_user, Admin):
        flash('Access denied: Only admins can perform this action.', 'danger')
        return redirect(url_for('index'))

    service = Service.query.get_or_404(service_id)
    service.name = request.form.get('name', service.name)
    service.description = request.form.get('description', service.description)
    service.base_price = float(request.form.get('base_price', service.base_price))
    service.time_required = request.form.get('time_required', service.time_required)

    db.session.commit()
    flash(f'Service "{service.name}" updated successfully.', 'success')

    return redirect(url_for('admin_dashboard'))


# Delete an existing service
@app.route('/delete_service/<int:service_id>', methods=['POST'])
@login_required
def delete_service(service_id):
    if not isinstance(current_user, Admin):
        flash('Access denied: Only admins can perform this action.', 'danger')
        return redirect(url_for('index'))

    # Fetch the service to delete
    service = Service.query.get_or_404(service_id)

    # Handle associated service requests
    service_requests = ServiceRequest.query.filter_by(service_id=service_id).all()
    if service_requests:
        for request in service_requests:
            db.session.delete(request)  # Delete associated service requests

    # Delete the service
    db.session.delete(service)
    db.session.commit()
    
    flash(f'Service "{service.name}" and its associated requests have been deleted successfully.', 'success')

    return redirect(url_for('admin_dashboard'))


#unblocking a user
@app.route('/unblock_user/<user_type>/<int:user_id>', methods=['POST'])
@login_required
def unblock_user(user_type, user_id):
    if not isinstance(current_user, Admin):
        flash('Access denied: Only admins can perform this action.', 'danger')
        return redirect(url_for('index'))

    if user_type == 'customer':
        user = Customer.query.get_or_404(user_id)
    elif user_type == 'service_professional':
        user = ServiceProfessional.query.get_or_404(user_id)
    else:
        flash('Invalid user type.', 'danger')
        return redirect(url_for('admin_dashboard'))

    user.is_active = True
    db.session.commit()
    flash(f'{user_type.capitalize()} {user.name} has been unblocked.', 'success')

    return redirect(url_for('admin_dashboard'))


#-----------------End of Admin Dashboard-----------------
#--Review Dashboard--
@app.route('/leave_review/<int:request_id>', methods=['POST'])
@login_required
def leave_review(request_id):
    if not isinstance(current_user, Customer):
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    service_request = ServiceRequest.query.get_or_404(request_id)

    # Ensure the request belongs to the customer
    if service_request.customer_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('customer_dashboard'))

    # Ensure the request is closed
    if service_request.service_status != 'closed':
        flash('You can only review completed services.', 'danger')
        return redirect(url_for('customer_dashboard'))

    # Add the review
    rating = int(request.form.get('rating'))
    feedback = request.form.get('feedback', '')

    review = Review(
        service_request_id=request_id,
        customer_id=current_user.id,
        rating=rating,
        feedback=feedback
    )

    db.session.add(review)
    db.session.commit()
    flash('Thank you for your feedback!', 'success')
    return redirect(url_for('customer_dashboard'))
#-----------------End of Review Dashboard-----------------
#-----------------Customer Dashboard-----------------
# Fetch customer dashboard
@app.route('/customer_dashboard')
@login_required
def customer_dashboard():
    if not isinstance(current_user, Customer):
        flash('Access denied: Only customers can access this page.', 'danger')
        return redirect(url_for('index'))

    # Query all services to display in the dropdown
    services = Service.query.all()

    # Query service requests specific to the logged-in customer
    service_requests = ServiceRequest.query.filter_by(customer_id=current_user.id).all()

    return render_template(
        'customer_dashboard.html',
        services=services,
        service_requests=service_requests
    )

#----------Search for service professionals----------
@app.route('/search_services', methods=['GET'])
@login_required
def search_services():
    if not isinstance(current_user, Customer):
        flash('Access denied: Only customers can search services.', 'danger')
        return redirect(url_for('index'))

    query = request.args.get('query', '').strip()
    search_results = Service.query.filter(
        (Service.name.ilike(f"%{query}%")) |
        (Service.description.ilike(f"%{query}%"))
    ).all()

    return render_template(
        'customer_dashboard.html',
        services=Service.query.all(),
        service_requests=ServiceRequest.query.filter_by(customer_id=current_user.id).all(),
        search_results=search_results
    )

@app.route('/search_professionals', methods=['GET'])
@login_required
def search_professionals():
    if not isinstance(current_user, Admin):
        flash('Access denied: Only admins can search professionals.', 'danger')
        return redirect(url_for('index'))

    query = request.args.get('query', '').strip()
    professional_results = ServiceProfessional.query.filter(
        (ServiceProfessional.name.ilike(f"%{query}%")) |
        (ServiceProfessional.email.ilike(f"%{query}%")) |
        (ServiceProfessional.service_type.ilike(f"%{query}%"))
    ).all()

    customers = Customer.query.all()
    professionals = ServiceProfessional.query.all()
    services = Service.query.all()

    return render_template(
        'admin_dashboard.html',
        customers=customers,
        professionals=professionals,
        services=services,
        professional_results=professional_results
    )

@app.route('/close_service_request_sp/<int:request_id>', methods=['POST'])
@login_required
def close_service_request_sp(request_id):
    # Ensure the current user is a service professional
    if not isinstance(current_user, ServiceProfessional):
        flash('Access denied: Only service professionals can close service requests.', 'danger')
        return redirect(url_for('index'))

    # Fetch the service request
    service_request = ServiceRequest.query.get_or_404(request_id)

    # Fetch all service requests assigned to the current professional
    service_requests = ServiceRequest.query.all()

    # Ensure the service professional is assigned to this request
    if service_request.professional_id != current_user.id:
        flash('Access denied: You are not assigned to this service request.', 'danger')
        return render_template(
            'service_professional_dashboard.html',
            service_requests=service_requests
        )

    # Ensure the service request is in "assigned" status
    if service_request.service_status != 'assigned':
        flash('This service request cannot be closed because it is not in the assigned state.', 'danger')
        return render_template(
            'service_professional_dashboard.html',
            service_requests=service_requests
        )

    # Close the service request
    service_request.service_status = 'closed'
    service_request.date_of_completion = datetime.utcnow()
    db.session.commit()

    flash(f'Service request {service_request.id} has been successfully closed.', 'success')

    # Refresh the service requests list and return to the dashboard
    service_requests = ServiceRequest.query.all()
    return render_template(
        'service_professional_dashboard.html',
        service_requests=service_requests
    )


#----------End of Search for service professionals----------
#----------View service requests----------ServiceProfessional_dashboard----------
@app.route('/service_professional_dashboard')
@login_required
def service_professional_dashboard():
    if not isinstance(current_user, ServiceProfessional):
        flash('Access denied: Only service professionals can access this page.', 'danger')
        return redirect(url_for('index'))

    # Fetch service requests assigned to the professional
    service_requests = ServiceRequest.query.filter_by(professional_id=current_user.id).all()

    # Fetch reviews for completed service requests handled by the professional
    reviews = Review.query.join(ServiceRequest).filter(ServiceRequest.professional_id == current_user.id).all()

    return render_template(
        'service_professional_dashboard.html',
        service_requests=service_requests,
        reviews=reviews
    )


@app.route('/update_service_professional_profile', methods=['POST'])
@login_required
def update_service_professional_profile():
    if not isinstance(current_user, ServiceProfessional):
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    current_user.name = request.form.get('name')
    current_user.email = request.form.get('email')
    current_user.phone = request.form.get('phone')
    current_user.service_type = request.form.get('service_type')

    db.session.commit()
    flash('Profile updated successfully.', 'success')
    return redirect(url_for('service_professional_dashboard'))

@app.route('/accept_service_request/<int:request_id>', methods=['POST'])
@login_required
def accept_service_request(request_id):
    if not isinstance(current_user, ServiceProfessional):
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    service_request = ServiceRequest.query.get_or_404(request_id)

    if service_request.service_status != 'requested':
        flash('This request cannot be accepted.', 'danger')
        return redirect(url_for('service_professional_dashboard'))

    service_request.service_status = 'assigned'
    service_request.professional_id = current_user.id
    db.session.commit()
    flash('Service request accepted.', 'success')

    return redirect(url_for('service_professional_dashboard'))

@app.route('/reject_service_request/<int:request_id>', methods=['POST'])
@login_required
def reject_service_request(request_id):
    if not isinstance(current_user, ServiceProfessional):
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    service_request = ServiceRequest.query.get_or_404(request_id)

    if service_request.service_status != 'requested':
        flash('This request cannot be rejected.', 'danger')
        return redirect(url_for('service_professional_dashboard'))

    service_request.service_status = 'rejected'
    db.session.commit()
    flash('Service request rejected.', 'success')

    return redirect(url_for('service_professional_dashboard'))

@app.route('/close_service_request_by_professional/<int:request_id>', methods=['POST'])
@login_required
def close_service_request_by_professional(request_id):
    if not isinstance(current_user, ServiceProfessional):
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    service_request = ServiceRequest.query.get_or_404(request_id)

    if service_request.service_status != 'assigned':
        flash('This request cannot be closed.', 'danger')
        return redirect(url_for('service_professional_dashboard'))

    service_request.service_status = 'closed'
    service_request.date_of_completion = datetime.utcnow()
    db.session.commit()
    flash('Service request closed successfully.', 'success')

    return redirect(url_for('service_professional_dashboard'))

#----------End of View service requests----------
#----------Customer Dashboard----------
# Update customer profile
@app.route('/update_customer_profile', methods=['POST'])
@login_required
def update_customer_profile():
    if not isinstance(current_user, Customer):
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    current_user.name = request.form.get('name')
    current_user.email = request.form.get('email')
    current_user.phone = request.form.get('phone')
    current_user.address = request.form.get('address')
    current_user.pin_code = request.form.get('pin_code')

    db.session.commit()
    flash('Profile updated successfully.', 'success')
    return redirect(url_for('customer_dashboard'))


# Create a new service request
@app.route('/create_service_request', methods=['POST'])
@login_required
def create_service_request():
    if not isinstance(current_user, Customer):
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    service_id = int(request.form.get('service_id'))
    remarks = request.form.get('remarks', '')

    new_request = ServiceRequest(
        service_id=service_id,
        customer_id=current_user.id,
        remarks=remarks,
        service_status='requested'
    )
    db.session.add(new_request)
    db.session.commit()
    flash('Service request created successfully.', 'success')
    return redirect(url_for('customer_dashboard'))


# Edit an existing service request
@app.route('/edit_service_request/<int:request_id>', methods=['POST'])
@login_required
def edit_service_request(request_id):
    if not isinstance(current_user, Customer):
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    service_request = ServiceRequest.query.get_or_404(request_id)

    # Ensure the request belongs to the current customer
    if service_request.customer_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('customer_dashboard'))

    # Update remarks and service_id
    service_request.remarks = request.form.get('remarks', service_request.remarks)
    service_id = request.form.get('service_id')
    if service_id:
        service_request.service_id = int(service_id)

    db.session.commit()
    flash('Service request updated successfully.', 'success')
    return redirect(url_for('customer_dashboard'))



# Close an existing service request
@app.route('/close_service_request/<int:request_id>', methods=['POST'])
@login_required
def close_service_request(request_id):
    if not isinstance(current_user, Customer):
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    service_request = ServiceRequest.query.get_or_404(request_id)

    # Ensure the request belongs to the current customer
    if service_request.customer_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('customer_dashboard'))

    service_request.service_status = 'closed'
    db.session.commit()
    flash('Service request closed successfully.', 'success')
    return redirect(url_for('customer_dashboard'))

#-----------------End of Customer Dashboard-----------------


@app.route('/register/<user_type>', methods=['GET', 'POST'])
def register(user_type):
    if user_type == 'customer':
        form = CustomerRegistrationForm()
    elif user_type == 'service_professional':
        form = ServiceProfessionalRegistrationForm()
    else:
        flash('Invalid user type.', 'danger')
        return redirect(url_for('index'))

    if form.validate_on_submit():
        if user_type == 'customer':
            user = Customer(
                username=form.username.data,
                name=form.username.data,
                email=form.email.data,
                phone=form.phone.data,
                address=form.address.data,
                pin_code=form.pincode.data,
                password=generate_password_hash(form.password.data)
            )
        else:
            user = ServiceProfessional(
                username=form.username.data,
                name=form.username.data,
                email=form.email.data,
                phone=form.phone.data,
                service_type=form.service_type.data,
                password=generate_password_hash(form.password.data),
                experience=0
            )

        db.session.add(user)
        db.session.commit()
        flash('Registration successful. You can now log in.', 'success')
        return redirect(url_for('login', user_type=user_type))

    return render_template(f'{user_type}_registration.html', form=form, user_type=user_type)


@app.route('/dashboard/<user_type>')
@login_required
def dashboard(user_type):
    print(f"Current user: {current_user}")
    print(f"User type: {user_type}")
    
    if user_type == 'customer' and isinstance(current_user, Customer):
        # Query all services to display in the dropdown
        services = Service.query.all()

        # Query service requests specific to the logged-in customer
        service_requests = ServiceRequest.query.filter_by(customer_id=current_user.id).all()

        return render_template(
            'customer_dashboard.html',
            services=services,
            service_requests=service_requests
        )
    elif user_type == 'service_professional' and isinstance(current_user, ServiceProfessional):
        # Fetch all service requests
        service_requests = ServiceRequest.query.all()
        reviews = Review.query.join(ServiceRequest).filter(ServiceRequest.professional_id == current_user.id).all()

        return render_template(
            'service_professional_dashboard.html',
            service_requests=service_requests,
            reviews=reviews
        )
    else:
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))




@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
