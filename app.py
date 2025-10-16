import streamlit as st # type: ignore
from huggingface_hub import InferenceClient # type: ignore
from huggingface_hub.utils import HfHubHTTPError # type: ignore
from pymongo import MongoClient # type: ignore
import hashlib
from datetime import datetime
import json
import re
import requests # type: ignore
from bs4 import BeautifulSoup # type: ignore
import pdfkit # type: ignore
import base64

# --- Configuration ---
st.set_page_config(
    page_title="Portfolio Maker - AI Resume Builder",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Professional UI ---
st.markdown("""
<style>
    .main {
        background-color: black;
    }
    
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 0 0 20px 20px;
        margin-bottom: 2rem;
        margin-top: -4rem;
        color: white;
    }
    
    .custom-card {
        background: black;
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    
    .custom-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
    }
    
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    
    .section-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .skill-tag {
        background: #e3f2fd;
        color: #1976d2;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        margin: 0.2rem;
        display: inline-block;
        font-size: 0.9rem;
    }
    
    .achievement-badge {
        background: #f3e5f5;
        color: #7b1fa2;
        padding: 0.5rem 1rem;
        border-radius: 10px;
        margin: 0.5rem;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# --- MongoDB Connection ---
@st.cache_resource
def get_mongo_client():
    """Establishes a connection to MongoDB and returns the collection object."""
    try:
        MONGO_URI = st.secrets["MONGO_URI"]
        DB_NAME = st.secrets["DB_NAME"]
        COLLECTION_NAME = st.secrets["COLLECTION_NAME"]
        client = MongoClient(MONGO_URI)
        return client[DB_NAME][COLLECTION_NAME]
    except Exception as e:
        st.error(f"Failed to connect to MongoDB: {e}")
        st.stop()

users_collection = get_mongo_client()

def hash_password(password):
    """Hashes a password for storing."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password, provided_password):
    """Verifies a provided password against a stored hash."""
    return stored_password == hash_password(provided_password)

# Hugging Face token
try:
    HF_TOKEN = st.secrets["HF_TOKEN"]
except FileNotFoundError:
    st.error("Streamlit secrets file not found. Please create a .streamlit/secrets.toml file with your HF_TOKEN.")
    st.stop()

# Using a powerful non-gated model like Gemma to avoid 401 Unauthorized errors
# that occur with gated models (e.g., Llama 3, Mistral) if terms haven't been accepted.
client = InferenceClient("meta-llama/Meta-Llama-3-8B-Instruct", token=HF_TOKEN)

# --- System Prompts for Portfolio Generation ---
PORTFOLIO_PROMPTS = {
    "resume_writer": """You are an expert resume writer and career coach. Your task is to create professional, ATS-friendly resumes that highlight the user's strengths and achievements.

Key guidelines:
- Use industry-standard resume formatting
- Focus on quantifiable achievements and results
- Use action verbs and professional language
- Tailor content to the user's target industry
- Ensure ATS (Applicant Tracking System) compatibility
- Highlight relevant skills and certifications
- Keep it concise and impactful

User Profile:
{user_data}

Target Position: {target_position}

Generate a professional resume in markdown format with the following sections:
1. Professional Summary
2. Technical Skills
3. Work Experience (with bullet points emphasizing achievements)
4. Education
5. Projects
6. Certifications
7. Additional Sections (if relevant)""",

    "cover_letter": """You are an expert cover letter writer. Create a compelling, personalized cover letter that complements the resume.

Key guidelines:
- Address the hiring manager professionally
- Connect the user's skills to the job requirements
- Show enthusiasm and cultural fit
- Include specific examples and achievements
- Keep it to one page
- Use professional but engaging tone

User Profile:
{user_data}

Target Position: {target_position}
Company: {company_name}
Job Description: {job_description}

Generate a professional cover letter in markdown format.""",

    "portfolio_analyzer": """You are a portfolio analysis expert. Analyze the user's provided links and information to extract key skills, achievements, and project details.

Extract and organize:
1. Technical skills and proficiency levels
2. Key projects with descriptions and technologies used
3. Professional achievements and metrics
4. Education and certifications
5. Work experience details
6. Specialized knowledge areas

User Information:
{user_data}

Provided Links:
{links}

Provide a comprehensive analysis in JSON format for resume generation.""",

    "skill_enhancer": """You are a career development expert. Enhance and professionalize the user's skill descriptions and achievements.

Transform basic descriptions into professional, impactful statements:
- Use industry-standard terminology
- Add quantifiable metrics where possible
- Focus on results and impact
- Use action-oriented language

Original Content:
{original_content}

Enhanced Version:"""
}

# --- Utility Functions ---
def extract_linkedin_info(profile_url):
    """Extract basic information from LinkedIn profile (simulated - in production use LinkedIn API)"""
    try:
        # Note: This is a simplified simulation. Real implementation would require LinkedIn API
        st.info("🔍 Simulating LinkedIn profile analysis... (In production, this would use LinkedIn API)")
        
        # Simulated response based on common patterns
        simulated_data = {
            "skills": ["Python", "Machine Learning", "Data Analysis", "SQL", "Project Management"],
            "experience": "3+ years in software development",
            "education": "Bachelor's in Computer Science",
            "certifications": ["AWS Certified", "Google Data Analytics"],
            "summary": "Experienced professional with strong technical background"
        }
        
        return simulated_data
    except Exception as e:
        st.error(f"Error analyzing LinkedIn profile: {e}")
        return None

def analyze_github_profile(profile_url):
    """Analyze GitHub profile for projects and skills"""
    try:
        st.info("🔍 Analyzing GitHub profile...")
        # Simulated GitHub analysis
        simulated_data = {
            "programming_languages": ["Python", "JavaScript", "Java"],
            "projects": ["Machine Learning Portfolio", "Web Application", "Data Analysis Tool"],
            "technologies": ["React", "Node.js", "MongoDB", "TensorFlow"],
            "activity": "Active contributor with multiple repositories"
        }
        return simulated_data
    except Exception as e:
        st.error(f"Error analyzing GitHub profile: {e}")
        return None

@st.cache_data(show_spinner=False)
def generate_ai_response(system_prompt, user_prompt):
    """Generate AI response for portfolio content"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    response_text = ""
    try:
        for chunk in client.chat_completion(messages, max_tokens=2048, temperature=0.7, stream=True):
            if chunk.choices and chunk.choices[0].delta.content:
                response_text += chunk.choices[0].delta.content
    except HfHubHTTPError as e:
        if e.response.status_code == 402:
            st.error("Monthly usage limit reached. Please try again later.")
            return "Service temporarily unavailable."
        st.error(f"AI service error: {e}")
        return "Unable to generate content at this time."
    except Exception as e:
        st.error(f"Error: {e}")
        return "Content generation failed."

    return response_text.strip()

def create_download_link(content, filename, file_type="text/plain"):
    """Create a download link for generated content"""
    b64 = base64.b64encode(content.encode()).decode()
    return f'<a href="data:{file_type};base64,{b64}" download="{filename}">Download {filename}</a>'

# --- UI Components ---
def display_professional_header():
    """Display professional header"""
    st.markdown("""
    <div class="header-container">
        <h1 style="margin:0; font-size: 2.5rem; font-weight: 300;">Portfolio Maker</h1>
        <p style="margin:0; font-size: 1.1rem; opacity: 0.9;">AI-Powered Resume & Portfolio Builder</p>
    </div>
    """, unsafe_allow_html=True)

def display_input_forms():
    """Display comprehensive input forms for user data"""
    st.markdown("### 📝 Personal Information")
    
    with st.form("portfolio_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            full_name = st.text_input("Full Name*", placeholder="John Doe")
            email = st.text_input("Email*", placeholder="john.doe@email.com")
            phone = st.text_input("Phone", placeholder="+1 (555) 123-4567")
            location = st.text_input("Location", placeholder="City, State")
            
        with col2:
            linkedin_url = st.text_input("LinkedIn Profile URL", placeholder="https://linkedin.com/in/username")
            github_url = st.text_input("GitHub Profile URL", placeholder="https://github.com/username")
            portfolio_url = st.text_input("Personal Portfolio URL", placeholder="https://yourportfolio.com")
            
        st.markdown("---")
        st.markdown("### 🎯 Career Objectives")
        
        target_position = st.text_input("Target Position*", placeholder="Software Engineer, Data Scientist, etc.")
        target_industry = st.selectbox("Target Industry", [
            "Technology", "Healthcare", "Finance", "Education", 
            "Marketing", "Engineering", "Design", "Other"
        ])
        experience_level = st.selectbox("Experience Level", [
            "Entry Level", "Junior", "Mid-Level", "Senior", "Executive"
        ])
        
        st.markdown("### 💼 Work Experience")
        with st.expander("Add Work Experience", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                company = st.text_input("Company Name", placeholder="Tech Company Inc.")
                job_title = st.text_input("Job Title", placeholder="Software Developer")
                start_date = st.date_input("Start Date")
                
            with col2:
                location = st.text_input("Location", placeholder="Remote / City, State")
                end_date = st.date_input("End Date")
                current_job = st.checkbox("I currently work here")
                
            responsibilities = st.text_area("Responsibilities & Achievements", 
                                          placeholder="• Developed and maintained web applications...\n• Improved system performance by 30%...\n• Led a team of 3 developers...",
                                          height=100)
            
        st.markdown("---")
        st.markdown("### 🎓 Education")
        
        col1, col2 = st.columns(2)
        with col1:
            institution = st.text_input("Institution*", placeholder="University Name")
            degree = st.text_input("Degree*", placeholder="Bachelor of Science in Computer Science")
            
        with col2:
            graduation_date = st.date_input("Graduation Date")
            gpa = st.text_input("GPA", placeholder="3.8/4.0")
            
        st.markdown("---")
        st.markdown("### 🛠️ Skills & Technologies")
        
        st.markdown("**Technical Skills**")
        technical_skills = st.text_area("List your technical skills (comma-separated)", 
                                      placeholder="Python, JavaScript, React, SQL, Machine Learning, AWS...",
                                      height=80)
        
        st.markdown("**Soft Skills**")
        soft_skills = st.text_area("List your soft skills (comma-separated)",
                                 placeholder="Leadership, Communication, Problem Solving, Teamwork...",
                                 height=80)
        
        st.markdown("---")
        st.markdown("### 🚀 Projects")
        
        with st.expander("Add Project Details"):
            project_title = st.text_input("Project Title", placeholder="Machine Learning Fraud Detection")
            project_description = st.text_area("Project Description", 
                                            placeholder="Developed a machine learning model to detect fraudulent transactions with 95% accuracy...",
                                            height=100)
            project_technologies = st.text_input("Technologies Used", placeholder="Python, Scikit-learn, Pandas, Flask")
            project_link = st.text_input("Project Link (optional)", placeholder="https://github.com/username/project")
        
        st.markdown("---")
        st.markdown("### 📜 Certifications")
        
        certifications = st.text_area("Certifications (one per line)", 
                                   placeholder="AWS Certified Solutions Architect\nGoogle Data Analytics Professional Certificate\n...",
                                   height=80)
        
        submitted = st.form_submit_button("✅ Save and Continue")
        
        if submitted:
            if not full_name or not email or not target_position:
                st.error("Please fill in all required fields (marked with *)")
            else:
                user_data = {
                    "personal_info": {
                        "full_name": full_name,
                        "email": email,
                        "phone": phone,
                        "location": location,
                        "linkedin": linkedin_url,
                        "github": github_url,
                        "portfolio": portfolio_url
                    },
                    "career_goals": {
                        "target_position": target_position,
                        "target_industry": target_industry,
                        "experience_level": experience_level
                    },
                    "work_experience": {
                        "company": company,
                        "job_title": job_title,
                        "start_date": start_date.strftime("%Y-%m") if start_date else "",
                        "end_date": end_date.strftime("%Y-%m") if end_date else "",
                        "current_job": current_job,
                        "responsibilities": responsibilities
                    },
                    "education": {
                        "institution": institution,
                        "degree": degree,
                        "graduation_date": graduation_date.strftime("%Y-%m") if graduation_date else "",
                        "gpa": gpa
                    },
                    "skills": {
                        "technical": [skill.strip() for skill in technical_skills.split(",") if skill.strip()],
                        "soft": [skill.strip() for skill in soft_skills.split(",") if skill.strip()]
                    },
                    "projects": {
                        "title": project_title,
                        "description": project_description,
                        "technologies": project_technologies,
                        "link": project_link
                    },
                    "certifications": [cert.strip() for cert in certifications.split("\n") if cert.strip()]
                }
                
                # Analyze provided links
                links_data = {}
                if linkedin_url:
                    links_data["linkedin"] = extract_linkedin_info(linkedin_url)
                if github_url:
                    links_data["github"] = analyze_github_profile(github_url)
                
                return user_data, links_data, True # Return True on successful submission

    return None, None, False

def display_resume_generator(user_data, links_data):
    """Display resume generation interface"""
    st.markdown("### 📄 AI Resume Generator")
    
    col1, col2 = st.columns(2)
    
    with col1:
        resume_style = st.selectbox("Resume Style", 
                                  ["Modern Professional", "Creative", "Minimalist", "ATS-Optimized"])
        include_summary = st.checkbox("Include Professional Summary", value=True)
        include_skills = st.checkbox("Include Skills Section", value=True)
        include_projects = st.checkbox("Include Projects", value=True)
        
    with col2:
        target_company = st.text_input("Target Company (optional)", placeholder="Google, Amazon, etc.")
        job_description = st.text_area("Paste Job Description (optional)", 
                                     placeholder="Paste the job description here for customization...",
                                     height=100)
    
    if st.button("✨ Generate Professional Resume", use_container_width=True):
        with st.spinner("Crafting your professional resume..."):
            # Prepare user data for AI
            user_data_str = json.dumps(user_data, indent=2)
            
            # Generate resume
            resume_prompt = f"""
            User Data: {user_data_str}
            Links Data: {links_data}
            Resume Style: {resume_style}
            Target Company: {target_company}
            Job Description: {job_description}
            """
            
            resume_content = generate_ai_response(
                PORTFOLIO_PROMPTS["resume_writer"], 
                resume_prompt
            )
            
            # Display generated resume
            st.markdown("---")
            st.markdown("### 🎉 Your Generated Resume")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(resume_content)
            
            with col2:
                st.markdown("### 📥 Download Options")
                
                # Create download links
                download_md = create_download_link(resume_content, "resume.md", "text/markdown")
                download_txt = create_download_link(resume_content, "resume.txt", "text/plain")
                
                st.markdown(download_md, unsafe_allow_html=True)
                st.markdown(download_txt, unsafe_allow_html=True)
                
                st.info("💡 **Pro Tip:** Copy the markdown content to a .md file for easy formatting")

def display_cover_letter_generator(user_data):
    """Display cover letter generator"""
    st.markdown("### 💌 AI Cover Letter Generator")
    
    col1, col2 = st.columns(2)
    
    with col1:
        company_name = st.text_input("Company Name*", placeholder="Tech Innovations Inc.")
        hiring_manager = st.text_input("Hiring Manager Name (optional)", placeholder="Jane Smith")
        job_title = st.text_input("Job Title*", placeholder="Senior Software Engineer")
        
    with col2:
        tone_style = st.selectbox("Tone Style", 
                                ["Professional", "Enthusiastic", "Formal", "Creative"])
        letter_length = st.selectbox("Length", ["Brief", "Standard", "Detailed"])
    
    job_description = st.text_area("Job Description*", 
                                 placeholder="Paste the complete job description here...",
                                 height=150)
    
    if st.button("📝 Generate Cover Letter", use_container_width=True):
        if not company_name or not job_title or not job_description:
            st.error("Please fill in all required fields")
        else:
            with st.spinner("Writing your personalized cover letter..."):
                cover_letter_prompt = f"""
                User Data: {json.dumps(user_data, indent=2)}
                Company: {company_name}
                Hiring Manager: {hiring_manager}
                Job Title: {job_title}
                Job Description: {job_description}
                Tone: {tone_style}
                Length: {letter_length}
                """
                
                cover_letter = generate_ai_response(
                    PORTFOLIO_PROMPTS["cover_letter"],
                    cover_letter_prompt
                )
                
                st.markdown("---")
                st.markdown("### 📨 Your Generated Cover Letter")
                st.markdown(cover_letter)
                
                # Download options
                download_cl = create_download_link(cover_letter, "cover_letter.md", "text/markdown")
                st.markdown(download_cl, unsafe_allow_html=True)

def display_portfolio_analyzer(user_data, links_data):
    """Display portfolio analysis and insights"""
    st.markdown("### 🔍 Portfolio Analysis")
    
    if links_data:
        st.markdown("#### 📊 Extracted Insights from Your Links")
        
        for platform, data in links_data.items():
            if data:
                with st.expander(f"📱 {platform.capitalize()} Analysis", expanded=True):
                    if platform == "linkedin":
                        st.markdown("**Skills Identified:**")
                        for skill in data.get("skills", []):
                            st.markdown(f'<span class="skill-tag">{skill}</span>', unsafe_allow_html=True)
                        
                        st.markdown(f"**Experience:** {data.get('experience', 'N/A')}")
                        st.markdown(f"**Education:** {data.get('education', 'N/A')}")
                        
                    elif platform == "github":
                        st.markdown("**Programming Languages:**")
                        for lang in data.get("programming_languages", []):
                            st.markdown(f'<span class="skill-tag">{lang}</span>', unsafe_allow_html=True)
                        
                        st.markdown("**Notable Projects:**")
                        for project in data.get("projects", []):
                            st.markdown(f"• {project}")
    
    # Skill enhancement
    st.markdown("---")
    st.markdown("### 🚀 Skill Enhancement")
    
    original_description = st.text_area(
        "Paste your original job description or achievement to enhance:",
        placeholder="Responsible for developing web applications and managing databases...",
        height=100
    )
    
    if st.button("Enhance Description", use_container_width=True):
        if original_description:
            with st.spinner("Professionalizing your description..."):
                enhanced = generate_ai_response(
                    PORTFOLIO_PROMPTS["skill_enhancer"],
                    original_description
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("#### Original")
                    st.info(original_description)
                
                with col2:
                    st.markdown("#### Enhanced")
                    st.success(enhanced)

def display_portfolio_templates():
    """Display portfolio template options"""
    st.markdown("### 🎨 Portfolio Templates")
    
    templates = [
        {
            "name": "Modern Professional",
            "description": "Clean, ATS-friendly design with focus on content",
            "features": ["Single column", "Professional fonts", "Skill tags", "Project highlights"]
        },
        {
            "name": "Creative Showcase", 
            "description": "Visual-focused template for designers and creatives",
            "features": ["Two-column layout", "Project galleries", "Color accents", "Custom sections"]
        },
        {
            "name": "Tech Portfolio",
            "description": "Optimized for developers and technical roles",
            "features": ["Code snippets", "Technology stack", "GitHub integration", "Live demos"]
        },
        {
            "name": "Executive Profile",
            "description": "Sophisticated design for senior and executive roles", 
            "features": ["Minimalist design", "Achievement metrics", "Leadership focus", "Testimonials"]
        }
    ]
    
    cols = st.columns(2)
    for i, template in enumerate(templates):
        with cols[i % 2]:
            st.markdown(f"""
            <div class="custom-card">
                <h4>{template['name']}</h4>
                <p>{template['description']}</p>
                <ul>
                    {''.join([f'<li>{feature}</li>' for feature in template['features']])}
                </ul>
                <button style="background: #667eea; color: white; border: none; padding: 0.5rem 1rem; border-radius: 20px; cursor: pointer;">Use Template</button>
            </div>
            """, unsafe_allow_html=True)

# --- Authentication System ---
def display_auth_system():
    """Display authentication system"""
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h2 style="color: #667eea; margin: 0;">Portfolio Maker</h2>
            <p style="color: #666; margin: 0;">AI Resume Builder</p>
        </div>
        """, unsafe_allow_html=True)
        
        if not st.session_state.get('logged_in'):
            tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
            
            with tab1:
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                
                if st.button("Login", use_container_width=True):
                    if username and password:
                        user_data = users_collection.find_one({"_id": username})
                        if user_data and verify_password(user_data["password"], password):
                            st.session_state.logged_in = True
                            st.session_state.username = username
                            st.session_state.user_data = user_data.get('portfolio_data', {})
                            st.rerun()
                        else:
                            st.error("Invalid username or password")
                    else:
                        st.warning("Please enter username and password")
            
            with tab2:
                new_username = st.text_input("New Username")
                new_password = st.text_input("New Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                
                if st.button("Register", use_container_width=True):
                    if new_username and new_password:
                        if new_password == confirm_password:
                            if users_collection.find_one({"_id": new_username}):
                                st.error("Username already exists")
                            else:
                                users_collection.insert_one({
                                    "_id": new_username,
                                    "password": hash_password(new_password),
                                    "portfolio_data": {},
                                    "created_at": datetime.now()
                                })
                                st.success("Registration successful! Please login.")
                        else:
                            st.error("Passwords do not match")
                    else:
                        st.warning("Please fill all fields")
        else:
            st.markdown(f"""
            <div class="custom-card">
                <h4 style="color: #667eea; margin: 0;">Welcome back!</h4>
                <p style="margin: 0.5rem 0;">{st.session_state.username}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.username = ""
                st.session_state.user_data = {}
                st.rerun()
            
            st.markdown("---")
            st.markdown("### 💾 Save Your Progress")
            if st.button("Save Portfolio Data", use_container_width=True):
                if hasattr(st.session_state, 'user_data'):
                    users_collection.update_one(
                        {"_id": st.session_state.username},
                        {"$set": {"portfolio_data": st.session_state.user_data}}
                    )
                    st.success("Portfolio data saved successfully!")

# --- Main Application ---
def main():
    display_professional_header()
    display_auth_system()
    
    if not st.session_state.get('logged_in'):
        # Welcome screen for non-logged in users
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.header("Create Professional Resumes & Portfolios with AI 🌟")
            st.markdown("""
            Portfolio Maker uses advanced AI to transform your experience and skills into 
            compelling resumes, cover letters, and portfolio websites that stand out to employers.
            """)

            st.subheader("What You Can Create:")
        
            # Create feature cards using Streamlit components
            col1a, col1b = st.columns(2)
            with col1a:
                with st.container():
                    st.markdown("### 📄 ATS-Optimized Resumes")
                    st.caption("Get past automated screening systems")
                with st.container():
                    st.markdown("### 🔗 LinkedIn & GitHub Analysis")
                    st.caption("Extract insights from your profiles")

            with col1b:
                with st.container():
                    st.markdown("### 💌 Personalized Cover Letters")
                    st.caption("Tailored to each job application")
                with st.container():
                    st.markdown("### 🎨 Professional Templates")
                    st.caption("Multiple designs for different industries")
        
        with col2:
            st.markdown("""
            <div class="custom-card" style="text-align: center; padding: 2rem;">
                <h4 style="color: #667eea;">Get Started</h4>
                <p>Login or register to start building your professional portfolio</p>
                <div style="font-size: 4rem; margin: 1rem 0;">🚀</div>
                <p><small>Open the sidebar to create your account</small></p>
            </div>
            """, unsafe_allow_html=True)
        
        return
    
    # Main application for logged-in users
    st.sidebar.markdown("### 🚀 Quick Actions")
    
    if st.sidebar.button("New Resume", use_container_width=True):
        st.session_state.current_tab = "Resume Builder"
    
    if st.sidebar.button("Analyze Profiles", use_container_width=True):
        st.session_state.current_tab = "Profile Analysis"
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 Input Data", 
        "📄 Resume Builder", 
        "💌 Cover Letters", 
        "🔍 Analysis"
    ])
    
    with tab1:
        st.markdown("### 👤 Provide Your Information")
        user_data, links_data, submitted = display_input_forms()
        if submitted:
            st.session_state.user_data = user_data
            st.session_state.links_data = links_data
            st.success("✅ Data saved! Navigate to other tabs to generate documents.")
    
    with tab2:
        if hasattr(st.session_state, 'user_data'):
            display_resume_generator(st.session_state.user_data, 
                                   getattr(st.session_state, 'links_data', {}))
        else:
            st.info("👈 Please provide your information in the 'Input Data' tab first")
    
    with tab3:
        if hasattr(st.session_state, 'user_data'):
            display_cover_letter_generator(st.session_state.user_data)
        else:
            st.info("👈 Please provide your information in the 'Input Data' tab first")
    
    with tab4:
        if hasattr(st.session_state, 'user_data'):
            display_portfolio_analyzer(st.session_state.user_data, 
                                     getattr(st.session_state, 'links_data', {}))
        else:
            st.info("👈 Please provide your information in the 'Input Data' tab first")

if __name__ == "__main__":
    main()