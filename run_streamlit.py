import streamlit as st
import subprocess
import sys
import os

def install_requirements():
    """Install required packages"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    st.set_page_config(
        page_title="Period Tracker Setup",
        page_icon="🌸",
        layout="centered"
    )
    
    st.title("🌸 Period Tracker Application")
    st.write("Welcome to your personal period tracking application!")
    
    # Check if requirements are installed
    try:
        import pandas
        import plotly
        requirements_installed = True
    except ImportError:
        requirements_installed = False
    
    if not requirements_installed:
        st.warning("Installing required packages...")
        if install_requirements():
            st.success("Packages installed successfully! Please refresh the page.")
            st.experimental_rerun()
        else:
            st.error("Failed to install packages. Please run: pip install -r requirements.txt")
            return
    
    st.success("All requirements are installed!")
    st.info("The Period Tracker application is ready to use!")
    
    # Import and run the main application
    try:
        from main import main as run_period_tracker
        run_period_tracker()
    except Exception as e:
        st.error(f"Error running the application: {str(e)}")
        st.info("Please make sure all dependencies are properly installed.")

if __name__ == "__main__":
    main()