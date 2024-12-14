import sqlite3
import bcrypt
from flask import Flask, jsonify,render_template,request,session,redirect,url_for,flash,logging,send_from_directory
import os
from flask_mail import Mail, Message





app = Flask(__name__)
app.secret_key = 'my_secret_key_123'




@app.route('/')
def hello_world():
    if 'username' not in session:
        return render_template('home.html')
    return render_template('home.html')

ALLOWED_EXTENSIONS = ['mp4']
app.config['MAX_CONTENT_LENGTH'] = 30 * 1024 * 1024
# app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'videos')
app.config['UPLOAD_FOLDER'] = 'static/videos'

@app.errorhandler(413)
def too_large(e):
    return "File is too large. Please upload a file smaller than 30 MB.", 413

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload',methods=['GET','POST'])
def upload():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    job_id = request.form.get('job_id')
    video = request.files.get('video')
    print(f"Username: {username}, Job ID: {job_id}, Video: {video}")

    conn = sqlite3.connect('mixmuse_users.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM applicants WHERE username = ? AND job_id = ?', (username, job_id))
    already_applied = c.fetchone()[0] > 0
    if already_applied:
        conn.close()
        flash("You have already applied for this job.")
        return redirect(url_for('posts'))    



    if video and video.filename.endswith('.mp4'):
        # Save the video file
        video_filename = f"{username}_{job_id}.mp4"  # Create a unique filename
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)
        video.save(video_path)

        relative_video_path = f"{video_filename}"

        # Insert the data into the SQLite database
        c.execute('INSERT INTO applicants (username, job_id, video_path) VALUES (?, ?, ?)',
                  (username, job_id, relative_video_path))
        conn.commit()
        conn.close()

        return redirect(url_for('posts'))  # Redirect to a success page or wherever you want

        
    return "Invalid file format", 400

@app.route('/videos/<filename>')
def audition_video(filename):
    try:
        # Get the directory path relative to the current file
        videos_dir = os.path.join('static', 'videos')
        full_path = os.path.join(videos_dir, filename)
        print(f"Requested filename: {filename}")
        print(f"Looking in directory: {videos_dir}")
        print(f"Full path: {full_path}")
        print(f"File exists: {os.path.exists(full_path)}")
        return send_from_directory(videos_dir, filename)
    except Exception as e:
        print(f"Error serving video: {str(e)}")
        return str(e), 404
    

@app.route('/viewappliprofile/<user>')
def viewappliprofile(user):
    if 'username' in session:
        connection = sqlite3.connect('mixmuse_users.db')
        cursor = connection.cursor()
        username = session['username']
        query = "SELECT * from users WHERE username = ?"
        cursor.execute(query,(user,))
        user_data = cursor.fetchone()
        is_own_profile = session.get('username') == user 
        connection.close()
        return render_template('profile.html', user_data=user_data,is_own_profile=is_own_profile,username=username)


@app.route('/vapplicants/<int:job_id>')
def vapplicants(job_id):
    connection = sqlite3.connect('mixmuse_users.db')
    cursor = connection.cursor()
    username = session['username']


    query = "SELECT * FROM users WHERE username = ?"
    cursor.execute(query, (username,))
    user_data = cursor.fetchone()

    cursor.execute("SELECT username FROM accepted_applicants WHERE job_id = ?", (job_id,))
    accepted_usernames = {row[0] for row in cursor.fetchall()}

    # Fetch job details based on job_id
    cursor.execute("SELECT username,video_path FROM applicants WHERE job_id = ?", (job_id,))
    applicants = cursor.fetchall()

    filtered_applicants = [applicant for applicant in applicants if applicant[0] not in accepted_usernames]



    connection.close()
    

    return render_template('viewappli.html', user_data=user_data,applicants=filtered_applicants,username=username)




@app.route('/reject_applicant',methods=['GET','POST'])
def reject_applicant():
    data = request.get_json()
    print(f"Received data: {data}")
    username = data.get('username')
    job_id = data.get('job_id')
    conn = sqlite3.connect('mixmuse_users.db')
    c = conn.cursor()

    try:
        # Delete the applicant from the database
        c.execute("DELETE FROM applicants WHERE username = ?", (username,))
        conn.commit()
        if c.rowcount > 0:
            return jsonify({'message': 'Applicant rejected successfully.'}), 200
        else:
            return jsonify({'message': 'No applicant found with the given username and job ID.'}), 404
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    finally:
        conn.close()


@app.route('/accept_applicant', methods=['POST'])
def accept_applicant():
    data = request.get_json()
    print('Received data:', data)
    username = data.get('username')
    job_id = data.get('job_id', '').strip()
    # job_id = data.get('job_id')

    if username and job_id:
        try:
            conn = sqlite3.connect('mixmuse_users.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO accepted_applicants (username, job_id)
                VALUES (?, ?)
            ''', (username, job_id))
            conn.commit()
            return jsonify({'message': 'Applicant accepted successfully!'}), 200
        except sqlite3.Error as e:
            return jsonify({'message': f'An error occurred: {str(e)}'}), 500
        finally:
            conn.close()
        
    else:
        return jsonify({'message': 'Invalid data!'}), 400
    


    


# @app.route('/notifyuser',methods=['GET'])
# def notifyuser():
#     username = session.get('username')  # Get the current session username
#     if not username:
#         redirect(url_for(login))

#     conn = sqlite3.connect('mixmuse_users.db')
#     cursor = conn.cursor()


#     query = "SELECT * FROM users WHERE username = ?"
#     cursor.execute(query, (username,))
#     user_data = cursor.fetchone()
#     if username:
#         # Connect to the database
        
#         # SQL query to check if the user is in accepted_applicants and get the job_id
#         query_job_id = '''
#             SELECT job_id
#             FROM accepted_applicants
#             WHERE username = ?
#         '''
        
#         # Execute the query to get the job_id
#         job_id_result = cursor.execute(query_job_id, (username,)).fetchone()

#         messages = []
        
#         if job_id_result:
#             job_id = job_id_result[0]  # Extract job_id
            
#             # Now, use job_id to get company_name, employer_email, and job_title from posts table
#             query_post_info = '''
#                 SELECT company_name, username, job_title
#                 FROM posts
#                 WHERE id = ?
#             '''
            
#             # Execute the query to get post information
#             post_info_result = cursor.execute(query_post_info, (job_id,)).fetchone()

#             if post_info_result:
#                 employer_username = post_info_result[1]  # Get employer username
                
#                 # Now use employer_username to find the employer's email in the users table
#                 query_employer_email = '''
#                     SELECT email
#                     FROM users
#                     WHERE username = ?
#                 '''
                
#                 # Execute the query to get the employer's email
#                 employer_email_result = cursor.execute(query_employer_email, (employer_username,)).fetchone()
                
#                 conn.close()  # Close the connection
                
#                 if employer_email_result:
#                     employer_email = employer_email_result[0]  # Extract employer's email
                    
#                     # If the job post information is found, return the message
#                     # return jsonify({
#                     #     'message': f"Congratulations! You have been selected by {post_info_result[0]} as a {post_info_result[2]}! Please contact {employer_email} for more details."
#                     # })
#                     messages.append({
#                         'company_name':post_info_result[0],
#                         'job_title':post_info_result[2],
#                         'employer_email':employer_email
#                     })

#             conn.close()  # Close the connection
#             if messages:
#                 return render_template('notify.html',messages=messages,user_data=user_data)
            
    
#     # If no user found or not selected
#     return render_template('notify.html',user_data=user_data)

@app.route('/notifyuser', methods=['GET'])
def notifyuser():
    username = session.get('username')  # Get the current session username
    if not username:
        return redirect(url_for('login'))  # Ensure you redirect properly

    conn = sqlite3.connect('mixmuse_users.db')
    cursor = conn.cursor()

    # Query to get user data
    query = "SELECT * FROM users WHERE username = ?"
    cursor.execute(query, (username,))
    user_data = cursor.fetchone()

    messages = []

    # SQL query to get all job_ids for accepted applicants
    query_job_ids = '''
        SELECT job_id
        FROM accepted_applicants
        WHERE username = ?
    '''
    
    # Execute the query to get job_ids
    job_id_results = cursor.execute(query_job_ids, (username,)).fetchall()

    # Iterate over all job_ids
    for job_id_result in job_id_results:
        job_id = job_id_result[0]  # Extract job_id
        
        # Get company_name, employer_username, and job_title from posts table
        query_post_info = '''
            SELECT company_name, username, job_title
            FROM posts
            WHERE id = ?
        '''
        
        # Execute the query to get post information
        post_info_result = cursor.execute(query_post_info, (job_id,)).fetchone()

        if post_info_result:
            employer_username = post_info_result[1]  # Get employer username
            
            # Get the employer's email from the users table
            query_employer_email = '''
                SELECT email
                FROM users
                WHERE username = ?
            '''
            
            # Execute the query to get the employer's email
            employer_email_result = cursor.execute(query_employer_email, (employer_username,)).fetchone()
            
            if employer_email_result:
                employer_email = employer_email_result[0]  # Extract employer's email
                
                # Append the message to the list
                messages.append({
                    'company_name': post_info_result[0],
                    'job_title': post_info_result[2],
                    'employer_email': employer_email
                })

    conn.close()  # Close the connection

    # Render the template with all messages or user data if no messages
    return render_template('notify.html', messages=messages, user_data=user_data)

@app.route('/notifyemp',methods=['GET'])
def notifyemp():
    username = session.get('username')  # Get the current session username
    if not username:
        return redirect(url_for('login'))

    conn = sqlite3.connect('mixmuse_users.db')
    cursor = conn.cursor()

    query = "SELECT * FROM users WHERE username = ?"
    cursor.execute(query, (username,))
    user_data = cursor.fetchone()

    # SQL query to get all job_ids posted by the employer
    query_job_ids = '''
        SELECT id, job_title
        FROM posts
        WHERE username = ?
    '''
    
    cursor.execute(query_job_ids, (username,))
    job_ids = cursor.fetchall()

    accepted_applicants = []

    if job_ids:
        # Extract job_id and check accepted applicants for each job_id
        for job_id in job_ids:
            job_id_value = job_id[0]  # Get job_id
            job_title_value = job_id[1]
            
            # SQL query to get accepted applicants for this job_id
            query_accepted_applicants = '''
                SELECT username
                FROM accepted_applicants
                WHERE job_id = ?
            '''
            
            cursor.execute(query_accepted_applicants, (job_id_value,))
            applicants = cursor.fetchall()
            
            for applicant in applicants:
                applicant_username = applicant[0]
                
                # Now get the email of the accepted applicant from the users table
                query_applicant_email = '''
                    SELECT email
                    FROM users
                    WHERE username = ?
                '''
                
                cursor.execute(query_applicant_email, (applicant_username,))
                email_result = cursor.fetchone()

                if email_result:
                    accepted_applicants.append({
                        'username': applicant[0],
                        'email':email_result[0],
                        'job_id': job_id_value,
                        'job_title':job_title_value
                    })

    conn.close()  # Close the connection

    # Render the template with accepted applicants
    return render_template('notifyemp.html', accepted_applicants=accepted_applicants, username=username,user_data=user_data)



@app.route('/job/<int:job_id>')
def job_details(job_id):
    # Fetch the job details from the database
    conn = sqlite3.connect('mixmuse_users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
    job = c.fetchone()  # Assuming job is a single record
    conn.close()

    # Check if job is found
    if job is None:
        return "Job not found", 404

    # Render the template with the job data
    return render_template('reqexp.html', job=job)


@app.route('/applicants')
def applicants():
    if 'username' in session:
        connection = sqlite3.connect('mixmuse_users.db')
        cursor = connection.cursor()

        username = session['username']
        website_user = session['website_user']
        query = "SELECT * from users where username = '"+username+"' "
        cursor.execute(query)
        user_data = cursor.fetchone()
        # cursor.execute("SELECT id, username, job_id, video_path FROM applicants")
        # applicants = cursor.fetchall()
        # connection.close()

        return render_template('viewappli.html',website_user=website_user,user_data=user_data,username=username)

    return render_template('viewappli.html')


@app.route('/api/acceptedApplicantsCount/<int:job_id>', methods=['GET'])
def get_accepted_applicants_count(job_id):
    try:
        conn = sqlite3.connect('mixmuse_users.db')
        cursor = conn.cursor()

        # Query to count accepted applicants for the given job_id
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM accepted_applicants 
            WHERE job_id = ?
        """, (job_id,))
        result = cursor.fetchone()

        # count = result['count'] if result and 'count' in result else 0
        # count = result[0] if result else 0
        count = result[0]

        conn.close()
        return jsonify({'count': count}), 200

    except Exception as e:
        return jsonify({'error': 'An error occurred', 'message': str(e)}), 500
    

@app.route('/api/updateOpenPositions', methods=['POST'])
def update_open_positions():
    try:
        # Get the JSON data from the request
        data = request.get_json()
        job_id = data.get('jobId')
        new_open_positions = data.get('newOpenPositions')

        if job_id is None or new_open_positions is None:
            return jsonify({'error': 'Missing jobId or newOpenPositions'}), 400

        # Connect to the database
        conn = sqlite3.connect('mixmuse_users.db')  # Ensure you're passing the correct path to the database
        cursor = conn.cursor()

        # Update the open_positions for the specified job
        cursor.execute("""
            UPDATE posts
            SET open_positions = ?
            WHERE id = ?
        """, (new_open_positions, job_id))

        # Commit the transaction
        conn.commit()

        # Check if any rows were affected (i.e., job_id exists)
        if cursor.rowcount == 0:
            return jsonify({'error': 'Job not found'}), 404

        # Close the connection
        conn.close()

        return jsonify({'message': 'Open positions updated successfully'}), 200

    except Exception as e:
        return jsonify({'error': 'An error occurred', 'message': str(e)}), 500


@app.route('/about')
def about():
    return render_template('about.html')



@app.route('/logout')
def logout():
    session.pop('username', None)
    return render_template('home.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        connection = sqlite3.connect('mixmuse_users.db')
        cursor = connection.cursor()

        username = request.form['user']
        password = request.form['password']

        print(f"Login attempt for user: {username}")  # Debug print

        query = "SELECT username, password, website_user FROM users WHERE username = ?"
        cursor.execute(query, (username,))

        user_data = cursor.fetchone()

        if user_data:
            stored_username, stored_password, website_user = user_data
            print(f"User found: {stored_username}")  # Debug print
            print(f"Stored password type: {type(stored_password)}")
            print(f"Stored password length: {len(stored_password)}")

            try:
                if isinstance(stored_password, str):
                    stored_password = stored_password.encode('utf-8')

                # Convert input password to bytes for comparison
                input_password = password.encode('utf-8')
                
                
                # Use bcrypt to check the password
                if bcrypt.checkpw(input_password, stored_password):
                    print("Password check succeeded")
                    session['username'] = username
                    session['website_user'] = website_user
                    
                    # Fetch additional user data if needed
                    query = "SELECT * FROM users WHERE username = ?"
                    cursor.execute(query, (username,))
                    user_data = cursor.fetchone()

                    # connection.close()

                    if website_user == 'artist':
                        return render_template('pexp.html', name=username, user_data=user_data)
                    elif website_user == 'employer':
                        return render_template('EmpHomePage.html', name=username, user_data=user_data)
                    else:
                        return redirect(url_for('login'))
                    
                    # return render_template('posts.html', name=username, user_data=user_data)
                else:
                    print("Password check failed")
                    connection.close()
                    flash('Invalid username or password', 'error')
                    return redirect(url_for('login'))
            except Exception as e:
                print(f"Exception during password check: {str(e)}")
                connection.close()
                flash('An error occurred during login. Please try again.', 'error')
                return redirect(url_for('login'))
        else:
            print(f"No user found for username: {username}")
            connection.close()
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            # Get form data with default values to prevent KeyError
            username = request.form.get('user', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm-password', '')
            email = request.form.get('email', '').strip()
            fullname = request.form.get('name', '').strip()
            phonenumber = request.form.get('phone', '').strip()
            gender = request.form.get('gender', '').strip()
            website_user = request.form.get('website_user', '').strip()
            

            # Validate required fields
            if not all([username, password, confirm_password, email, fullname, phonenumber, gender,website_user]):
                return render_template('signup.html',
                    error_msg="All fields are required.",
                    username=username,
                    email=email,
                    fullname=fullname,
                    phonenumber=phonenumber,
                    gender=gender)

            # Check if passwords match
            if password != confirm_password:
                return render_template('signup.html',
                    error_msg="Passwords do not match. Please try again.",
                    username=username,
                    email=email,
                    fullname=fullname,
                    phonenumber=phonenumber,
                    gender=gender)

            # Connect to database
            con = sqlite3.connect('mixmuse_users.db')
            c = con.cursor()

            # Check if username exists
            c.execute("SELECT * FROM users WHERE username = ?", (username,))
            existing_user = c.fetchone()

            if existing_user:
                con.close()
                return render_template('signup.html',
                    error_msg="Username already exists. Please choose a different username.",
                    email=email,
                    fullname=fullname,
                    phonenumber=phonenumber,
                    gender=gender)

            # Hash password and insert user
            # hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            c.execute("""
                INSERT INTO users (username, password, fullname, phoneno, gender, email,website_user) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (username, hashed_password, fullname, phonenumber, gender, email,website_user))
            
            con.commit()
            # con.close()

            flash('Registration successful! Please login.')
            return redirect(url_for('login'))

        except Exception as e:
            app.logger.error(f"Error during signup: {str(e)}")  # For debugging
            return render_template('signup.html',
                error_msg="An error occurred during signup. Please try again.",
                username=username,
                email=email,
                fullname=fullname,
                phonenumber=phonenumber,
                gender=gender)
        finally:
            if con:
                con.close()

    # GET request
    return render_template('signup.html')



@app.route('/profile', methods=['GET','POST'])
def profile():
    if 'username' not in session:
        return render_template('home.html')
    

    if 'username' in session:
        connection = sqlite3.connect('mixmuse_users.db')
        cursor = connection.cursor()

        username = session['username']
        website_user = session['website_user']
        query = "SELECT * from users where username = '"+username+"' "
        cursor.execute(query)

        user_data = cursor.fetchone()

        if request.method == 'POST':
            fullname = request.form['name']
            username = request.form["user"]
            password = request.form["password"]
            email = request.form["email"]
            phonenumber = request.form["phone"]
            gender = request.form["gender"]
            address = request.form["address"]
            skills = request.form["skills"]
            experience = request.form["exp"]

            query = "UPDATE users SET fullname = ?, username = ?, email = ?, phoneno = ?, password = ?, address = ?, skills = ?, experience = ?, gender = ? WHERE username = ?"
            cursor.execute(query,(fullname, username, email, phonenumber, password,address,skills,experience, gender, username))
            connection.commit()

            query = "SELECT * from users where username = '"+username+"' "
            cursor.execute(query)
            user_data = cursor.fetchone()

            session['username'] = username

            return render_template('profile.html', user_data=user_data,website_user=website_user)
        
        return render_template('profile.html', user_data=user_data,website_user=website_user)
    else:
        return render_template('profile.html')
    




@app.route('/api/jobs/<int:id>', methods=['DELETE'])
def delete_job(id):
    conn = sqlite3.connect('mixmuse_users.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM accepted_applicants WHERE job_id=?",(id,))
        cursor.execute("DELETE FROM applicants WHERE job_id=?", (id,))
        cursor.execute("DELETE FROM posts WHERE id=?", (id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            return jsonify({"error": "Job not found"}), 404  # Job not found
        return jsonify({"message": "Job deleted successfully"}), 200  # Successful deletion
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500  # Internal server error
    finally:
        conn.close() 

    
@app.route('/emphome')
def emphome():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    posts = []

    connection = sqlite3.connect('mixmuse_users.db')
    cursor = connection.cursor()


    query = "SELECT * FROM users WHERE username = ?"
    cursor.execute(query, (username,))
    user_data = cursor.fetchone()
    

    # if website_user == 'employer':
        
    # Fetch job posts for the logged-in employer
    posts = cursor.execute('SELECT * FROM posts WHERE username = ?',(username,)).fetchall()

    connection.close()
    return render_template('EmpHomePage.html', name=username, user_data=user_data, posts=posts)

    # else:
    return render_template('EmpHomePage.html',name=username,user_data=user_data)





# def get_jobs():    # Connect to your database    conn = sqlite3.connect('mixmuse_users.db')
#     conn = sqlite3.connect('mixmuse_users.db')
#     cursor = conn.cursor()

#     username = session['username']
#         # Fetch jobs from the posts table
#     cursor.execute("SELECT * FROM posts WHERE username = ?",(username,))
#     jobs = cursor.fetchall()

#         # Close the connection
#     conn.close()

#     # Format the jobs into a list of dictionaries
#     job_list = []
#     for job in jobs:
#         job_list.append({
#             'title': job[1],
#             'company_name': job[2],
#             'company_address': job[3],
#             'job_type': job[4],
#             'salary': job[5],
#             'duration': job[6],
#             'open_positions': job[7],
#             'requirements': job[8],
#             'job_description': job[9],
#             'employee_responsibilities': job[10],
#             'what_your_company_offers': job[11]
#         })

#     return job_list





@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    
        connection = sqlite3.connect('mixmuse_users.db')
        cursor = connection.cursor()
        
        
        username = session['username']

        # Fetch all job posts
        cursor.execute("SELECT id, job_title, company_name, open_positions,job_description FROM posts WHERE username = ?",(username,))
        jobs = cursor.fetchall()

        connection.close()

        # Convert jobs to a list of dictionaries
        job_list = []
        for job in jobs:
            job_list.append({
                'id': job[0],
                'title': job[1],
                'company_name': job[2],
                'open_positions': job[3],
                'job_description':job[4]
            })

        return jsonify(job_list)

# @app.route('/api/acceptedApplicantsCount/<int:job_id>', methods=['GET'])
# def get_accepted_applicants_count(job_id):
#     connection = sqlite3.connect('mixmuse_users.db')
#     cursor = connection.cursor()
#     cursor.execute('SELECT COUNT(*) AS count FROM accepted_applicants WHERE job_id = ?', (job_id,))
#     count = cursor.fetchone()[0]
#     return jsonify({'count': count})

# @app.route('/api/updateOpenPositions', methods=['POST'])
# def update_open_positions():

#     data = request.json
#     job_id = data['jobId']
#     new_open_positions = data['newOpenPositions']
#     connection = sqlite3.connect('mixmuse_users.db')
#     cursor = connection.cursor()
#     cursor.execute('UPDATE posts SET open_positions = ? WHERE id = ?', (new_open_positions, job_id))
#     connection.commit()
    
#     return jsonify({'message': 'Open positions updated successfully'})


@app.route('/api/alljobs', methods=['GET'])
def get_alljobs():
    
        connection = sqlite3.connect('mixmuse_users.db')
        cursor = connection.cursor()
        
        
        #username = session['username']

        # Fetch all job posts
        cursor.execute("SELECT id, job_title, company_name, open_positions,job_description FROM posts")
        jobs = cursor.fetchall()

        connection.close()

        # Convert jobs to a list of dictionaries
        job_list = []
        for job in jobs:
            job_list.append({
                'id': job[0],
                'title': job[1],
                'company_name': job[2],
                'open_positions': job[3],
                'job_description':job[4]
            })

        return jsonify(job_list)



@app.route('/posts',methods=['GET','POST'])
def posts():
    
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    posts = []

    connection = sqlite3.connect('mixmuse_users.db')
    cursor = connection.cursor()


    query = "SELECT * FROM users WHERE username = ?"
    cursor.execute(query, (username,))
    user_data = cursor.fetchone()
    

    # if website_user == 'employer':
        
    # Fetch job posts for the logged-in employer
    posts = cursor.execute('SELECT * FROM posts').fetchall()

    connection.close()
    return render_template('pexp.html', name=username, user_data=user_data, posts=posts)
    

    # if 'username' in session:
    #     connection = sqlite3.connect('mixmuse_users.db')
    #     cursor = connection.cursor()

    #     username = session['username']
    #     website_user = session['website_user']

    #     cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    #     user_data = cursor.fetchone()

    #     if website_user == 'artists':
    #         query_jobs = "SELECT * FROM posts ORDER BY id DESC"
    #         cursor.execute(query_jobs)
    #         jobs = cursor.fetchall()

    #         connection.close()
    #         return render_template('pexp.html',name=username, user_data=user_data, website_user=website_user,jobs=jobs)
        

        # else:
        #     return render_template('pexp.html')

        

@app.route('/postjob',methods=['GET','POST'])
def postjob():
    
    if 'username' in session:
        connection = sqlite3.connect('mixmuse_users.db')
        cursor = connection.cursor()

        username = session['username']
        query = "SELECT * from users where username = '"+username+"' "
        cursor.execute(query)

        user_data = cursor.fetchone()

    if request.method == 'POST':
        job_title = request.form['profession']
        company_name = request.form['company']
        company_addr = request.form['address']
        job_type = request.form['jobType']
        sal = request.form['salary']
        duration = request.form['duration']
        openPos = int(request.form['positions'])
        req = request.form['requirements']
        job_desc = request.form['description']
        job_resp = request.form['responsibilities']
        offers = request.form['offers']

        try:
            con = sqlite3.connect('mixmuse_users.db')
            c = con.cursor()
            c.execute(''' INSERT INTO posts (job_title, company_name, company_address, job_type, salary, duration, open_positions, requirements, job_description, employee_responsibilities, what_your_company_offers,username)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''',
                    (job_title, company_name, company_addr, job_type, sal, duration, openPos, req, job_desc, job_resp, offers,username))
            
            post_id = c.lastrowid
            con.commit()
            con.close()
            return render_template('EmpHomePage.html',post_id=post_id,user_data=user_data)

        except Exception as e:
            con.rollback()
            print("An error occurred:", e)
            return render_template('postjob.html', error="An error occurred while posting the job.", user_data=user_data)
        finally:
            con.close()

    return render_template('postjob.html',user_data=user_data)

@app.route('/requirments/<int:job_id>')
def requirments(job_id):
    connection = sqlite3.connect('mixmuse_users.db')
    cursor = connection.cursor()
    username = session['username']

    query = "SELECT * FROM users WHERE username = ?"
    cursor.execute(query, (username,))
    user_data = cursor.fetchone()

    # Fetch job details based on job_id
    cursor.execute("SELECT job_title, company_name, company_address,job_type, salary,duration,open_positions, requirements, job_description, employee_responsibilities, what_your_company_offers FROM posts WHERE id = ?", (job_id,))
    job = cursor.fetchone()

    cursor.execute('SELECT COUNT(*) FROM applicants WHERE username = ? AND job_id = ?', (username, job_id))
    already_applied = cursor.fetchone()[0] > 0

    connection.close()

    if job:
        job_details = {
            'id':job_id,
            'title': job[0],
            'company_name': job[1],
            'company_address': job[2],
            'job_type': job[3],
            'salary': job[4],
            'duration': job[5],
            'open_positions': job[6],
            'requirements': job[7],
            'job_description': job[8],
            'employee_responsibilities': job[9],
            'what_your_company_offers': job[10]
        }
        return render_template('reqexp.html', job=job_details,already_applied=already_applied,user_data=user_data)
    else:
        return "Job not found", 404


app.run(debug="True")



