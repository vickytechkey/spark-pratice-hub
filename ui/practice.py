import streamlit as st
from streamlit_ace import st_ace
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
            
    # Expander to switch problem via table selector
    with st.expander("🔍 Switch Problem (Table Selector)", expanded=False):
        # Retrieve list of solved/completed problems
        submissions = db.get_submissions()
        solved_ids = set(s["problem_id"] for s in submissions if s["status"] == "PASS")
        
        col_f1, col_f2, col_f3, col_f4 = st.columns([2, 1, 1, 1])
        with col_f1:
            search_query = st.text_input("🔍 Search Title / Concept", "", key="practice_search")
        with col_f2:
            difficulty_filter = st.selectbox("Difficulty", ["All", "Easy", "Medium", "Hard"], key="practice_diff")
        with col_f3:
            status_filter = st.selectbox("Status", ["All", "Completed", "Pending"], key="practice_status")
        with col_f4:
            page_size = st.selectbox("Display Limit", [5, 10, 20, 50, 100], index=1, key="practice_limit")
            
        # Get all problems
        all_probs_raw = db.get_problems()
        
        # Apply filters
        filtered_probs = []
        for p in all_probs_raw:
            # Search
            if search_query:
                q = search_query.lower()
                title_match = q in p["title"].lower()
                desc_match = q in p["description"].lower()
                concept_match = q in p.get("concepts", "").lower() if p.get("concepts") else False
                if not (title_match or desc_match or concept_match):
                    continue
            
            # Difficulty
            if difficulty_filter != "All" and p["difficulty"] != difficulty_filter:
                continue
                
            # Status
            is_solved = p["id"] in solved_ids
            if status_filter == "Completed" and not is_solved:
                continue
            if status_filter == "Pending" and is_solved:
                continue
                
            filtered_probs.append(p)
            
        if not filtered_probs:
            st.info("No problems found matching the filters.")
        else:
            # Pagination
            total_items = len(filtered_probs)
            total_pages = max(1, (total_items + page_size - 1) // page_size)
            
            col_page, col_info = st.columns([1, 4])
            with col_page:
                page_num = st.number_input("Page", min_value=1, max_value=total_pages, value=1, key="practice_page")
            with col_info:
                st.write("")
                st.write(f"Showing {(page_num-1)*page_size + 1} - {min(page_num*page_size, total_items)} of {total_items} problems")
                
            start_idx = (page_num - 1) * page_size
            end_idx = start_idx + page_size
            page_probs = filtered_probs[start_idx:end_idx]
            
            # Display DataFrame
            display_data = []
            for p in page_probs:
                is_active = p["id"] == st.session_state["selected_problem_id"]
                status_str = "🟢 Completed" if p["id"] in solved_ids else "🟡 Pending"
                display_data.append({
                    "Active": "🎯 Active" if is_active else "",
                    "Status": status_str,
                    "ID": p["id"],
                    "Title": p["title"],
                    "Difficulty": p["difficulty"],
                    "Category": p["category"]
                })
                
            df_display = pd.DataFrame(display_data)
            
            event = st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Active": st.column_config.TextColumn("Active", width="small"),
                    "Status": st.column_config.TextColumn("Status", width="small"),
                    "ID": st.column_config.TextColumn("ID", width="small"),
                    "Title": st.column_config.TextColumn("Title"),
                    "Difficulty": st.column_config.TextColumn("Difficulty", width="small"),
                    "Category": st.column_config.TextColumn("Category"),
                },
                selection_mode="single-row",
                on_select="rerun"
            )
            
            if event and hasattr(event, "selection") and event.selection.rows:
                selected_row_idx = event.selection.rows[0]
                new_selected_id = df_display.iloc[selected_row_idx]["ID"]
                if new_selected_id != st.session_state["selected_problem_id"]:
                    st.session_state["selected_problem_id"] = new_selected_id
                    st.rerun()
    
    problem_id = st.session_state["selected_problem_id"]
    problem = db.get_problem(problem_id)
    
    # Fallback if the selected problem no longer exists in the database
    if not problem:
        problems = db.get_problems()
        if problems:
            st.session_state["selected_problem_id"] = problems[0]["id"]
            problem_id = problems[0]["id"]
            problem = problems[0]
        else:
            st.warning("No problems available. Please import problems.")
            return
            
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
        
    code_str = st_ace(
        value=default_code,
        language="python",
        theme="monokai",
        keybinding="vscode",
        font_size=14,
        tab_size=4,
        show_gutter=True,
        show_print_margin=False,
        wrap=True,
        key=f"editor_{problem_id}",
        height=350
    )
    
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
        
        col_hist_title, col_hist_btn = st.columns([5, 1])
        with col_hist_title:
            st.write("**Recent Submissions**")
        with col_hist_btn:
            if st.button("🔄 Refresh", key="btn_refresh_history", use_container_width=True):
                st.rerun()
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
