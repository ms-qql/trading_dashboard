def get_custom_css(theme='dark'):
    """Generate custom CSS based on theme selection"""
    
    if theme == 'light':
        return """
        <style>
            /* Light Mode Styling */
            .stApp {
                background-color: #f8fafc;
                color: #1e293b;
                font-family: 'Inter', sans-serif;
            }
            
            /* Darker Blue Sidebar */
            [data-testid="stSidebar"] {
                background-color: #3b82f6 !important;
            }
            
            /* Sidebar text and inputs - better contrast */
            [data-testid="stSidebar"] * {
                color: #ffffff !important;
            }
            
            /* Input fields in sidebar - white background for readability */
            [data-testid="stSidebar"] input,
            [data-testid="stSidebar"] .stNumberInput input,
            [data-testid="stSidebar"] .stTextInput input {
                background-color: #ffffff !important;
                color: #1e293b !important;
                border: 1px solid #cbd5e1 !important;
            }
            
            /* Radio buttons */
            [data-testid="stSidebar"] .st-emotion-cache-1gulkj5 {
                color: #ffffff !important;
            }

            /* Gradient Text */
            .gradient-text {
                background: linear-gradient(45deg, #2563eb, #7c3aed);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-weight: 800;
            }

            /* Metric Cards */
            .metric-card {
                background: rgba(255, 255, 255, 0.9);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
                transition: transform 0.2s ease-in-out;
            }
            
            .metric-card:hover {
                transform: translateY(-2px);
                border-color: rgba(0, 0, 0, 0.2);
            }

            .metric-label {
                font-size: 0.85rem;
                color: #64748b;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 8px;
            }

            .metric-value {
                font-size: 1.8rem;
                font-weight: 700;
                color: #0f172a;
            }

            .metric-sub {
                font-size: 0.8rem;
                margin-top: 4px;
            }

            .positive { color: #16a34a; }
            .negative { color: #dc2626; }
            .neutral { color: #64748b; }

            h1, h2, h3 {
                font-weight: 700 !important;
                color: #0f172a !important;
            }
        </style>
        """
    else:  # dark mode
        return """
        <style>
            /* General Page Styling */
            .stApp {
                background-color: #0e1117;
                color: #fafafa;
                font-family: 'Inter', sans-serif;
            }

            /* Gradient Text */
            .gradient-text {
                background: linear-gradient(45deg, #4f46e5, #9333ea);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-weight: 800;
            }

            /* Metric Cards */
            .metric-card {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                backdrop-filter: blur(10px);
                transition: transform 0.2s ease-in-out;
            }
            
            .metric-card:hover {
                transform: translateY(-2px);
                border-color: rgba(255, 255, 255, 0.2);
            }

            .metric-label {
                font-size: 0.85rem;
                color: #a1a1aa;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 8px;
            }

            .metric-value {
                font-size: 1.8rem;
                font-weight: 700;
                color: #ffffff;
            }

            .metric-sub {
                font-size: 0.8rem;
                margin-top: 4px;
            }

            .positive { color: #10b981; }
            .negative { color: #ef4444; }
            .neutral { color: #d1d5db; }

            /* Headers */
            h1, h2, h3 {
                font-weight: 700 !important;
            }
            
            /* Plotly Chart Background */
            .js-plotly-plot .plotly .main-svg {
                background: transparent !important;
            }
            
            /* Custom File Uploader */
            .stFileUploader > div > div {
                background-color: rgba(255, 255, 255, 0.03);
                border: 1px dashed rgba(255, 255, 255, 0.2);
                border-radius: 12px;
            }
        </style>
        """
