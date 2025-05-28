from flask import render_template, flash, url_for, redirect, request, abort
from VolunTier.models import Post, User, Projects, Application
from VolunTier.forms import PostForm, RegistrationForm, LoginForm, ProjectForm, ApplicationForm, AccountForm
from VolunTier import app, db, bcrypt
from flask_login import current_user, login_required, logout_user, login_user
from sqlalchemy import or_
import secrets, os
from PIL import Image

@app.route('/')
@app.route('/home')
def home():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=10)
    return render_template('home.html', posts=posts)

@app.route('/search')
def search():
    query = request.args.get('query', '')
    page = request.args.get('page', 1, type=int)

    posts = Post.query.filter(
        or_(
            Post.title.ilike(f'%{query}%'),
            Post.content.ilike(f'%{query}%'),
            Post.skills_needed.ilike(f'%{query}%'),
            Post.tags.ilike(f'%{query}%')
        )
    ).order_by(Post.date_posted.desc()).paginate(page=page, per_page=10)

    return render_template('results.html', posts=posts, query=query)

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pictures', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

@app.route('/account', methods=['GET', 'POST'])
@login_required
def edit_account():
    form = AccountForm()
    if form.validate_on_submit():
        if form.picture.data and hasattr(form.picture.data, 'filename'):
            if current_user.profile_picture:
                old_picture_path = os.path.join(app.root_path, 'static/profile_pictures', current_user.profile_picture)
                if os.path.exists(old_picture_path):
                    os.remove(old_picture_path)
            picture_file = save_picture(form.picture.data)
            current_user.profile_picture = picture_file

        current_user.username = form.username.data
        current_user.skills = form.skills.data
        current_user.contact_info = form.contact_info.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('home'))
    if request.method == 'GET':
        form.username.data = current_user.username
        form.skills.data = current_user.skills
        form.contact_info.data = current_user.contact_info
    return render_template('edit_account.html', form=form)

@app.route('/my_projects')
@login_required
def my_projects():
    page = request.args.get('page', 1, type=int)

    owned_projects = Projects.query.filter_by(owner_id=current_user.id)

    accepted_applications = Application.query.filter_by(user_id=current_user.id, status='Accepted').all()
    accepted_project_ids = {app.project_id for app in accepted_applications}
    accepted_projects = Projects.query.filter(Projects.id.in_(accepted_project_ids))

    all_projects = owned_projects.union(accepted_projects).order_by(Projects.date_posted.desc())

    projects = all_projects.paginate(page=page, per_page=10)

    return render_template('my_projects.html', projects=projects)

@app.route('/register', methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email = form.email.data, password = hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Your account has been created!', 'sucess')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit(): 
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash("Login unsuccessful", 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/create_project', methods=['GET', 'POST'])
@login_required
def create_project():
    form = ProjectForm()
    if form.validate_on_submit():
        project = Projects(title=form.title.data, description=form.description.data, skills_needed=form.skills_needed.data, owner=current_user)
        db.session.add(project)
        db.session.commit()
        flash('Your project has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_project.html', title='Create Project', form=form)

@app.route('/project/<int:project_id>/apply', methods=['GET', 'POST'])
@login_required
def apply_for_project(project_id):
    form = ApplicationForm()
    if form.validate_on_submit():
        application = Application(
            content=form.content.data,
            skills=form.skills.data,
            user_id=current_user.id,
            project_id=project_id,
        )
        db.session.add(application)
        db.session.commit()
        flash('Your application has been submitted!', 'success')
        return redirect(url_for('home'))
    return render_template('apply_for_project.html', title='Apply for Project', form=form)


@app.route('/project/<int:project_id>/<int:application_id>/accept')
@login_required
def accept_application(project_id, application_id):
    project = Projects.query.get_or_404(project_id)
    if project.owner != current_user:
        abort(403)
    application = Application.query.get_or_404(application_id)
    if application.project_id != project_id:
        abort(404)
    if application:
        application.status = 'Accepted'
        applicant = User.query.get(application.user_id)
        if applicant not in project.members:
            project.members.append(applicant)
        db.session.delete(application)
        db.session.commit()
        flash('Application has been acccepted.', 'success')
    return redirect(url_for('view_applications', project_id=project_id))

@app.route('/project/<int:project_id>/<int:application_id>/reject')
@login_required
def reject_application(project_id, application_id):
    project = Projects.query.get_or_404(project_id)
    if project.owner != current_user:
        abort(403)
    application = Application.query.get_or_404(application_id)
    if application.project_id != project_id:
        abort(404)
    if application:
        db.session.delete(application)
        db.session.commit()
        flash('Application has been rejected.', 'success')
    return redirect(url_for('view_applications', project_id=project_id))

@app.route('/project/<int:project_id>/view_applications')
@login_required
def view_applications(project_id):
    project = Projects.query.get_or_404(project_id)
    if project.owner != current_user:
        abort(403)
    page = request.args.get('page', 1, type=int)
    applications = Application.query.order_by(Application.date_applied.desc()).paginate(page=page, per_page=10)
    return render_template('view_applications.html', title='View Applications', applications=applications, project=project)

@app.route('/project/<int:project_id>/view_members')
@login_required
def view_members(project_id):
    project = Projects.query.get_or_404(project_id)
    if project.owner != current_user:
        abort(403)
    members = project.members
    return render_template('view_members.html', title='View Members', members=members, project=project)

@app.route('/create_post/<int:project_id>', methods=['GET', 'POST'])
@login_required
def create_post(project_id):
    form = PostForm()
    if form.validate_on_submit():
        post = Post(
            title=form.title.data,
            content=form.content.data,
            skills_needed=form.skills_needed.data,
            author_id=current_user.id,
            project_id=project_id,
            tags=form.tags.data
        )
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='Create Post', form=form)

@app.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    form = PostForm()
    if post.author != current_user:
        abort(403)
    if request.method == 'POST' and form.validate_on_submit():
        post.title = form.title.data 
        post.content = form.content.data 
        post.skills_needed = form.skills_needed.data 
        post.tags = form.tags.data 
        flash('Your post has been edited!', 'success')
        db.session.commit()
        return redirect(url_for('home'))
    if request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
        form.skills_needed.data = post.skills_needed
        form.tags.data = post.tags
    
    return render_template('create_post.html', title='Edit Post', form=form, post=post)

@app.route('/post/<int:post_id>/delete')
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))
