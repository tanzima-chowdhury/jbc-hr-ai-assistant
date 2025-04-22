
import streamlit as st
import pandas as pd
import io
import os
import PyPDF2
import openai
import re
import tempfile
import json
from datetime import datetime
import dateutil.parser
from dateutil.relativedelta import relativedelta

# Initialize session state variables if they don't exist
def init_session_state():
    if 'api_key' not in st.session_state:
        st.session_state.api_key = ""
    if 'api_key_activated' not in st.session_state:
        st.session_state.api_key_activated = False
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = "gpt-4o"

def extract_text_from_pdf(pdf_file):
    """Extract text content from a PDF file."""
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page_num in range(len(pdf_reader.pages)):
        text += pdf_reader.pages[page_num].extract_text()
    return text

def calculate_experience_duration(start_date_str):
    """Calculate duration between start date and current date in 'X year Y month' format."""
    try:
        # Parse the start date string
        if start_date_str == "Not found" or not start_date_str:
            return "Not found"
            
        # Try to parse the date with dateutil parser
        try:
            start_date = dateutil.parser.parse(start_date_str, fuzzy=True)
        except:
            # If parsing fails, try to extract month and year manually
            match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* (\d{4})', 
                             start_date_str, re.IGNORECASE)
            if match:
                month_str = match.group(1)
                year_str = match.group(2)
                # Map abbreviated month to number
                month_map = {
                    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
                    'may': 5, 'jun': 6, 'jul': 7, 'aug': 8,
                    'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                }
                month = month_map.get(month_str.lower()[:3], 1)
                year = int(year_str)
                start_date = datetime(year, month, 1)
            else:
                return "Date format not recognized"
            
        # Calculate the difference between the start date and current date
        current_date = datetime.now()
        delta = relativedelta(current_date, start_date)
        
        # Format the result as "X year Y month"
        years = delta.years
        months = delta.months
        
        if years == 0:
            if months == 1:
                return f"{months} month"
            else:
                return f"{months} months"
        elif years == 1:
            if months == 0:
                return "1 year"
            elif months == 1:
                return "1 year 1 month"
            else:
                return f"1 year {months} months"
        else:
            if months == 0:
                return f"{years} years"
            elif months == 1:
                return f"{years} years 1 month"
            else:
                return f"{years} years {months} months"
    except Exception as e:
        return f"Error calculating duration: {str(e)}"

def extract_field(text, field_name):
    """Extract a specific field from text response when JSON parsing fails"""
    pattern = rf"{field_name}[:\s]+(.*?)(?:\n|$|,)"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "Not found"

def extract_cv_info(cv_text):
    """Use OpenAI API to extract structured information from CV text."""
    
    # Get current date for calculating work experience
    current_date = datetime.now()
    current_date_str = current_date.strftime("%Y %B")
    
    prompt = f"""
    Extract the following information from the CV text below. 
    If you cannot find a particular piece of information, respond with "Not found" for that field.
    
    Information to extract:
    1. Name
    2. Last Education and university
    3. Number of total year experiences
    4. Present field of experience
    5. Overall expertise area
    6. Present organization designation
    7. Mobile number
    8. Email address
    9. Present organization name
    10. Working experience in present organization (start date in format 'Month YYYY', e.g. 'December 2022')
    
    Today is {current_date_str}.
    
    CV Text:
    {cv_text}
    
    Your response MUST be a valid JSON object with ONLY the following keys:
    {{
      "name": "extracted name",
      "last_education": "extracted education and university",
      "total_experience": "total number of experiences in all organizations",
      "present_field": "present field of experience",
      "overall_expertise_area": "areas of expertise or specialization",
      "present_organization_designation": "current job title or designation",
      "mobile": "extracted mobile number",
      "email": "extracted email address",
      "present_organization_name": "name of current organization",
      "working_experience_in_present_organization": "start date in format 'Month YYYY'"
    }}
    
    Do not include any explanation, just return the JSON object.
    """
    # print(f"Prompt sent to OpenAI API: {prompt}")  # Debugging line
    
    try:
        # Use the model specified in session state or default to gpt-3.5-turbo
        model = st.session_state.get("selected_model", "gpt-3.5-turbo")
        
        # Set the API key from session state
        openai.api_key = st.session_state.api_key
        
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts structured information from CVs. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3  # Lower temperature for more consistent results
        )
        
        # Extract and parse the JSON response
        result = response.choices[0].message.content
        import json
        import re
        
        # Try to find JSON in the response
        json_match = re.search(r'(\{[\s\S]*\})', result, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            try:
                parsed_result = json.loads(json_str)
                
                # Calculate work experience duration
                start_date = parsed_result.get("working_experience_in_present_organization", "Not found")
                parsed_result["working_experience_in_year_in_present_organization"] = calculate_experience_duration(start_date)
                
                return parsed_result
            except json.JSONDecodeError:
                st.warning(f"Failed to parse JSON from response. Attempting alternate extraction.")
                
        # If extraction failed, try to create a structured response manually
        try:
            # Create a standard response manually
            start_date = extract_field(result, "working_experience_in_present_organization")
            experience_duration = calculate_experience_duration(start_date)
            
            # Return in the specified order
            return {
                "name": extract_field(result, "name"),
                "last_education": extract_field(result, "last_education"),
                "overall_expertise_area": extract_field(result, "overall_expertise_area"),
                "present_organization_name": extract_field(result, "present_organization_name"),
                "present_organization_designation": extract_field(result, "present_organization_designation"),
                "working_experience_in_present_organization": start_date,
                "working_experience_in_year_in_present_organization": experience_duration,
                "total_experience": extract_field(result, "total_experience"),
                "present_field": extract_field(result, "present_field"),
                "mobile": extract_field(result, "mobile"),
                "email": extract_field(result, "email")
            }
        except Exception as e:
            st.error(f"Error creating structured response: {str(e)}")
            # Last resort, try direct JSON parsing
            parsed_result = json.loads(result)
            
            # Calculate work experience duration
            start_date = parsed_result.get("working_experience_in_present_organization", "Not found")
            parsed_result["working_experience_in_year_in_present_organization"] = calculate_experience_duration(start_date)
            
            return parsed_result
    
    except Exception as e:
        st.error(f"Error extracting information: {str(e)}")
        return {
            "name": "Error",
            "last_education": "Error",
            "total_experience": "Error",
            "present_field": "Error",
            "overall_expertise_area": "Error",
            "present_organization_designation": "Error",
            "present_organization_name": "Error",
            "working_experience_in_present_organization": "Error",
            "working_experience_in_year_in_present_organization": "Error",
            "mobile": "Error",
            "email": "Error"
        }

def sidebar_settings():
    """Handle sidebar settings for API key and model selection"""
    # API Key input in sidebar
    st.sidebar.header("API Settings")
    
    # API Key input
    api_key_input = st.sidebar.text_input(
        "OpenAI API Key", 
        value=st.session_state.api_key,
        type="password",
        help="Enter your OpenAI API key"
    )
    
    # Activate API Key button
    activate_button = st.sidebar.button("Activate API Key")
    
    if activate_button:
        if api_key_input.strip() == "":
            st.sidebar.error("Please enter an API key")
        else:
            st.session_state.api_key = api_key_input.strip()
            st.session_state.api_key_activated = True
            st.sidebar.success("API Key activated successfully!")
    
    # # Display API key status
    # if st.session_state.api_key_activated:
    #     st.sidebar.info("API Key Status: ✅ Active")
    # else:
    #     st.sidebar.warning("API Key Status: ❌ Not activated")
    
    # Model selection
    st.sidebar.header("Model Settings")
    model_options = ["gpt-3.5-turbo", "gpt-4", "gpt-4o", "gpt-3.5-turbo-16k"]
    selected_model = st.sidebar.selectbox(
        "Select OpenAI Model", 
        options=model_options,
        index=model_options.index(st.session_state.selected_model)
    )
    st.session_state.selected_model = selected_model
    
    # st.sidebar.markdown("---")
    # st.sidebar.markdown("### About")
    # st.sidebar.markdown("""
    # This application extracts key information from CVs/resumes using AI technology.
    
    # Made with ❤️ using:
    # - Streamlit
    # - OpenAI API
    # - PyPDF2
    # """)

def app():
    """Main function for CV extractor app"""
    st.title("CV Information Extractor AI Agent")
    
    # Initialize session state
    init_session_state()
    
    # Handle sidebar settings
    sidebar_settings()
    
    # Main content area
    st.markdown("""
    ### Upload multiple CVs 
    Upload one or more CV PDFs to extract information using AI.
    """)
    
    # File uploader
    uploaded_files = st.file_uploader("Upload CV PDFs", type="pdf", accept_multiple_files=True)
    
    if uploaded_files:
        if st.button("Extract Information"):
            # Check if API key is activated
            if not st.session_state.api_key_activated:
                st.error("Please activate your OpenAI API key in the sidebar first")
                return
                
            # Create progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Create a list to store results
            all_results = []
            
            # Calculate progress steps
            total_files = len(uploaded_files)
            
            # Process each uploaded PDF
            for i, uploaded_file in enumerate(uploaded_files):
                # Update progress
                progress_value = i / total_files
                progress_bar.progress(progress_value)
                status_text.text(f"Processing {i+1} of {total_files}: {uploaded_file.name}")
                
                # Create a temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                    temp_file.write(uploaded_file.getvalue())
                    temp_path = temp_file.name
                
                # Open the temporary file and extract text
                with open(temp_path, 'rb') as file:
                    # Extract text from PDF
                    cv_text = extract_text_from_pdf(file)
                    
                    # Extract structured information
                    cv_info = extract_cv_info(cv_text)
                    
                    # Store filename
                    cv_info["filename"] = uploaded_file.name
                    
                    # Add to results list
                    all_results.append(cv_info)
                
                # Remove temporary file
                os.unlink(temp_path)
            
            # Update progress to completion
            progress_bar.progress(1.0)
            status_text.text("Processing complete!")
            
            # Create a DataFrame from all results and ensure column order
            df = pd.DataFrame(all_results)
 
            # Define the desired column order
            column_order = [
                "name", 
                "last_education", 
                "overall_expertise_area",
                "present_organization_name", 
                "present_organization_designation",
                "working_experience_in_present_organization", 
                "working_experience_in_year_in_present_organization", 
                "total_experience", 
                "present_field", 
                "mobile", 
                "email",
                "filename"
            ]
            
            # Reorder columns (only include columns that exist)
            existing_columns = [col for col in column_order if col in df.columns]
            extra_columns = [col for col in df.columns if col not in column_order]
            df = df[existing_columns + extra_columns]
            
            # Ensure all data is treated as strings to avoid Arrow conversion issues
            for column in df.columns:
                df[column] = df[column].astype(str)
            
            # Display the DataFrame
            st.subheader("Extracted Information")
            st.dataframe(df)
            
            # Create Excel file for download
            excel_buffer = io.BytesIO()
            df.to_excel(excel_buffer, index=False)
            excel_buffer.seek(0)
            
            # Provide download button
            st.download_button(
                label="Download Excel File",
                data=excel_buffer,
                file_name="cv_information.xlsx",
                mime="application/vnd.ms-excel"
            )
