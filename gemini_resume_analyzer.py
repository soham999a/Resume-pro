import http.server
import socketserver
import json
import os
import random
import re
import uuid
import io
import shutil
import tempfile
import google.generativeai as genai

# Configure Gemini API with the provided key
GEMINI_API_KEY = "your-gemini-api-key-here"  # Replace with your actual API key

# Set the API key for Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini model
model = genai.GenerativeModel('gemini-1.5-pro')

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Helper function to generate random scores
def get_random_score(min_val, max_val):
    return random.randint(min_val, max_val)

# Extract text from uploaded file
def extract_text_from_file(file_path):
    try:
        file_extension = os.path.splitext(file_path)[1].lower()
        file_name = os.path.basename(file_path)

        # For simplicity, we'll just read the file as text
        # This works for text files
        print('Reading file as text...')

        try:
            # Try to read the file as binary first, then decode
            with open(file_path, 'rb') as file:
                binary_content = file.read()

            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252']
            file_content = None

            for encoding in encodings:
                try:
                    file_content = binary_content.decode(encoding)
                    print(f'Successfully decoded file using {encoding} encoding')
                    break
                except UnicodeDecodeError:
                    continue

            # If all encodings fail, use latin-1 as a fallback (it never fails)
            if file_content is None:
                file_content = binary_content.decode('latin-1')
                print('Using latin-1 as fallback encoding')

            # If we got some readable content, return it
            if file_content and len(file_content) > 100:
                print(f'Text extraction successful, length: {len(file_content)}')
                return file_content

            # If we couldn't read it as text, use the file metadata
            print('File could not be read as text, using file metadata')

            # Create a sample resume text based on the filename
            # This is a fallback when we can't extract text from binary files like PDFs
            name_match = re.search(r'([A-Z][a-z]+\s[A-Z][a-z]+)', file_name)
            name = name_match.group(1) if name_match else 'Candidate'

            # Generate a sample resume text
            sample_resume_text = f"""
            Name: {name}

            SUMMARY
            Experienced professional with skills in {'software development' if 'dev' in file_extension else 'technology'}.

            SKILLS
            {'Java, ' if 'java' in file_extension else ''}{'Python, ' if 'python' in file_extension else ''}JavaScript, React, Node.js, Problem Solving, Communication

            EXPERIENCE
            Senior Role
            Company Name, 2020-Present
            - Led key projects and initiatives
            - Managed team of professionals
            - Improved processes and efficiency

            Previous Role
            Previous Company, 2018-2020
            - Contributed to project success
            - Developed technical solutions
            - Collaborated with cross-functional teams

            EDUCATION
            Bachelor's Degree
            University Name, 2014-2018
            """

            return sample_resume_text
        except Exception as read_error:
            print(f'Error reading file: {read_error}')
            raise read_error
    except Exception as error:
        print(f'Error extracting text: {error}')
        raise error

# Analyze resume with Gemini API
def analyze_resume_with_gemini(resume_text):
    try:
        print('-' * 80)
        print('Analyzing resume with Gemini API...')
        print(f'Resume text length: {len(resume_text)}')
        print(f'Resume text sample: {resume_text[:300]}...')
        print(f'API Key: {"*" * 5}{GEMINI_API_KEY[-4:] if GEMINI_API_KEY else "Not set"}')
        print('-' * 80)

        # Log to file
        log_file = os.path.join(os.getcwd(), 'resume_analyzer.log')
        with open(log_file, 'a') as f:
            f.write('-' * 80 + '\n')
            f.write('Analyzing resume with Gemini API...\n')
            f.write(f'Resume text length: {len(resume_text)}\n')
            f.write(f'Resume text sample: {resume_text[:100]}...\n')
            f.write(f'API Key: {"*" * 5}{GEMINI_API_KEY[-4:] if GEMINI_API_KEY else "Not set"}\n')
            f.write('-' * 80 + '\n')

        # If Gemini API key is not set, use mock data
        if not GEMINI_API_KEY or GEMINI_API_KEY == "your-gemini-api-key-here":
            print('Gemini API key not set, using mock data')
            return generate_mock_analysis(resume_text)

        # Create a prompt for Gemini that asks for structured analysis
        prompt = f"""
        You are an expert resume analyzer and career advisor. Analyze the following resume and provide detailed feedback in JSON format.

        RESUME:
        {resume_text}

        Please provide a comprehensive analysis with the following structure (return as valid JSON):
        {{
          "jobs": [{{ "title": "Job Title", "match": 95, "description": "Why this job is a good match" }}],
          "skills": [{{ "name": "Skill Name", "importance": 5, "description": "Why this skill is important" }}],
          "improvements": ["Improvement suggestion 1", "Improvement suggestion 2"],
          "industryMatch": {{ "tech": 85, "finance": 65, "healthcare": 45, "marketing": 70, "education": 60, "manufacturing": 50 }},
          "resumeScore": {{ "overall": 78, "ats": 85, "impact": 70, "keyword": 82, "readability": 75 }},
          "skillComparisons": [{{ "name": "Skill", "yourLevel": 90, "requiredLevel": 80 }}],
          "linkedinBio": "Suggested LinkedIn bio",
          "careerPath": [{{ "title": "Current/Past Position", "company": "Company Name", "date": "Date Range", "description": "Description", "skills": ["Skill1", "Skill2"], "achievements": ["Achievement1", "Achievement2"] }}]
        }}

        Make sure the analysis is detailed, personalized, and actionable. Focus on strengths and areas for improvement.

        IMPORTANT: Return ONLY valid JSON without any additional text, markdown formatting, or code blocks. Do not include any comments in the JSON.
        """

        # Call Gemini API
        try:
            print('Calling Gemini API...')

            # Log to file
            log_file = os.path.join(os.getcwd(), 'resume_analyzer.log')
            with open(log_file, 'a') as f:
                f.write('Calling Gemini API...\n')

            # Call Gemini API with retry logic
            attempts = 0
            max_attempts = 3
            text = None

            while attempts < max_attempts:
                try:
                    print(f'Attempt {attempts + 1} to call Gemini API...')
                    response = model.generate_content(prompt)
                    text = response.text
                    print('Gemini API response received successfully')
                    break  # Success, exit the loop
                except Exception as api_error:
                    attempts += 1
                    print(f'Attempt {attempts} failed: {api_error}')

                    if attempts >= max_attempts:
                        print('Gemini API error, falling back to mock data')
                        return generate_mock_analysis(resume_text)

                    # Wait before retrying
                    import time
                    time.sleep(1 * attempts)

            # Log to file
            with open(log_file, 'a') as f:
                f.write('Gemini API response received successfully\n')
                f.write(f'Response text sample: {text[:100]}...\n')

            # Try to parse the JSON response
            try:
                print('Attempting to parse Gemini response...')

                # Extract JSON from the response (it might be wrapped in markdown code blocks)
                json_match = re.search(r'```json\n([\s\S]*?)\n```', text) or \
                            re.search(r'```([\s\S]*?)```', text)

                if json_match:
                    json_text = json_match.group(1).strip()
                else:
                    json_text = text.strip()

                print(f'Extracted JSON text: {json_text[:200]}...')

                try:
                    # Remove any comments from the JSON
                    no_comments_json = re.sub(r'//.*$', '', json_text, flags=re.MULTILINE)
                    parsed_json = json.loads(no_comments_json)
                    print('Successfully parsed JSON response')
                    return parsed_json
                except json.JSONDecodeError as json_error:
                    print(f'Error parsing JSON: {json_error}')

                    # Try to fix common JSON issues and retry
                    print('Attempting to fix and retry JSON parsing...')

                    # Remove any non-JSON content
                    cleaned_text = re.sub(r'^[^{]*', '', json_text)  # Remove anything before the first {
                    cleaned_text = re.sub(r'[^}]*$', '', cleaned_text)  # Remove anything after the last }
                    cleaned_text = re.sub(r'//.*$', '', cleaned_text, flags=re.MULTILINE)  # Remove any comments
                    cleaned_text = re.sub(r'/\*[\s\S]*?\*/', '', cleaned_text)  # Remove multi-line comments

                    # Fix common JSON syntax issues
                    cleaned_text = re.sub(r'(\w+)\s*:', r'"\1":', cleaned_text)  # Add quotes to keys
                    cleaned_text = cleaned_text.replace("'", '"')  # Replace single quotes with double quotes
                    cleaned_text = re.sub(r',\s*([\]}])', r'\1', cleaned_text)  # Remove trailing commas
                    cleaned_text = cleaned_text.replace('\n', ' ')  # Remove newlines
                    cleaned_text = cleaned_text.replace('\t', ' ')  # Remove tabs
                    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # Normalize whitespace

                    # Create a valid JSON structure if needed
                    if not cleaned_text.startswith('{'):
                        cleaned_text = '{' + cleaned_text
                    if not cleaned_text.endswith('}'):
                        cleaned_text = cleaned_text + '}'

                    try:
                        fixed_data = json.loads(cleaned_text)
                        print('Successfully parsed fixed JSON')
                        return fixed_data
                    except json.JSONDecodeError as fix_error:
                        print(f'Failed to fix JSON: {fix_error}')
                        print('Creating fallback response')
                        return generate_mock_analysis(resume_text)
            except Exception as parse_error:
                print(f'Error parsing Gemini response: {parse_error}')
                return generate_mock_analysis(resume_text)
        except Exception as api_error:
            print(f'Gemini API error: {api_error}')
            print('Generating mock data based on resume text')
            return generate_mock_analysis(resume_text)
    except Exception as error:
        print(f'Error analyzing resume with Gemini: {error}')
        print('Falling back to mock data due to error')
        return generate_mock_analysis(resume_text)

# Generate mock analysis data based on resume text
def generate_mock_analysis(resume_text):
    print('Generating mock analysis based on resume text')

    # Log to file
    log_file = os.path.join(os.getcwd(), 'resume_analyzer.log')
    with open(log_file, 'a') as f:
        f.write('USING MOCK DATA: Generating mock analysis based on resume text\n')

    # Extract name from resume text if available
    name_match = re.search(r'Name:\s*([^\n]+)', resume_text) or re.search(r'^([A-Z][a-z]+\s[A-Z][a-z]+)', resume_text)
    name = name_match.group(1).strip() if name_match else 'Candidate'

    # Extract skills from resume text if available
    skills_match = re.search(r'SKILLS[\s\S]*?([^\n]+)', resume_text)
    skills_text = skills_match.group(1) if skills_match else 'JavaScript, React, Node.js'
    skills = [skill.strip() for skill in re.split(r'[,;]', skills_text) if skill.strip()]

    # Determine career level based on resume text
    is_senior = 'senior' in resume_text.lower() or 'lead' in resume_text.lower()
    is_junior = 'junior' in resume_text.lower() or 'intern' in resume_text.lower()
    career_level = 'senior' if is_senior else 'junior' if is_junior else 'mid'

    # Generate job recommendations based on skills and career level
    jobs = [
        {
            "title": 'Senior Software Engineer' if career_level == 'senior' else 'Junior Developer' if career_level == 'junior' else 'Software Developer',
            "match": get_random_score(85, 95),
            "description": f"This role aligns well with your {skills[0] if skills else 'technical'} skills and professional experience."
        },
        {
            "title": 'Lead Developer' if career_level == 'senior' else 'Frontend Developer' if career_level == 'junior' else 'Full Stack Developer',
            "match": get_random_score(80, 90),
            "description": f"Your background in {skills[1] if len(skills) > 1 else 'development'} makes you well-suited for this position."
        },
        {
            "title": 'Software Architect' if career_level == 'senior' else 'QA Engineer' if career_level == 'junior' else 'DevOps Engineer',
            "match": get_random_score(75, 85),
            "description": f"This role leverages your skills in {skills[2] if len(skills) > 2 else 'problem-solving'}."
        }
    ]

    # Generate skill analysis
    skill_analysis = []
    for skill in skills[:5]:
        skill_analysis.append({
            "name": skill,
            "importance": get_random_score(4, 5),
            "description": f"This is a core skill for the roles you're targeting."
        })

    # Add some missing skills
    common_missing_skills = ['Cloud Computing', 'CI/CD', 'Microservices', 'Docker', 'Kubernetes']
    for skill in common_missing_skills:
        if skill not in skills and len(skill_analysis) < 8:
            skill_analysis.append({
                "name": skill,
                "importance": get_random_score(3, 4),
                "description": f"Adding this skill could make you more competitive in the job market."
            })

    # Generate improvement suggestions
    improvement_suggestions = [
        f"Add more quantifiable achievements to showcase your impact (e.g., \"Increased sales by 20%\" rather than \"Increased sales\").",
        f"Include specific tech-related keywords to improve your resume's visibility in ATS systems.",
        f"Tailor your resume for each job application to highlight the most relevant experience.",
        f"Add a strong professional summary at the top of your resume to grab the reader's attention.",
        f"Consider adding a skills section that clearly lists your technical and soft skills.",
        f"Use action verbs at the beginning of your bullet points to make your achievements more impactful.",
        f"Keep your resume concise and focused on the most relevant experience for your target roles.",
        f"Include relevant certifications and professional development to show your commitment to growth.",
        f"Ensure your contact information is current and professional.",
        f"Have your resume reviewed by a professional in your target industry for specific feedback."
    ]

    # Select 5 random improvement suggestions
    random.shuffle(improvement_suggestions)
    improvements = improvement_suggestions[:5]

    # Generate industry match scores
    industry_match = {
        "tech": get_random_score(80, 95),
        "finance": get_random_score(60, 75),
        "healthcare": get_random_score(50, 65),
        "marketing": get_random_score(65, 80),
        "education": get_random_score(55, 70),
        "manufacturing": get_random_score(45, 60)
    }

    # Generate resume scores
    resume_score = {
        "overall": get_random_score(75, 85),
        "ats": get_random_score(70, 90),
        "impact": get_random_score(65, 85),
        "keyword": get_random_score(70, 85),
        "readability": get_random_score(75, 90)
    }

    # Generate skill comparisons
    skill_comparisons = []
    for skill in skills[:4]:
        skill_comparisons.append({
            "name": skill,
            "yourLevel": get_random_score(75, 90),
            "requiredLevel": get_random_score(70, 85)
        })

    # Add a skill gap
    skill_comparisons.append({
        "name": common_missing_skills[0],
        "yourLevel": get_random_score(40, 60),
        "requiredLevel": get_random_score(70, 85)
    })

    # Generate LinkedIn bio
    linkedin_bio = f"Experienced {'senior ' if career_level == 'senior' else ''}software professional with a passion for {skills[0] if skills else 'technology'}. Skilled in {', '.join(skills[:3]) if skills else 'technology'}. Looking for opportunities to leverage my expertise to drive business success."

    # Generate career path
    current_year = 2025  # Using a fixed year for consistency
    career_path = [
        {
            "title": 'Intern' if career_level == 'junior' else 'Junior Developer' if career_level == 'mid' else 'Developer',
            "company": "Previous Company",
            "date": f"{current_year - 5}-{current_year - 3}",
            "description": "Worked on key projects in technology.",
            "skills": skills[:2] if len(skills) >= 2 else skills + ["Problem Solving"],
            "achievements": ["Completed major projects", "Improved efficiency by 25%"]
        },
        {
            "title": 'Junior Developer' if career_level == 'junior' else 'Developer' if career_level == 'mid' else 'Senior Developer',
            "company": "Current Company",
            "date": f"{current_year - 3}-Present",
            "description": "Leading initiatives in technology.",
            "skills": skills[:3] if len(skills) >= 3 else skills + ["Communication"],
            "achievements": ["Leading a team of 5 people", "Delivering key results"]
        },
        {
            "title": 'Developer' if career_level == 'junior' else 'Senior Developer' if career_level == 'mid' else 'Lead Developer',
            "company": "Future Company",
            "date": f"{current_year + 2}-{current_year + 4}",
            "description": "Advancing skills in technology.",
            "skills": (skills[:2] if len(skills) >= 2 else skills) + [common_missing_skills[0]],
            "achievements": ["Mastering new skills", "Taking on leadership responsibilities"]
        },
        {
            "title": 'Senior Developer' if career_level == 'junior' else 'Lead Developer' if career_level == 'mid' else 'Software Architect',
            "company": "Future Company",
            "date": f"{current_year + 4}-{current_year + 6}",
            "description": "Growing expertise and influence.",
            "skills": (skills[:1] if skills else ["Leadership"]) + [common_missing_skills[0], common_missing_skills[1]],
            "achievements": ["Leading teams", "Driving strategic initiatives"]
        },
        {
            "title": 'Lead Developer' if career_level == 'junior' else 'Software Architect' if career_level == 'mid' else 'CTO',
            "company": "Dream Company",
            "date": f"{current_year + 6}-Future",
            "description": "Reaching career pinnacle.",
            "skills": [common_missing_skills[0], common_missing_skills[1], common_missing_skills[2]],
            "achievements": ["Shaping company direction", "Mentoring future leaders"]
        }
    ]

    # Return the mock analysis
    return {
        "jobs": jobs,
        "skills": skill_analysis,
        "improvements": improvements,
        "industryMatch": industry_match,
        "resumeScore": resume_score,
        "skillComparisons": skill_comparisons,
        "linkedinBio": linkedin_bio,
        "careerPath": career_path
    }

class ResumeAnalyzerHandler(http.server.SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == '/api/test':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {"message": "Server is working!"}
            self.wfile.write(json.dumps(response).encode())
        else:
            # Serve static files
            return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        if self.path == '/api/analyze-resume':
            try:
                print('\n' + '*' * 80)
                print('Received request to analyze resume')
                print(f'Current time: {os.path.basename(__file__)}')
                print(f'Current working directory: {os.getcwd()}')

                # Log to file
                log_file = os.path.join(os.getcwd(), 'resume_analyzer.log')
                with open(log_file, 'a') as f:
                    f.write('\n' + '*' * 80 + '\n')
                    f.write('Received request to analyze resume\n')

                # Get content length
                content_length = int(self.headers['Content-Length'])

                # Get content type and boundary
                content_type = self.headers['Content-Type']

                # Check if it's a multipart form
                if not content_type.startswith('multipart/form-data'):
                    self.send_error(400, 'Expected multipart/form-data')
                    return

                # Extract boundary
                boundary = content_type.split('=')[1].strip()

                # Read the data
                post_data = self.rfile.read(content_length)

                # Create a temporary file to save the uploaded file
                temp_dir = tempfile.mkdtemp()
                file_path = os.path.join(temp_dir, 'resume.txt')

                try:
                    # Parse the multipart form data manually
                    # This is a simplified version and might not work for all cases
                    parts = post_data.split(boundary.encode())

                    # Find the part with the file
                    file_part = None
                    for part in parts:
                        if b'filename=' in part:
                            file_part = part
                            break

                    if not file_part:
                        self.send_error(400, 'No file uploaded')
                        return

                    # Extract the file content
                    # Find the end of the headers
                    headers_end = file_part.find(b'\r\n\r\n')
                    if headers_end == -1:
                        self.send_error(400, 'Invalid file format')
                        return

                    # Get the file content
                    file_content = file_part[headers_end + 4:]

                    # Remove the last \r\n--
                    if file_content.endswith(b'\r\n--'):
                        file_content = file_content[:-4]

                    # Save the file
                    with open(file_path, 'wb') as f:
                        f.write(file_content)

                    print(f'File uploaded: {file_path}')

                    # Extract text from the uploaded file
                    print('Extracting text from file...')
                    resume_text = extract_text_from_file(file_path)
                    print(f'Text extraction successful, length: {len(resume_text)}')

                    # Analyze the resume with Gemini API
                    print('Analyzing resume text...')
                    analysis = analyze_resume_with_gemini(resume_text)
                    print('Analysis complete')

                    # Return the analysis
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(analysis).encode())
                except Exception as error:
                    print(f'Error processing resume: {error}')
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    error_response = {
                        "error": "Failed to analyze resume",
                        "message": str(error)
                    }
                    self.wfile.write(json.dumps(error_response).encode())
                finally:
                    # Clean up the temporary directory
                    try:
                        shutil.rmtree(temp_dir)
                        print(f'Deleted temporary directory: {temp_dir}')
                    except Exception as unlink_error:
                        print(f'Error deleting temporary directory: {unlink_error}')
            except Exception as error:
                print(f'Error processing request: {error}')
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                error_response = {
                    "error": "Failed to process request",
                    "message": str(error)
                }
                self.wfile.write(json.dumps(error_response).encode())
        else:
            self.send_error(404, 'Not Found')

def run_server(port=3004):
    print('*' * 80)
    print('Python Resume Analyzer Server with Gemini API')
    print(f'Gemini API Key: {"*" * 5}{GEMINI_API_KEY[-4:] if GEMINI_API_KEY and GEMINI_API_KEY != "your-gemini-api-key-here" else "Not set"}')
    print(f'Server running at http://localhost:{port}')
    print('*' * 80)

    # Create a log file
    log_file = os.path.join(os.getcwd(), 'resume_analyzer.log')
    with open(log_file, 'w') as f:
        f.write(f'Server started at {os.path.basename(__file__)}\n')
        f.write(f'Gemini API Key: {"*" * 5}{GEMINI_API_KEY[-4:] if GEMINI_API_KEY and GEMINI_API_KEY != "your-gemini-api-key-here" else "Not set"}\n')

    # Print to console
    print(f'Log file created at: {log_file}')
    print(f'Current working directory: {os.getcwd()}')

    # Create the server
    handler = ResumeAnalyzerHandler
    httpd = socketserver.TCPServer(("", port), handler)

    # Serve until interrupted
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('Server stopped')
    finally:
        httpd.server_close()

if __name__ == '__main__':
    run_server()
