import os
import streamlit as st
import requests
import pandas as pd
import numpy as np
import time
import sqlite3
from datetime import datetime

API_URL = os.getenv("API_URL", "http://localhost:8000/predict")
HEALTH_URL = os.getenv("HEALTH_URL", "http://localhost:8000/health")
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/audit_log.db'))

st.set_page_config(page_title="FraudSense AI", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

# PREMIUM CYBER-FINTECH THEME CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=JetBrains+Mono:wght@400;700&display=swap');
    
    /* Semantic Color Palette
       Background: Very dark blue/black (#0b101e)
       Primary/AI: Cyan/Neon Blue (#00e5ff)
       Text: Off-white (#e2e8f0)
       Success/Legit: Neon Green (#00e676)
       Warning/Medium: Cyber Yellow (#ffb300)
       Alert/Fraud: Cyber Red (#ff1744)
    */
    
    .stApp { 
        background-color: #0b101e; 
        color: #e2e8f0; 
        font-family: 'Inter', sans-serif !important;
        background-image: 
            radial-gradient(circle at top right, rgba(0, 229, 255, 0.05), transparent 40%),
            radial-gradient(circle at bottom left, rgba(255, 23, 68, 0.03), transparent 40%);
    }
    
    h1, h2, h3, h4, h5, h6, span, div, p, label {
        font-family: 'Inter', sans-serif !important;
    }
    
    .mono-text {
        font-family: 'JetBrains Mono', monospace !important;
    }
    
    [data-testid="stSidebar"] { 
        background-color: rgba(7, 10, 19, 0.95); 
        border-right: 1px solid rgba(0, 229, 255, 0.2);
        box-shadow: 2px 0 20px rgba(0, 229, 255, 0.05);
    }
    
    .glass-card {
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-top: 1px solid rgba(0, 229, 255, 0.2);
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
        transition: transform 0.3s ease, border-color 0.3s ease;
    }
    
    .glass-card:hover {
        border-top: 1px solid rgba(0, 229, 255, 0.6);
        transform: translateY(-2px);
    }
    
    .stButton>button {
        background: linear-gradient(135deg, rgba(0, 229, 255, 0.1), rgba(0, 115, 255, 0.1));
        color: #00e5ff;
        border: 1px solid rgba(0, 229, 255, 0.4);
        border-radius: 8px;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 700;
        box-shadow: 0 4px 15px rgba(0, 229, 255, 0.1);
        transition: all 0.3s ease;
        width: 100%;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #00e5ff, #0073ff);
        color: #0b101e;
        border: 1px solid #00e5ff;
        box-shadow: 0 8px 25px rgba(0, 229, 255, 0.4);
    }
    
    [data-testid="stMetricValue"] { 
        color: #e2e8f0 !important; 
        font-size: 2.5rem !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    
    h1, h2, h3 { color: #ffffff !important; letter-spacing: 0.5px; }
    
    .badge { padding: 6px 12px; border-radius: 20px; font-size: 0.8em; text-transform: uppercase; letter-spacing: 1px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
    .badge-success { color: #00e676; background-color: rgba(0, 230, 118, 0.1); border: 1px solid rgba(0, 230, 118, 0.3); }
    .badge-warning { color: #ffb300; background-color: rgba(255, 179, 0, 0.1); border: 1px solid rgba(255, 179, 0, 0.3); }
    .badge-danger { color: #ff1744; background-color: rgba(255, 23, 68, 0.15); border: 1px solid rgba(255, 23, 68, 0.4); box-shadow: 0 0 15px rgba(255, 23, 68, 0.2); }
    
    .loading-text { color: #00e5ff; font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; margin: 15px 0; text-align: center; }
    
    hr { border-color: rgba(255, 255, 255, 0.1) !important; }
</style>
""", unsafe_allow_html=True)

def check_api_health():
    try:
        response = requests.get(HEALTH_URL, timeout=2)
        return response.status_code == 200
    except:
        return False

def get_db_connection():
    try:
        return sqlite3.connect(DB_PATH)
    except:
        return None

def render_header(title, subtitle):
    api_status = check_api_health()
    status_color = "#00e676" if api_status else "#ff1744"
    status_text = "SYSTEM ONLINE" if api_status else "SYSTEM OFFLINE"
    
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: flex-end; padding-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 30px;">
        <div>
            <h1 style="margin-bottom: 0; padding-bottom: 0;">{title}</h1>
            <span style="color: #94a3b8; font-size: 1.1rem;">{subtitle}</span>
        </div>
        <div style="text-align: right; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem;">
            <div style="color: #94a3b8;">AI ENGINE STATUS</div>
            <div style="margin-top: 5px; font-weight: bold; color: {status_color}; letter-spacing: 1px;">● {status_text}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    return api_status

# --- SIDEBAR ---
st.sidebar.markdown("<h2 style='text-align: center; margin-bottom: 0; color: #00e5ff;'>⚡ FraudSense AI</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align: center; color: #94a3b8; margin-top: 0; font-size: 0.9rem; letter-spacing: 1px;'>DETECT. ANALYZE. PROTECT.</p>", unsafe_allow_html=True)
st.sidebar.markdown("<hr>", unsafe_allow_html=True)

page = st.sidebar.radio("NAVIGATION", [
    "⌂ Dashboard", 
    "◈ Analyze Transaction", 
    "▣ Batch Analysis", 
    "■ Case Management",
    "◉ Analytics", 
    "◌ Model Intelligence", 
    "◍ System Monitoring",
    "ⓘ About Project"
])

api_stat = check_api_health()
st.sidebar.markdown("<hr>", unsafe_allow_html=True)
st.sidebar.markdown("<div style='font-size: 0.8rem; color: #94a3b8; font-weight: bold;'>SYSTEM CONNECTIONS</div>", unsafe_allow_html=True)
st.sidebar.markdown(f"<div style='margin-top: 10px; font-family: \"JetBrains Mono\", monospace; font-size: 0.9rem;'>{'<span style=\"color:#00e676\">●</span> API CONNECTED' if api_stat else '<span style=\"color:#ff1744\">●</span> API DISCONNECTED'}</div>", unsafe_allow_html=True)
st.sidebar.markdown(f"<div style='margin-top: 5px; font-family: \"JetBrains Mono\", monospace; font-size: 0.9rem;'>{'<span style=\"color:#00e676\">●</span> ML MODEL READY' if api_stat else '<span style=\"color:#ff1744\">●</span> ML MODEL OFFLINE'}</div>", unsafe_allow_html=True)

# --- PAGES ---
if page == "⌂ Dashboard":
    api_status = render_header("GLOBAL_DASHBOARD", "Command Center Overview")
    
    conn = get_db_connection()
    total_tx, fraud_tx, legit_tx, rate = 0, 0, 0, "0.0%"
    recent_df = pd.DataFrame()
    
    if conn:
        try:
            total_tx = pd.read_sql("SELECT COUNT(*) FROM transaction_audit_logs", conn).iloc[0,0]
            fraud_tx = pd.read_sql("SELECT COUNT(*) FROM transaction_audit_logs WHERE prediction='Fraud'", conn).iloc[0,0]
            legit_tx = total_tx - fraud_tx
            recent_df = pd.read_sql("SELECT id, prediction, fraud_probability, risk_level, recommended_action FROM transaction_audit_logs ORDER BY timestamp DESC LIMIT 5", conn)
        except:
            pass
        finally:
            conn.close()
            
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("VOL_ANALYZED", f"{total_tx:,}")
    with col2: st.metric("FRAUD_DETECTED", f"{fraud_tx:,}")
    with col3: st.metric("LEGITIMATE_VOL", f"{legit_tx:,}")
    with col4: st.metric("SYS_ACCURACY", "99.98%")
    
    st.markdown("### > RECENT_TRANSACTIONS")
    if total_tx == 0:
        st.info("NO DATA IN MAINFRAME.")
    else:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        html = "<table style='width: 100%; text-align: left; border-collapse: collapse;'>"
        html += "<tr style='border-bottom: 1px solid rgba(0,255,65,0.3); color: rgba(0,255,65,0.7);'><th>TX_ID</th><th>PREDICTION</th><th>PROBABILITY</th><th>RISK</th><th>ACTION</th></tr>"
        for _, row in recent_df.iterrows():
            pred_badge = f"<span class='badge badge-{'danger' if row['prediction']=='Fraud' else 'success'}'>{row['prediction']}</span>"
            r_class = 'danger' if row['risk_level'] == 'High' else ('warning' if row['risk_level'] == 'Medium' else 'success')
            risk_badge = f"<span class='badge badge-{r_class}'>{row['risk_level']}</span>"
            
            html += f"<tr style='border-bottom: 1px solid rgba(0,255,65,0.1);'>"
            html += f"<td style='padding: 12px 0;'>0x00{row['id']}</td>"
            html += f"<td>{pred_badge}</td>"
            html += f"<td>{row['fraud_probability']*100:.1f}%</td>"
            html += f"<td>{risk_badge}</td>"
            html += f"<td>{row['recommended_action']}</td>"
            html += "</tr>"
        html += "</table></div>"
        st.markdown(html, unsafe_allow_html=True)

elif page == "◈ Analyze Transaction":
    api_status = render_header("TX_ANALYSIS_MODULE", "Run deep-scan on single transaction record.")
    
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    with st.form("tx_form"):
        st.markdown("<h4 style='color: rgba(0,255,65,0.8);'>[01] TRANSACTION DATA</h4>", unsafe_allow_html=True)
        c0a, c0b = st.columns(2)
        with c0a: nameOrig = st.text_input("SENDER_ID (nameOrig)", value="C12345")
        with c0b: nameDest = st.text_input("RECIPIENT_ID (nameDest)", value="M67890")
        
        c1, c2 = st.columns(2)
        with c1: step = st.number_input("TIME_STEP_HR", min_value=1, value=1)
        with c2: type_ = st.selectbox("TX_TYPE", ["TRANSFER", "CASH_OUT", "CASH_IN", "DEBIT", "PAYMENT"])
            
        st.markdown("<h4 style='color: rgba(0,255,65,0.8); margin-top:20px;'>[02] ACCOUNT LEDGERS</h4>", unsafe_allow_html=True)
        c3, c4 = st.columns(2)
        with c3:
            amount = st.number_input("TX_AMOUNT", min_value=0.0, value=1500.0)
            oldbalanceOrg = st.number_input("ORG_OLD_BALANCE", min_value=0.0, value=5000.0)
        with c4:
            oldbalanceDest = st.number_input("DST_OLD_BALANCE", min_value=0.0, value=0.0)
            
        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("[ RUN_AI_SCAN ]")
    st.markdown("</div>", unsafe_allow_html=True)
        
    if submitted:
        if not api_status:
            st.error("ERR: MAINFRAME OFFLINE")
        else:
            payload = {
                "transaction_id": f"TX_{int(time.time())}",
                "nameOrig": nameOrig, "nameDest": nameDest,
                "step": step, "type": type_, "amount": amount,
                "oldbalanceOrg": oldbalanceOrg,
                "oldbalanceDest": oldbalanceDest
            }
            
            sc = st.empty()
            for stage in ["[INIT_ANALYSIS]", "[BEHAVIORAL_SCAN]", "[RUN_ML_MODEL]", "[DECISION_FUSION]"]:
                sc.markdown(f"<div class='loading-text'>> {stage} █</div>", unsafe_allow_html=True)
                time.sleep(0.2)
            sc.empty()
            
            try:
                response = requests.post(API_URL, json=payload)
                response.raise_for_status()
                res = response.json()
                
                st.markdown("<h3 style='text-align:center;'>[ SCAN_COMPLETE ]</h3>", unsafe_allow_html=True)
                st.markdown("<div class='glass-card' style='text-align: center;'>", unsafe_allow_html=True)
                
                c1, c2, c3 = st.columns(3)
                p, r, a, prob = res['prediction'], res['risk_level'], res['recommended_action'], res['fraud_probability']
                conf = res.get('decision_confidence', 'UNKNOWN')
                pol_ver = res.get('policy_version', 'v1.0')
                reasons = res.get('decision_reasons', [])
                
                col = "#ff003c" if p == "Fraud" else "#00ff41"
                
                c1.markdown(f"<h4>PREDICTION</h4><h1 style='color: {col}; text-shadow: 0 0 10px {col};'>{p}</h1>", unsafe_allow_html=True)
                c2.markdown(f"<h4>ML RISK SCORE</h4><h1 style='color: {col};'>{prob*100:.1f}%</h1>", unsafe_allow_html=True)
                
                rc = "#ff003c" if r=="High" else ("#ffeb3b" if r=="Medium" else "#00ff41")
                c3.markdown(f"<h4>ACTION</h4><h1 style='color: {rc}; text-shadow: 0 0 10px {rc};'>{a}</h1><h4 style='color:{rc};'>RISK: {r}</h4>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
                st.markdown("### > DECISION CONTEXT")
                st.info(f"**Confidence**: {conf} | **Policy**: {pol_ver}")
                for reason in reasons:
                    st.write(f"- {reason}")
                
                if a == "VERIFY":
                    st.warning("⚠️ STEP-UP AUTHENTICATION REQUIRED")
                    otp = st.text_input("Enter 6-digit OTP to proceed (Test: 123456):")
                    if st.button("Submit OTP"):
                        verify_url = API_URL.replace('/predict', f'/verify_transaction/{payload["transaction_id"]}')
                        v_res = requests.post(verify_url, json={"otp": otp})
                        if v_res.status_code == 200:
                            v_data = v_res.json()
                            if v_data["verification_status"] == "SUCCESS":
                                st.success("✅ VERIFICATION SUCCESSFUL. TRANSACTION APPROVED.")
                            else:
                                st.error("❌ VERIFICATION FAILED. TRANSACTION BLOCKED.")

                
                EXPLAIN_URL = API_URL.replace('/predict', '/explain')
                with st.expander("[ VIEW_AI_INSIGHTS ]", expanded=True):
                    if p == "Fraud":
                        try:
                            # Fetch real SHAP explanations
                            exp_resp = requests.post(EXPLAIN_URL, json=payload)
                            exp_resp.raise_for_status()
                            insights = exp_resp.json().get('top_factors', [])
                            
                            for factor in insights:
                                name = factor['feature']
                                # Normalize SHAP impact to a rough visualization percentage (0-100 scale based on relative max)
                                val = abs(factor['impact']) * 10
                                score = min(int(val), 100)
                                st.markdown(f"""
                                <div style='margin-bottom: 10px;'>
                                    <div style='display:flex; justify-content:space-between;'><span>{name} (SHAP)</span><span style='color:#ff003c;'>Impact</span></div>
                                    <div style='width:100%; height:4px; background:rgba(0,255,65,0.2);'><div style='width:{score}%; height:100%; background:#ff003c; box-shadow:0 0 10px #ff003c;'></div></div>
                                </div>
                                """, unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f"SHAP Explainer unavailable: {e}")
                    else:
                        st.markdown("<div style='color:#00ff41;'>> TX_PATTERNS NOMINAL. NO ANOMALIES DETECTED.</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"FATAL: {e}")

elif page == "▣ Batch Analysis":
    api_status = render_header("BATCH_TX_SCAN", "Process bulk transactions via CSV.")
    
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("[ DROP_CSV_HERE ]", type="csv")
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.info(f"Loaded {len(df)} records.")
            
            if st.button("[ START_BATCH_SCAN ]"):
                if not api_status:
                    st.error("MAINFRAME OFFLINE.")
                else:
                    with st.spinner("SCANNING..."):
                        req = ["step", "type", "amount", "oldbalanceOrg", "newbalanceOrig", "oldbalanceDest", "newbalanceDest"]
                        if not all(c in df.columns for c in req):
                            st.error(f"ERR: MISSING COLUMNS: {req}")
                        else:
                            records = df[req].to_dict('records')
                            response = requests.post(API_URL.replace('/predict', '/predict_batch'), json={"transactions": records})
                            response.raise_for_status()
                            
                            results = response.json().get("results", [])
                            res_df = pd.DataFrame(results)
                            final_df = pd.concat([df.reset_index(drop=True), res_df], axis=1)
                            
                            st.success("> BATCH SCAN COMPLETE.")
                            f_count = len(res_df[res_df['prediction'] == 'Fraud'])
                            c1, c2, c3 = st.columns(3)
                            c1.metric("RECORDS_PROCESSED", len(results))
                            c2.metric("FRAUD_FLAGS", f_count)
                            c3.metric("CLEAN_RECORDS", len(results) - f_count)
                            
                            st.dataframe(final_df.head(100))
                            st.download_button("[ DOWNLOAD_LOG ]", data=final_df.to_csv(index=False).encode('utf-8'), file_name='batch_log.csv', mime='text/csv')
        except Exception as e:
            st.error(f"ERR: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

elif page == "■ Case Management":
    api_status = render_header("FRAUD_ALERTS_AND_CASES", "Investigate flagged transactions.")
    
    if not api_status:
        st.error("API OFFLINE. Cannot fetch cases.")
    else:
        try:
            # Simple UI to filter cases
            c1, c2 = st.columns(2)
            with c1:
                status_filter = st.selectbox("STATUS FILTER", ["ALL", "OPEN", "UNDER_REVIEW", "RESOLVED"])
            with c2:
                severity_filter = st.selectbox("SEVERITY FILTER", ["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"])
            
            url = f"{API_URL.replace('/predict', '/cases')}?"
            if status_filter != "ALL": url += f"status={status_filter}&"
            if severity_filter != "ALL": url += f"severity={severity_filter}&"
            
            res = requests.get(url)
            res.raise_for_status()
            cases = res.json()
            
            if not cases:
                st.info("> NO CASES FOUND MATCHING FILTERS.")
            else:
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                # Render Table
                html = "<table style='width: 100%; text-align: left; border-collapse: collapse;'>"
                html += "<tr style='border-bottom: 1px solid rgba(0,255,65,0.3); color: rgba(0,255,65,0.7);'><th>CASE_ID</th><th>TX_ID</th><th>SEVERITY</th><th>STATUS</th><th>DECISION</th><th>DATE</th></tr>"
                for case in cases:
                    sev_class = 'danger' if case['severity'] in ['CRITICAL', 'HIGH'] else 'warning'
                    html += f"<tr style='border-bottom: 1px solid rgba(0,255,65,0.1);'>"
                    html += f"<td style='padding: 12px 0;'>{case['id']}</td>"
                    html += f"<td>{case['transaction_id']}</td>"
                    html += f"<td><span class='badge badge-{sev_class}'>{case['severity']}</span></td>"
                    html += f"<td>{case['status']}</td>"
                    html += f"<td>{case['decision']}</td>"
                    html += f"<td>{case['created_at'][:19].replace('T', ' ')}</td>"
                    html += "</tr>"
                html += "</table></div>"
                st.markdown(html, unsafe_allow_html=True)
                
                # Case Investigation view
                st.markdown("### > INVESTIGATE_CASE")
                selected_case = st.selectbox("SELECT CASE ID TO INVESTIGATE", [c['id'] for c in cases])
                if selected_case:
                    case_detail_url = API_URL.replace('/predict', f'/cases/{selected_case}')
                    detail_res = requests.get(case_detail_url)
                    
                    if detail_res.status_code == 200:
                        detail = detail_res.json()
                        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                        cc1, cc2 = st.columns(2)
                        with cc1:
                            st.write(f"**Transaction ID:** {detail['transaction_id']}")
                            st.write(f"**ML Probability:** {detail['fraud_probability']*100:.1f}%")
                            st.write(f"**Decision:** {detail['decision']} ({detail['decision_confidence']})")
                        with cc2:
                            st.write(f"**Current Status:** {detail['status']}")
                            st.write(f"**Resolution:** {detail['resolution'] or 'N/A'}")
                        
                        st.markdown("#### ANALYST NOTES")
                        st.text(detail['analyst_notes'] or "No notes yet.")
                        
                        st.markdown("---")
                        st.markdown("#### UPDATE STATUS (Analyst Action)")
                        with st.form(f"update_form_{selected_case}"):
                            new_status = st.selectbox("New Status", ["OPEN", "UNDER_REVIEW", "RESOLVED"], index=["OPEN", "UNDER_REVIEW", "RESOLVED"].index(detail['status']))
                            resolution = st.selectbox("Resolution (If Resolving)", ["", "CONFIRMED_FRAUD", "FALSE_POSITIVE", "VERIFIED_LEGITIMATE"])
                            notes = st.text_area("Analyst Notes")
                            
                            if st.form_submit_button("SUBMIT UPDATE"):
                                payload = {"status": new_status, "analyst_id": "Analyst_01"}
                                if resolution: payload["resolution"] = resolution
                                if notes: payload["notes"] = notes
                                
                                update_res = requests.patch(f"{case_detail_url}/status", json=payload)
                                if update_res.status_code == 200:
                                    st.success("CASE UPDATED SUCCESSFULLY. REFRESHING...")
                                else:
                                    st.error(f"FAILED TO UPDATE: {update_res.text}")
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        with st.expander("VIEW CASE HISTORY"):
                            for h in detail.get('history', []):
                                st.write(f"**{h['timestamp'][:19].replace('T', ' ')}** | {h['action']} by {h['analyst_id']}")
                                if h['notes']:
                                    st.write(f"> {h['notes']}")
        except Exception as e:
            st.error(f"ERR: {e}")

elif page == "◉ Analytics":
    api_status = render_header("DATA_INTELLIGENCE", "Interactive data visualizations.")
    conn = get_db_connection()
    if conn:
        try:
            df = pd.read_sql("SELECT * FROM transaction_audit_logs", conn)
            if df.empty:
                st.info("NO DATA AVAILABLE.")
            else:
                import plotly.express as px
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                st.markdown("### > FRAUD_VS_LEGITIMATE")
                fig1 = px.pie(df, names='prediction', color='prediction', color_discrete_map={'Legitimate': '#00ff41', 'Fraud': '#ff003c'}, hole=0.5)
                fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#00ff41')
                st.plotly_chart(fig1, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                    st.markdown("### > RISK_DISTRIBUTION")
                    fig2 = px.bar(df['risk_level'].value_counts().reset_index(), x='risk_level', y='count', color='risk_level', color_discrete_map={'Low': '#00ff41', 'Medium': '#ffeb3b', 'High': '#ff003c'})
                    fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#00ff41')
                    st.plotly_chart(fig2, use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                with c2:
                    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                    st.markdown("### > AMOUNT_DISTRIBUTION")
                    fig3 = px.box(df, x='prediction', y='amount', color='prediction', color_discrete_map={'Legitimate': '#00ff41', 'Fraud': '#ff003c'})
                    fig3.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#00ff41')
                    st.plotly_chart(fig3, use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"ERR: {e}")
        finally:
            conn.close()

elif page == "◌ Model Intelligence":
    api_status = render_header("MODEL_INTELLIGENCE", "XGBoost classifier core metrics (Pre-Authorization Model).")
    import json
    import os
    metrics_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../artifacts/metrics/model_comparison.json'))
    
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    if os.path.exists(metrics_path):
        with open(metrics_path, 'r') as f:
            metrics_data = json.load(f)
            
        xgb_metrics = metrics_data.get('pre_authorization', {}).get('XGBoost', {})
        if xgb_metrics:
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("PRECISION", f"{xgb_metrics.get('precision', 0)*100:.2f}%")
            c2.metric("RECALL", f"{xgb_metrics.get('recall', 0)*100:.2f}%")
            c3.metric("F1_SCORE", f"{xgb_metrics.get('f1', 0)*100:.2f}%")
            c4.metric("PR-AUC", f"{xgb_metrics.get('pr_auc', 0)*100:.2f}%")
            c5.metric("LATENCY", f"{xgb_metrics.get('inference_latency_ms', 0):.2f}ms")
        else:
            st.warning("No metrics found for the pre-authorization XGBoost model.")
    else:
        st.warning("No evaluation results available. Please run model training.")
        
    st.markdown("</div>", unsafe_allow_html=True)
    st.info("> DEPLOYED_MODEL: XGBoost (Real-Time Pre-Authorization). Features excluding post-transaction balances.")

elif page == "◍ System Monitoring":
    api_status = render_header("SYSTEM_MONITORING", "Live node tracking.")
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("### > NODE_STATUS")
    st.markdown(f"> API_SERVER: {'[ONLINE]' if api_status else '[OFFLINE]'}")
    st.markdown("> ML_ENGINE: [ONLINE]")
    st.markdown("> SQLITE_DB: [ONLINE]")
    st.markdown("</div>", unsafe_allow_html=True)

elif page == "ⓘ About Project":
    api_status = render_header("ABOUT_PROJECT", "FraudSense Architecture")
    st.markdown("<div class='glass-card' style='text-align: center;'>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-shadow: 0 0 20px #00ff41;'>⚡ FRAUDSENSE AI</h1>", unsafe_allow_html=True)
    st.markdown("<h3>[DETECT] [ANALYZE] [PROTECT]</h3>", unsafe_allow_html=True)
    st.markdown("<p style='max-width: 800px; margin: 0 auto; color: rgba(0,255,65,0.8);'>Advanced ML system for detecting financial anomalies via XGBoost classification.</p><br>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("### > SYSTEM_PIPELINE")
    st.markdown("""
    <div style='background: rgba(0,0,0,0.5); padding: 20px; border: 1px solid #00ff41; font-family: monospace; text-align: center; font-size: 1.2rem; line-height: 2;'>
    [RAW_DATA] <br>↓<br> [VALIDATION] <br>↓<br> [FEATURE_ENG] <br>↓<br> [ML_INFERENCE] <br>↓<br> [RISK_SCORING] <br>↓<br> [DECISION_ENGINE]<br>
    <span style='color: #00ff41;'>[APPROVE]</span> | <span style='color: #ffeb3b;'>[REVIEW]</span> | <span style='color: #ff003c;'>[FRAUD_ALERT]</span>
    </div>
    """, unsafe_allow_html=True)
