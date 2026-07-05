import streamlit as st
import pandas as pd
import json
import plotly.express as px
from database import db
from engine import runner

def show():
    st.title("💻 Practice Sandbox")
    
    db.init_db()
    
    # Session state for selected problem
    if "selected_problem_id" not in st.session_state:
        problems = db.get_problems()
        if problems:
            st.session_state["selected_problem_id"] = problems[0]["id"]
        else:
            st.warning("No problems available. Please import problems via the Import page.")
            return
            
    # Load all problems for dropdown selector
    all_probs = db.get_problems()
    prob_options = {f"{p['id']} - {p['title']} ({p['difficulty']})": p["id"] for p in all_probs}
    
    # Dropdown selector to switch problems
    selected_label = st.selectbox(
        "Select Problem",
        list(prob_options.keys()),
        index=list(prob_options.values()).index(st.session_state["selected_problem_id"]) if st.session_state["selected_problem_id"] in prob_options.values() else 0
    )
    st.session_state["selected_problem_id"] = prob_options[selected_label]
    
    problem_id = st.session_state["selected_problem_id"]
    problem = db.get_problem(problem_id)
    test_cases = db.get_test_cases(problem_id)
    
    # Spark profile selector
    profiles = db.get_profiles()
    profile_names = [p["name"] for p in profiles]
    selected_profile = st.selectbox("⚡ Spark Execution Profile", profile_names, index=0 if profile_names else None)
    
    # Create tabs for problem specs
    tab_desc, tab_input, tab_expected = st.tabs(["📝 Description", "📥 Input Datasets", "📤 Expected Output"])
    
    with tab_desc:
        col_d1, col_d2 = st.columns([3, 1])
        with col_d1:
            st.markdown(f"### {problem['title']}")
        with col_d2:
            color = "#107c41" if problem["difficulty"] == "Easy" else ("#ffc107" if problem["difficulty"] == "Medium" else "#ff4b4b")
            st.markdown(f"<span style='background-color: {color}; padding: 4px 8px; border-radius: 4px; color: white; font-weight: bold;'>{problem['difficulty']}</span>", unsafe_allow_html=True)
            
        st.markdown(f"**Category:** `{problem['category']}`")
        st.markdown("#### Description:")
        st.markdown(problem["description"])
        
        if problem["concepts"]:
            st.markdown("#### Concepts:")
            for concept in problem["concepts"].split(","):
                st.markdown(f"- `{concept.strip()}`")
                
        if problem["hints"]:
            with st.expander("💡 Hints"):
                for idx, hint in enumerate(problem["hints"].split(";")):
                    st.write(f"{idx+1}. {hint.strip()}")
                    
    # Previews of input datasets (loading using standard pandas for quick UI responsiveness)
    with tab_input:
        if test_cases:
            tc = test_cases[0] # Preview first testcase
            for key, ds_name in tc["input_datasets"].items():
                st.markdown(f"##### Input name: `{key}` (Dataset: `{ds_name}`)")
                ds = db.get_dataset(ds_name)
                if ds:
                    try:
                        if ds["type"] == "CSV":
                            preview_df = pd.read_csv(ds["file_path"]).head(10)
                        elif ds["type"] == "JSON":
                            preview_df = pd.read_json(ds["file_path"]).head(10)
                        elif ds["type"] == "PARQUET":
                            preview_df = pd.read_parquet(ds["file_path"]).head(10)
                        elif ds["type"] == "EXCEL":
                            preview_df = pd.read_excel(ds["file_path"]).head(10)
                        st.dataframe(preview_df, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error loading preview: {str(e)}")
        else:
            st.info("No test cases or inputs registered.")
            
    # Preview expected output
    with tab_expected:
        if test_cases:
            tc = test_cases[0]
            ds_name = tc["expected_output_dataset"]
            st.markdown(f"##### Expected Output Dataset: `{ds_name}`")
            ds = db.get_dataset(ds_name)
            if ds:
                try:
                    if ds["type"] == "CSV":
                        preview_df = pd.read_csv(ds["file_path"]).head(10)
                    elif ds["type"] == "JSON":
                        preview_df = pd.read_json(ds["file_path"]).head(10)
                    elif ds["type"] == "PARQUET":
                        preview_df = pd.read_parquet(ds["file_path"]).head(10)
                    elif ds["type"] == "EXCEL":
                        preview_df = pd.read_excel(ds["file_path"]).head(10)
                    st.dataframe(preview_df, use_container_width=True)
                except Exception as e:
                    st.error(f"Error loading expected output preview: {str(e)}")
        else:
            st.info("No expected output dataset registered.")
            
    # Code Editor Section
    st.write("---")
    st.subheader("🐍 Write your PySpark Solution")
    
    # Load last submission code if available
    subs = db.get_submissions(problem_id)
    default_code = """def solve(spark, inputs):
    # 'inputs' is a dictionary mapping input names to Spark DataFrames.
    # To extract a specific DataFrame, access it by its key, e.g.:
    # df = inputs['df1']
    #
    # Write your PySpark transformation logic here.
    
    df = list(inputs.values())[0]
    
    return df
"""
    if subs:
        default_code = subs[0]["code"]
        
    code_str = st.text_area("Python Code", default_code, height=300)
    
    # Execution & results
    col_btn1, col_btn2 = st.columns(2)
    run_clicked = False
    submit_clicked = False
    
    with col_btn1:
        if st.button("💻 Run Code", use_container_width=True):
            run_clicked = True
            
    with col_btn2:
        if st.button("🚀 Submit Solution", type="primary", use_container_width=True):
            submit_clicked = True
            
    if run_clicked or submit_clicked:
        submit_flag = True if submit_clicked else False
        status_action = "Submitting solution..." if submit_flag else "Running code..."
        
        with st.spinner(status_action):
            result = runner.run_solution(problem_id, code_str, selected_profile, submit=submit_flag)
            
            if result["status"] == "PASS":
                st.success("🎉 Correct! All test cases passed.")
            elif result["status"] == "FAIL":
                st.error("❌ Incorrect. One or more test cases failed.")
            else:
                st.exception(Exception(result.get("message", "Error executing code")))
                if result.get("traceback"):
                    st.code(result["traceback"], language="python")
                    
            # Output details/Previews
            if "results" in result:
                for idx, tc_res in enumerate(result["results"]):
                    tc_status = "🟢 Passed" if tc_res["passed"] else "🔴 Failed"
                    with st.expander(f"Test Case {idx+1}: {tc_status}"):
                        st.write(tc_res.get("message", ""))
                        if "actual_preview" in tc_res:
                            col_act, col_exp = st.columns(2)
                            with col_act:
                                st.markdown("**Your Output Preview:**")
                                st.dataframe(pd.DataFrame(tc_res["actual_preview"]), use_container_width=True)
                            with col_exp:
                                st.markdown("**Expected Output Preview:**")
                                st.dataframe(pd.DataFrame(tc_res["expected_preview"]), use_container_width=True)
                                
            # Performance stats
            if "metrics" in result:
                st.write("---")
                st.subheader("📊 Performance Diagnostics")
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                with col_m1:
                    st.metric("Runtime", f"{result['total_time_ms']} ms")
                with col_m2:
                    st.metric("Spark Jobs", result["metrics"]["jobs"])
                with col_m3:
                    st.metric("Spark Stages", result["metrics"]["stages"])
                with col_m4:
                    st.metric("Spark Tasks", result["metrics"]["tasks"])
                    
    # History & Performance over time
    if subs:
        st.write("---")
        st.subheader("📈 Progress History")
        
        hist_df = pd.DataFrame([
            {
                "Submission Time": s["timestamp"],
                "Status": s["status"],
                "Runtime (ms)": s["execution_time_ms"],
                "Jobs Run": s["metrics"].get("jobs", 0) if s["metrics"] else 0
            } for s in reversed(subs)
        ])
        
        # Plot run times
        fig = px.line(hist_df, x="Submission Time", y="Runtime (ms)", markers=True, title="Execution Time Trend")
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
        
        # Submission History Table
        st.write("**Recent Submissions**")
        st.dataframe(
            pd.DataFrame([
                {
                    "Time": s["timestamp"],
                    "Status": "🟢 PASS" if s["status"] == "PASS" else "🔴 FAIL",
                    "Runtime (ms)": s["execution_time_ms"],
                    "Jobs": s["metrics"].get("jobs", 0) if s["metrics"] else 0,
                    "Code Preview": s["code"][:60] + "..."
                } for s in subs
            ]),
            use_container_width=True,
            hide_index=True
        )
