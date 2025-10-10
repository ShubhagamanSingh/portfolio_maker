# 📄 Portfolio Maker - AI Resume Builder

This Streamlit application is **Portfolio Maker**, an intelligent resume and portfolio builder designed to help students and professionals create standout career documents. By leveraging the power of large language models, this tool transforms your skills and experience into compelling resumes and cover letters tailored to your career goals.

## ✨ Features

- **AI Resume Generator**: Creates professional, ATS-friendly resumes from your personal, professional, and educational information.
- **AI Cover Letter Generator**: Writes personalized and compelling cover letters tailored to specific job descriptions and companies.
- **Profile Analysis**: Simulates the analysis of your LinkedIn and GitHub profiles to extract key skills and projects.
- **Skill Enhancement**: Uses AI to transform basic job descriptions into impactful, action-oriented achievement statements.
- **Secure User Authentication**: Features a robust login and registration system to keep your portfolio data private.
- **Data Persistence**: Saves your portfolio information securely in a MongoDB database, so you can return and update it anytime.
- **Downloadable Documents**: Allows you to download your generated resume and cover letter as Markdown (`.md`) files.

## 🚀 Setup and Installation Guide

Follow these steps to get the application running on your local machine.

### Prerequisites

This application uses `pdfkit` to generate PDF files, which requires `wkhtmltopdf`. You must install it separately and ensure it's in your system's PATH.

- **Windows/macOS**: Download from the wkhtmltopdf website.
- **Linux (Debian/Ubuntu)**: `sudo apt-get install wkhtmltopdf`

### Step 1: Get Your Credentials

You will need three things:
1.  **Hugging Face API Token**: To access the AI model.
2.  **MongoDB Connection URI**: To store user data and history.

*   **Hugging Face Token**:
    1.  Go to the Hugging Face website: huggingface.co
    2.  Navigate to **Settings** -> **Access Tokens** and create a new token with `read` permissions.

*   **MongoDB URI**:
    1.  Create a free cluster on MongoDB Atlas.
    2.  Once your cluster is set up, go to **Database** -> **Connect** -> **Drivers**.
    3.  Select Python and copy the connection string (URI). Remember to replace `<password>` with your database user's password.

### Step 2: Create the Secrets File

Streamlit uses a `.streamlit/secrets.toml` file to store sensitive information like API keys.

1.  In your project's root directory (`portfolio_maker/`), create a new folder named `.streamlit`.
2.  Inside the `.streamlit` folder, create a new file named `secrets.toml`.
3.  Add your credentials to this file as shown below:

    ```toml
    # .streamlit/secrets.toml
    HF_TOKEN = "hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    MONGO_URI = "mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/"
    DB_NAME = "portfolio_maker"
    COLLECTION_NAME = "users"
    ```
    *Replace the placeholder values with your actual credentials.*

### Step 3: Install Dependencies

Open your terminal or command prompt, navigate to the project's root directory (`portfolio_maker/`), and run the following command to install the required Python packages:

```bash
pip install -r requirements.txt
```

### Step 4: Run the Streamlit App

Once the installation is complete, run the following command in your terminal:

```bash
streamlit run app.py
```

Your web browser should automatically open with the application running!

## 📁 Project Structure
mybuddy/
├── .streamlit/
│   └── secrets.toml
├── app.py
├── requirements.txt
└── README.md
