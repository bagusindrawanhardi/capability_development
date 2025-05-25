# -*- coding: utf-8 -*-
"""
Created on Mon May  5 09:20:57 2025

@author: bagus
"""

import os
import dash
from dash import Dash, html, dcc, Input, Output, State, ALL, dash_table
import plotly.graph_objects as go
import pandas as pd
import logging

# --- Google Sheets setup ---
import gspread
from google.oauth2.service_account import Credentials
from google.auth.exceptions import RefreshError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to your service account credentials JSON and your Google Sheet key
cred_file = 'api2-387815-6e8d5d70f48d.json'
sheet_key = '13FEr2LjKcpsUQnOBp0GJvsVUmPVZNa7H4lXrs7n8abY'

# Initialize worksheet variable so it's always defined
worksheet = None
score_data = []

# Authenticate and open the Google Sheet
scope = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
try:
    creds = Credentials.from_service_account_file(cred_file, scopes=scope)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(sheet_key)
    worksheet = sh.sheet1
    records = worksheet.get_all_records()
    score_data = records or []
    logger.info(f"Loaded {len(score_data)} records from Google Sheet.")
except FileNotFoundError:
    logger.error(f"Credentials file not found at {cred_file}. Please replace with a valid JSON key.")
except RefreshError as e:
    logger.error(f"Failed to refresh credentials: {e}. Check the service account JSON and your system clock.")
except Exception as e:
    logger.error(f"Unexpected error accessing Google Sheet: {e}. Falling back to empty dataset.")

# --- Data definitions ---
participants = [
    "Ernanda (BackEnd Developer)", "Yudi (FrontEnd Developer)", "Wahyu Widi (Developer)",
    "Gilas (Developer)", "Irwan (FrontEnd Developer)", "Nahrowi (Data Scientist)",
    "David (Designer)", "Ammar (Product Manager)", "Bagus (Data Scientist)"
]

week_dropdown = [
    {"label": "Week 1 (Communication)", "value": "Week 1"},
    {"label": "Week 2 (Documentation)", "value": "Week 2"},
    {"label": "Week 3 (Tool Explanation)", "value": "Week 3"},
    {"label": "Week 4 (Teamwork)", "value": "Week 4"},
    {"label": "Week 5 (Interviewing)", "value": "Week 5"},
    {"label": "Week 6 (Feedback)", "value": "Week 6"},
    {"label": "Week 7 (Presentation)", "value": "Week 7"},
    {"label": "Week 8 (Professionalism)", "value": "Week 8"}
]

week_criteria = {
    "Week 1": ["Eye Contact", "Posture", "Voice Clarity", "Natural Gesture"],
    "Week 2": ["Structure", "Technical Accuracy", "Simplicity", "Readability"],
    "Week 3": ["Clarity", "Relevance", "Confidence", "Simplicity"],
    "Week 4": ["Active Listening", "Responsiveness", "Supportiveness", "Teamwork"],
    "Week 5": ["Structure (STAR)", "Confidence", "Engagement", "Clarity"],
    "Week 6": ["Honesty", "Reflection Quality", "Openness", "Empathy"],
    "Week 7": ["Presentation Flow", "Visual Support", "Explanation Clarity", "Time Management"],
    "Week 8": ["Professionalism", "Completeness", "Confidence", "Adaptability"]
}

competency_map = {
    "Week 1": "Communication", "Week 2": "Documentation", "Week 3": "Tool Explanation",
    "Week 4": "Teamwork", "Week 5": "Interviewing", "Week 6": "Feedback",
    "Week 7": "Presentation", "Week 8": "Professionalism"
}

weeks = list(week_criteria.keys())

# --- App setup ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

app.title = "GEARS Capability Development Dashboard"

# --- Layout ---
app.layout = html.Div(
    [
        html.H1(
            "GEARS Capability Development Dashboard",
            style={
                'textAlign': 'center', 'marginTop': '20px',
                'marginBottom': '30px', 'color': '#333'
            }
        ),

        # Left Panel
        html.Div(
            [
                html.Label("👤 Participant"),
                dcc.Dropdown(
                    id="participant",
                    options=[{"label": p, "value": p} for p in participants],
                    value=participants[0]
                ),
                html.Br(),
                html.Label("👤 Reviewer"),
                dcc.Dropdown(
                    id="reviewer",
                    options=[{"label": p, "value": p} for p in participants],
                    value=participants[1]
                ),
                html.Br(),
                html.Label("📅 Week"),
                dcc.Dropdown(id="week", options=week_dropdown, value="Week 1"),
                html.Br(),
                html.Div(id="sliders-container", style={"marginTop": "20px"}),
                html.Button(
                    "Submit Score", id="submit-score", n_clicks=0,
                    style={"marginTop": "10px", "marginBottom": "20px"}
                ),

                html.H4("Evaluation History"),
                dash_table.DataTable(
                    id="score-table",
                    columns=[
                        {"name": c, "id": c}
                        for c in ["Reviewer", "Participant", "Week", "Final Score"]
                    ],
                    data=[],
                    style_table={"maxHeight": "350px", "overflowY": "auto"},
                    style_cell={"textAlign": "left"}
                )
            ],
            style={
                'width': '33%', 'display': 'inline-block', 'verticalAlign': 'top',
                'padding': '20px', 'border': '2px solid #ccc',
                'borderRadius': '10px', 'boxShadow': '0 2px 6px rgba(0,0,0,0.1)',
                'backgroundColor': '#fafafa', 'height': '1055px'
            }
        ),

        # Right Panel
        html.Div(
            [
                # Score Trend
                html.Div(
                    [
                        html.Label("🔎 View Participant"),
                        dcc.Dropdown(
                            id="right-participant",
                            options=[{"label": p, "value": p} for p in participants],
                            value=participants[0],
                            clearable=False,
                            style={"width": "600px", "marginBottom": "20px"}
                        ),
                        dcc.Graph(id="score-trend", style={"backgroundColor": "white"})
                    ],
                    style={
                        "marginBottom": "30px", "padding": "10px",
                        "border": "2px solid #3399ff", "borderRadius": "10px"
                    }
                ),

                # Readiness + Windrose
                html.Div(
                    [
                        # Readiness block
                        html.Div(
                            [
                                html.Img(
                                    id="participant-photo", src="",
                                    style={
                                        "height": "300px", "borderRadius": "10px",
                                        "marginBottom": "10px"
                                    }
                                ),
                                html.Div(
                                    id="readiness-score-text",
                                    style={"fontSize": "36px", "fontWeight": "bold"}
                                )
                            ],
                            style={
                                'border': '2px solid #28a745', 'padding': '20px',
                                'borderRadius': '10px', 'width': '40%',
                                'color': '#28a745', 'textAlign': 'center',
                                'display': 'inline-block', 'backgroundColor': 'white',
                                'verticalAlign': 'top'
                            }
                        ),
                        # Windrose block
                        html.Div(
                            dcc.Graph(id="windrose-diagram"),
                            style={
                                'width': '58%', 'display': 'inline-block',
                                'verticalAlign': 'top', 'marginLeft': '2%',
                                'padding': '10px', 'border': '2px solid #ff9933',
                                'borderRadius': '10px', 'backgroundColor': '#fff'
                            }
                        )
                    ],
                    style={'display': 'flex', 'justifyContent': 'space-between'}
                )
            ],
            style={
                'width': '58%', 'display': 'inline-block', 'padding': '20px',
                'border': '2px solid #ccc', 'borderRadius': '10px',
                'boxShadow': '0 2px 6px rgba(0,0,0,0.1)', 'marginLeft': '2%'
            }
        )
    ],
    style={"padding": "0px 30px", "fontFamily": "Arial, sans-serif"}
)

# --- Callbacks ---
@app.callback(
    Output("sliders-container", "children"),
    Input("week", "value")
)
def update_sliders(week):
    return [
        html.Div([
            html.Label(f"{crit} (0–10)"),
            dcc.Slider(
                id={"type": "dynamic-slider", "index": crit},
                min=0, max=10, step=1, value=5,
                marks={i: str(i) for i in range(11)}
            )
        ], style={"marginBottom": "10px"})
        for crit in week_criteria.get(week, [])
    ]

@app.callback(
    Output("score-trend", "figure"),
    Output("participant-photo", "src"),
    Output("readiness-score-text", "children"),
    Output("windrose-diagram", "figure"),
    Output("score-table", "data"),
    Input("submit-score", "n_clicks"),
    Input("right-participant", "value"),
    State("participant", "value"),
    State("reviewer", "value"),
    State("week", "value"),
    State({"type": "dynamic-slider", "index": ALL}, "value"),
    State({"type": "dynamic-slider", "index": ALL}, "id")
)
def update_scores(submit_clicks, view_participant,
                  participant, reviewer, week, values, ids):
    ctx = dash.callback_context
    global score_data

    trig = ctx.triggered[0]["prop_id"].split(".")[0]

    # Submit a new score
    if trig == "submit-score":
        criteria = [i["index"] for i in ids]
        final = round(sum(values) / len(values), 2) if values else 0
        new_entry = {
            "Reviewer": reviewer,
            "Participant": participant,
            "Week": week,
            **dict(zip(criteria, values)),
            "Final Score": final
        }
        score_data.append(new_entry)
        # Persist to Google Sheet if auth succeeded
        if worksheet is not None:
            df = pd.DataFrame(score_data)
            try:
                worksheet.clear()
                worksheet.update([df.columns.tolist()] + df.values.tolist())
            except Exception as e:
                logger.error(f"Error updating sheet: {e}")
        else:
            logger.warning("Skipping sheet update because authentication failed.")

    # Build DataFrame for visuals
    df = pd.DataFrame(score_data)
    table_data = df[["Reviewer", "Participant", "Week", "Final Score"]].to_dict("records") if not df.empty else []

    # Score Trend
    tf = go.Figure()
    if not df.empty:
        df_avg = df.groupby(["Participant", "Week"])['Final Score'].mean().reset_index()
        part_df = df_avg[df_avg['Participant'] == view_participant]
        tf.add_trace(go.Scatter(
            x=part_df['Week'], y=part_df['Final Score'],
            mode='lines+markers', name=view_participant
        ))
    tf.update_layout(
        title=f"{view_participant} Score Trend",
        xaxis_title="Week", yaxis_title="Score (0–10)",
        plot_bgcolor='white'
    )
    tf.update_xaxes(
        showgrid=True, gridwidth=1, gridcolor='lightgrey',
        minor=dict(showgrid=True, gridwidth=0.5, gridcolor='lightgrey')
    )
    tf.update_yaxes(
        showgrid=True, gridwidth=1, gridcolor='lightgrey',
        minor=dict(showgrid=True, gridwidth=0.5, gridcolor='lightgrey')
    )

    # Readiness Score
    pd_sel = df[df['Participant'] == view_participant] if not df.empty else pd.DataFrame()
    all_scores = [
        v for w in weeks for c in week_criteria[w]
        if c in pd_sel.columns for v in pd_sel[c].dropna()
    ]
    readiness = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0
    rd_text = f"🚀 Readiness Score: {readiness}/10"

    # Competency Radar (Windrose)
    cats = list(set(competency_map.values()))
    rs = []
    for cat in cats:
        vals = []
        for w, comp in competency_map.items():
            if comp == cat:
                for crit in week_criteria[w]:
                    if crit in pd_sel.columns:
                        vals += pd_sel[crit].tolist()
        rs.append(round(sum(vals) / len(vals), 2) if vals else 0)
    rf = go.Figure()
    rf.add_trace(go.Scatterpolar(
        r=rs + [rs[0]], theta=cats + [cats[0]],
        fill='toself', name=view_participant
    ))
    rf.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10])))

    # Participant Photo URL
    photo = view_participant.split(" ")[0]
    src = f"/assets/photo/{photo}.PNG"

    return tf, src, rd_text, rf, table_data

if __name__ == "__main__":
    app.run_server(debug=True, port=8051)
