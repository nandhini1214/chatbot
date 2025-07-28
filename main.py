import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
import calendar

class PeriodTracker:
    def __init__(self):
        self.db_name = "period_tracker.db"
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database with required tables"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Create periods table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS periods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_date DATE NOT NULL,
                end_date DATE,
                flow_intensity TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create symptoms table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS symptoms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                symptom_type TEXT NOT NULL,
                severity INTEGER,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create cycle_data table for predictions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cycle_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cycle_length INTEGER DEFAULT 28,
                period_length INTEGER DEFAULT 5,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_period(self, start_date, end_date=None, flow_intensity="Medium", notes=""):
        """Add a new period record"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO periods (start_date, end_date, flow_intensity, notes)
            VALUES (?, ?, ?, ?)
        ''', (start_date, end_date, flow_intensity, notes))
        
        conn.commit()
        conn.close()
        return True
    
    def add_symptom(self, date, symptom_type, severity, notes=""):
        """Add a symptom record"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO symptoms (date, symptom_type, severity, notes)
            VALUES (?, ?, ?, ?)
        ''', (date, symptom_type, severity, notes))
        
        conn.commit()
        conn.close()
        return True
    
    def get_periods(self):
        """Retrieve all period records"""
        conn = sqlite3.connect(self.db_name)
        df = pd.read_sql_query("SELECT * FROM periods ORDER BY start_date DESC", conn)
        conn.close()
        return df
    
    def get_symptoms(self):
        """Retrieve all symptom records"""
        conn = sqlite3.connect(self.db_name)
        df = pd.read_sql_query("SELECT * FROM symptoms ORDER BY date DESC", conn)
        conn.close()
        return df
    
    def calculate_cycle_stats(self):
        """Calculate cycle statistics"""
        periods_df = self.get_periods()
        if len(periods_df) < 2:
            return None
        
        periods_df['start_date'] = pd.to_datetime(periods_df['start_date'])
        periods_df = periods_df.sort_values('start_date')
        
        # Calculate cycle lengths
        cycle_lengths = []
        for i in range(1, len(periods_df)):
            cycle_length = (periods_df.iloc[i]['start_date'] - periods_df.iloc[i-1]['start_date']).days
            cycle_lengths.append(cycle_length)
        
        if cycle_lengths:
            avg_cycle_length = np.mean(cycle_lengths)
            return {
                'average_cycle_length': round(avg_cycle_length, 1),
                'cycle_lengths': cycle_lengths,
                'last_period': periods_df.iloc[0]['start_date'].date()
            }
        return None
    
    def predict_next_period(self):
        """Predict next period date"""
        stats = self.calculate_cycle_stats()
        if stats:
            next_period = stats['last_period'] + timedelta(days=int(stats['average_cycle_length']))
            return next_period
        return None
    
    def get_fertility_window(self):
        """Calculate fertility window"""
        stats = self.calculate_cycle_stats()
        if stats:
            last_period = stats['last_period']
            cycle_length = int(stats['average_cycle_length'])
            ovulation_day = last_period + timedelta(days=cycle_length - 14)
            fertility_start = ovulation_day - timedelta(days=5)
            fertility_end = ovulation_day + timedelta(days=1)
            return {
                'ovulation': ovulation_day,
                'fertility_start': fertility_start,
                'fertility_end': fertility_end
            }
        return None

def main():
    st.set_page_config(
        page_title="Period Tracker",
        page_icon="🌸",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize the tracker
    tracker = PeriodTracker()
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        color: #FF69B4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #FFF0F5;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #FF69B4;
    }
    .prediction-card {
        background-color: #E6F3FF;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #4169E1;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="main-header">🌸 Period Tracker</h1>', unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a page", [
        "📊 Dashboard", 
        "📅 Log Period", 
        "😷 Log Symptoms", 
        "📈 Analytics", 
        "🔮 Predictions"
    ])
    
    if page == "📊 Dashboard":
        show_dashboard(tracker)
    elif page == "📅 Log Period":
        show_period_logging(tracker)
    elif page == "😷 Log Symptoms":
        show_symptom_logging(tracker)
    elif page == "📈 Analytics":
        show_analytics(tracker)
    elif page == "🔮 Predictions":
        show_predictions(tracker)

def show_dashboard(tracker):
    st.header("Dashboard Overview")
    
    # Get basic stats
    periods_df = tracker.get_periods()
    symptoms_df = tracker.get_symptoms()
    stats = tracker.calculate_cycle_stats()
    
    # Create columns for metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total Periods Logged", len(periods_df))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Symptoms Logged", len(symptoms_df))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        if stats:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Average Cycle Length", f"{stats['average_cycle_length']} days")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Average Cycle Length", "Need more data")
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        next_period = tracker.predict_next_period()
        if next_period:
            days_until = (next_period - datetime.now().date()).days
            st.markdown('<div class="prediction-card">', unsafe_allow_html=True)
            st.metric("Next Period In", f"{days_until} days")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="prediction-card">', unsafe_allow_html=True)
            st.metric("Next Period", "Need more data")
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Recent periods
    if not periods_df.empty:
        st.subheader("Recent Periods")
        st.dataframe(periods_df.head(5), use_container_width=True)
    
    # Recent symptoms
    if not symptoms_df.empty:
        st.subheader("Recent Symptoms")
        st.dataframe(symptoms_df.head(5), use_container_width=True)

def show_period_logging(tracker):
    st.header("Log Your Period")
    
    with st.form("period_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input("Period Start Date", value=datetime.now().date())
            flow_intensity = st.selectbox("Flow Intensity", ["Light", "Medium", "Heavy"])
        
        with col2:
            end_date = st.date_input("Period End Date (optional)", value=None)
            notes = st.text_area("Notes (optional)")
        
        submitted = st.form_submit_button("Log Period")
        
        if submitted:
            success = tracker.add_period(start_date, end_date, flow_intensity, notes)
            if success:
                st.success("Period logged successfully!")
                st.rerun()

def show_symptom_logging(tracker):
    st.header("Log Symptoms")
    
    with st.form("symptom_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            symptom_date = st.date_input("Date", value=datetime.now().date())
            symptom_type = st.selectbox("Symptom Type", [
                "Cramps", "Headache", "Mood Changes", "Bloating", 
                "Breast Tenderness", "Fatigue", "Nausea", "Back Pain", "Other"
            ])
        
        with col2:
            severity = st.slider("Severity (1-10)", 1, 10, 5)
            notes = st.text_area("Additional Notes")
        
        submitted = st.form_submit_button("Log Symptom")
        
        if submitted:
            success = tracker.add_symptom(symptom_date, symptom_type, severity, notes)
            if success:
                st.success("Symptom logged successfully!")
                st.rerun()

def show_analytics(tracker):
    st.header("Analytics & Insights")
    
    periods_df = tracker.get_periods()
    symptoms_df = tracker.get_symptoms()
    
    if not periods_df.empty:
        # Cycle length trend
        stats = tracker.calculate_cycle_stats()
        if stats and len(stats['cycle_lengths']) > 1:
            st.subheader("Cycle Length Trend")
            fig = px.line(
                x=range(1, len(stats['cycle_lengths']) + 1),
                y=stats['cycle_lengths'],
                title="Cycle Length Over Time",
                labels={'x': 'Cycle Number', 'y': 'Days'}
            )
            fig.add_hline(y=stats['average_cycle_length'], line_dash="dash", 
                         annotation_text=f"Average: {stats['average_cycle_length']:.1f} days")
            st.plotly_chart(fig, use_container_width=True)
    
    if not symptoms_df.empty:
        # Symptom frequency
        st.subheader("Symptom Analysis")
        symptom_counts = symptoms_df['symptom_type'].value_counts()
        fig = px.bar(
            x=symptom_counts.index,
            y=symptom_counts.values,
            title="Most Common Symptoms",
            labels={'x': 'Symptom Type', 'y': 'Frequency'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Symptom severity over time
        symptoms_df['date'] = pd.to_datetime(symptoms_df['date'])
        fig = px.scatter(
            symptoms_df,
            x='date',
            y='severity',
            color='symptom_type',
            title="Symptom Severity Over Time",
            labels={'date': 'Date', 'severity': 'Severity (1-10)'}
        )
        st.plotly_chart(fig, use_container_width=True)

def show_predictions(tracker):
    st.header("Cycle Predictions")
    
    next_period = tracker.predict_next_period()
    fertility_window = tracker.get_fertility_window()
    
    if next_period:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="prediction-card">', unsafe_allow_html=True)
            st.subheader("Next Period")
            st.write(f"**Predicted Date:** {next_period}")
            days_until = (next_period - datetime.now().date()).days
            st.write(f"**Days Until:** {days_until}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            if fertility_window:
                st.markdown('<div class="prediction-card">', unsafe_allow_html=True)
                st.subheader("Fertility Window")
                st.write(f"**Ovulation:** {fertility_window['ovulation']}")
                st.write(f"**Fertile Period:** {fertility_window['fertility_start']} to {fertility_window['fertility_end']}")
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Calendar view
        st.subheader("Monthly Calendar View")
        show_calendar_view(tracker, next_period, fertility_window)
    else:
        st.info("Log at least 2 periods to see predictions!")

def show_calendar_view(tracker, next_period, fertility_window):
    """Display a calendar view with predictions"""
    today = datetime.now().date()
    
    # Create a simple calendar visualization
    cal_data = []
    start_date = today.replace(day=1)
    
    # Get days in current month
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    
    for day in range(1, days_in_month + 1):
        current_date = today.replace(day=day)
        status = "Normal"
        
        if current_date == today:
            status = "Today"
        elif current_date == next_period:
            status = "Predicted Period"
        elif fertility_window and fertility_window['fertility_start'] <= current_date <= fertility_window['fertility_end']:
            status = "Fertile Window"
        elif current_date == fertility_window['ovulation'] if fertility_window else False:
            status = "Ovulation"
        
        cal_data.append({
            'Day': day,
            'Date': current_date,
            'Status': status
        })
    
    cal_df = pd.DataFrame(cal_data)
    
    # Create color mapping
    color_map = {
        'Normal': '#F0F0F0',
        'Today': '#FFD700',
        'Predicted Period': '#FF69B4',
        'Fertile Window': '#98FB98',
        'Ovulation': '#FF6347'
    }
    
    fig = px.scatter(
        cal_df,
        x=(cal_df['Day'] - 1) % 7,
        y=-((cal_df['Day'] - 1) // 7),
        color='Status',
        color_discrete_map=color_map,
        title=f"Calendar View - {calendar.month_name[today.month]} {today.year}",
        hover_data=['Date']
    )
    
    fig.update_traces(marker_size=20)
    fig.update_layout(
        xaxis=dict(tickmode='array', tickvals=list(range(7)), 
                  ticktext=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']),
        yaxis=dict(showticklabels=False),
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
