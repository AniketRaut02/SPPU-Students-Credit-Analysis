import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import plotly.express as px  

# ---------------- CONFIGURATION ---------------- #
st.set_page_config(page_title="SPPU Credit & Prediction System", layout="wide")

# ---------------- GRADE LOGIC ---------------- #
def get_grade(marks):
    if marks >= 90: return ("O", 10)
    elif marks >= 80: return ("A+", 9)
    elif marks >= 70: return ("A", 8)
    elif marks >= 60: return ("B+", 7)
    elif marks >= 50: return ("B", 6)
    elif marks >= 45: return ("C", 5)
    elif marks >= 40: return ("P", 4)
    else: return ("F", 0)

# ---------------- DECOUPLED STRENGTH CALCULATION ---------------- #
def calculate_theory_strength(past_df):
    past_df.columns = past_df.columns.str.strip().str.capitalize()
    
    th_df = past_df[past_df['Type'].str.upper() == 'TH']
    
    if th_df.empty:
        return 0.60 
        
    total_gp = 0
    total_credits = 0
    
    for _, row in th_df.iterrows():
        total_marks = row['Total'] if 'Total' in row else (row['Internal'] + row['External'])
        _, gp = get_grade(total_marks)
        credits = row['Credits'] if 'Credits' in row else 3 
        total_gp += (gp * credits)
        total_credits += credits
        
    th_sgpa = total_gp / total_credits if total_credits > 0 else 0
    th_percentage = max(0, (th_sgpa - 0.75) * 10) 
    
    return th_percentage / 100.0, th_sgpa, th_percentage

# ---------------- WEIGHTED PREDICTION MODEL ---------------- #
def predict_endsem_performance(df, subject, insem_marks, attendance, theory_multiplier):
    sub_df = df[(df['Subject'] == subject) & (df['Type'] == 'TH')]
    
    if len(sub_df) < 2:
        return (insem_marks / 30.0) * 70.0 
        
    X = sub_df[['Internal', 'Attendance']]
    y = sub_df['External']
    
    model = LinearRegression()
    model.fit(X, y)
    
    input_data = pd.DataFrame([[insem_marks, attendance]], columns=['Internal', 'Attendance'])
    base_ml_prediction = model.predict(input_data)[0]
    
    relative_strength = theory_multiplier / 0.65 
    historical_component = base_ml_prediction * relative_strength
    current_momentum = (insem_marks / 30.0) * 70.0
    
    final_prediction = (historical_component * 0.70) + (current_momentum * 0.30)
    
    return max(0, min(70, final_prediction))

# ---------------- UI & DATA LOADING ---------------- #
st.title("🎓 SPPU Credit Analysis & Prediction System")
uploaded_file = st.sidebar.file_uploader("Upload Past Year Dataset (CSV)", type=["csv"])

df = None
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip().str.capitalize()
    if 'Type' not in df.columns:
        df['Type'] = 'TH'
    df['Total'] = df['Internal'] + df['External']
    df['Subject'] = df['Subject'].astype(str)

tab1, tab2 = st.tabs(["📊 Dashboard Analysis", "🤖 Performance Predictor"])

# ---------------- TAB 1: DASHBOARD ---------------- #
with tab1:
    if df is not None:
        st.subheader("📄 Historical Dataset Preview")
        st.dataframe(df.head(10), use_container_width=True)
        st.markdown("---")
        
        # --- SECTION 1: GLOBAL DATASET PERFORMANCE ---
        st.subheader("📊 Global Dataset Performance")
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Avg Overall Score", f"{df['Total'].mean():.2f}")
        col_m2.metric("Pass Rate (Overall)", f"{(df['Total'] >= 40).mean()*100:.1f}%")
        col_m3.metric("Students Analyzed", df['Student_id'].nunique())
        st.markdown("---")

        # --- SECTION 2: GLOBAL CHARTS ---
        st.subheader("📈 Global Dataset Trends")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Grade Distribution**")
            df_temp = df.copy()
            df_temp['Grade'] = df_temp['Total'].apply(lambda x: get_grade(x)[0])
            grade_order = ['O','A+','A','B+','B','C','P','F']
            grade_counts = df_temp['Grade'].value_counts().reindex(grade_order).fillna(0).reset_index()
            grade_counts.columns = ['Grade', 'Count']
            
            fig1 = px.bar(grade_counts, x='Grade', y='Count', color='Grade', 
                          color_discrete_sequence=px.colors.sequential.Viridis)
            fig1.update_traces(hovertemplate="<b>Grade: %{x}</b><br>Total Students: %{y}<br><i>This bar shows how many students secured an %{x} grade.</i><extra></extra>")
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.markdown("**Subject Performance (EndSem Avg)**")
            sub_avg = df.groupby(['Subject', 'Type'])['External'].mean().reset_index()
            
            fig2 = px.bar(sub_avg, x='Subject', y='External', color='Type', barmode='group',
                          color_discrete_sequence=px.colors.sequential.Magma)
            fig2.add_hline(y=df['External'].mean(), line_dash="dash", line_color="red", annotation_text="Global Avg")
            fig2.update_traces(hovertemplate="<b>Subject: %{x}</b><br>Avg EndSem Marks: %{y:.1f}<br><i>This bar represents the dataset's average external marks for this subject.</i><extra></extra>")
            st.plotly_chart(fig2, use_container_width=True)

        col3, col4 = st.columns(2)
        with col3:
            st.markdown("**Heatmap: Corelation Analysis**")
            fig3, ax3 = plt.subplots()
            numeric_df = df[['Internal', 'External', 'Attendance', 'Total']]
            sns.heatmap(numeric_df.corr(), annot=True, cmap="coolwarm", fmt=".2f")
            st.pyplot(fig3)
            
        with col4:
            st.markdown("**Attendance vs Total Score**")
            fig4, ax4 = plt.subplots()
            sns.regplot(data=df, x='Attendance', y='Total', scatter_kws={'alpha':0.3}, line_kws={"color":"red"})
            st.pyplot(fig4)
            
        st.markdown("---")

        # --- SECTION 3: GLOBAL SUBJECT TOUGHNESS (UPDATED LOGIC) ---
        st.subheader("🔥 Global Subject Toughness (Relative Scale)")
        st.caption("This uses Relative Scaling. The hardest subject in the dataset is locked to a 10, and all other subjects are ranked proportionally. This prevents high overall pass rates from hiding subject difficulty.")
        
        # 1. Get average total marks per subject
        tough_df = df.groupby(['Subject', 'Type'])['Total'].mean().reset_index()
        
        # 2. Calculate baseline difficulty (points lost from 100)
        tough_df['Baseline_Diff'] = 100 - tough_df['Total']
        
        # 3. Find the maximum difficulty (the toughest subject)
        max_diff = tough_df['Baseline_Diff'].max()
        
        # 4. Scale everything relative to the maximum difficulty so the toughest gets exactly 10
        if max_diff > 0:
            tough_df['Toughness'] = (tough_df['Baseline_Diff'] / max_diff) * 10
        else:
            tough_df['Toughness'] = 0 # Failsafe if everyone scored 100
            
        tough_df = tough_df.sort_values(by='Toughness', ascending=False)
        
        fig_tough = px.bar(tough_df, x='Subject', y='Toughness', color='Toughness',
                           color_continuous_scale='Reds', text_auto='.1f')
        fig_tough.update_traces(textposition='outside', 
                                hovertemplate="<b>Subject: %{x}</b><br>Relative Toughness: %{y:.2f} / 10<br><i>A score of 10 indicates the toughest subject in this specific dataset.</i><extra></extra>")
        fig_tough.update_layout(yaxis_range=[0,11]) # Set to 11 to give text labels room to breathe
        st.plotly_chart(fig_tough, use_container_width=True)

        st.markdown("---")

        # --- SECTION 4: INDIVIDUAL STUDENT LOOKUP ---
        st.subheader("🧑‍🎓 Individual Student Performance")
        student_list = df['Student_id'].unique()
        selected_student = st.selectbox("Select a Student ID to view their breakdown:", student_list)
        
        student_data = df[df['Student_id'] == selected_student]
        
        th_data = student_data[student_data['Type'] == 'TH']
        pr_data = student_data[student_data['Type'] == 'PR']
        
        c_th, c_pr, c_tot = st.columns(3)
        c_th.metric("Avg Theory Total (InSem+EndSem)", f"{th_data['Total'].mean():.1f}" if not th_data.empty else "N/A")
        c_pr.metric("Avg Practical Total", f"{pr_data['Total'].mean():.1f}" if not pr_data.empty else "N/A")
        c_tot.metric("Overall Subjects Passed", f"{len(student_data[student_data['Total'] >= 40])} / {len(student_data)}")
        
        st.dataframe(student_data[['Subject', 'Type', 'Internal', 'External', 'Total', 'Attendance']], use_container_width=True)
        
        # --- INDIVIDUAL VS GLOBAL AVG CHARTS ---
        st.markdown("#### Subject Marks vs Global Average")
        global_sub_avg = df.groupby(['Subject', 'Type'])['Total'].mean().reset_index()
        global_sub_avg.rename(columns={'Total': 'Global_Avg'}, inplace=True)
        student_data_merged = pd.merge(student_data, global_sub_avg, on=['Subject', 'Type'], how='left')
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.markdown("**Theory Subjects (TH)**")
            th_merged = student_data_merged[student_data_merged['Type'] == 'TH']
            if not th_merged.empty:
                th_melted = th_merged.melt(id_vars='Subject', value_vars=['Total', 'Global_Avg'], var_name='Metric', value_name='Marks')
                th_melted['Metric'] = th_melted['Metric'].replace({'Total': 'Student Score', 'Global_Avg': 'Global Average'})
                
                fig_th = px.bar(th_melted, x='Subject', y='Marks', color='Metric', barmode='group',
                                color_discrete_sequence=px.colors.qualitative.Set2)
                fig_th.update_traces(hovertemplate="<b>%{x}</b><br>Marks: %{y:.1f}<br><i>This bar represents the %{data.name} for this specific subject.</i><extra></extra>")
                st.plotly_chart(fig_th, use_container_width=True)
            else:
                st.info("No Theory data available for this student.")

        with col_chart2:
            st.markdown("**Practical Subjects (PR)**")
            pr_merged = student_data_merged[student_data_merged['Type'] == 'PR']
            if not pr_merged.empty:
                pr_melted = pr_merged.melt(id_vars='Subject', value_vars=['Total', 'Global_Avg'], var_name='Metric', value_name='Marks')
                pr_melted['Metric'] = pr_melted['Metric'].replace({'Total': 'Student Score', 'Global_Avg': 'Global Average'})
                
                fig_pr = px.bar(pr_melted, x='Subject', y='Marks', color='Metric', barmode='group',
                                color_discrete_sequence=px.colors.qualitative.Set2)
                fig_pr.update_traces(hovertemplate="<b>%{x}</b><br>Marks: %{y:.1f}<br><i>This bar represents the %{data.name} for this specific subject.</i><extra></extra>")
                st.plotly_chart(fig_pr, use_container_width=True)
            else:
                st.info("No Practical data available for this student.")

    else:
        st.info("Upload the historical students dataset (Input 1) in the sidebar to begin.")

# ---------------- TAB 2: PREDICTOR ---------------- #
with tab2:
    st.header("🎯 SPPU EndSem Predictor")
    
    if df is None:
        st.warning("⚠️ Please upload the Past Year Dataset in the sidebar first. The model needs it to learn subject difficulty.")
    else:
        st.markdown("Upload the student's **Past Semester Results (CSV)** to calculate their True Theory Strength.")
        past_result_file = st.file_uploader("Upload Past Result (CSV)", type=["csv"], key="past_res")
        
        if past_result_file:
            past_df = pd.read_csv(past_result_file)
            th_multiplier, th_sgpa, th_percentage = calculate_theory_strength(past_df)
            
            st.success(f"**True Theory Strength Analyzed:** {th_percentage:.2f}% (Derived from {th_sgpa:.2f} Theory-Only SGPA)")
            st.caption("Note: Practical/Lab marks were isolated and removed from this calculation to prevent inflation.")
            st.markdown("---")
            
            th_subjects = df[df['Type'] == 'TH']['Subject'].unique()
            results = []
            
            st.subheader("Current Semester Inputs")
            st.caption("Expand each subject to enter your current InSem marks and attendance.")
            
            for sub in th_subjects:
                with st.expander(f"📚 {sub} - Enter Data"):
                    c1, c2 = st.columns(2)
                    in_marks = c1.slider("InSem Marks (out of 30)", 0, 30, 20, key=f"in_{sub}")
                    attendance = c2.slider("Attendance %", 0, 100, 75, key=f"att_{sub}")

                    pred_external = predict_endsem_performance(df, sub, in_marks, attendance, th_multiplier)
                    total = in_marks + pred_external
                    grade, gp = get_grade(total)
                    
                    results.append({
                        "Subject": sub,
                        "InSem (Actual)": in_marks,
                        "EndSem (Predicted)": round(pred_external, 2),
                        "Total Marks": round(total, 2),
                        "Grade": grade,
                        "GP": gp,
                        "Credits": 3
                    })

            if st.button("Generate Final Prediction", type="primary"):
                res_df = pd.DataFrame(results)
                st.markdown("### 🏆 Predicted Semester Result")
                st.dataframe(res_df[['Subject', 'InSem (Actual)', 'EndSem (Predicted)', 'Total Marks', 'Grade']], use_container_width=True)
                
                total_gp = sum(res_df['GP'] * res_df['Credits'])
                total_credits = sum(res_df['Credits'])
                final_sgpa = total_gp / total_credits if total_credits > 0 else 0
                
                has_failed = "F" in res_df['Grade'].values
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Predicted SGPA", f"{final_sgpa:.2f}")
                m2.metric("Theory Credits Earned", 0 if has_failed else total_credits)
                
                if has_failed:
                    m3.error("RESULT: FAIL (Backlog Expected)")
                else:
                    m3.success("RESULT: PASS")