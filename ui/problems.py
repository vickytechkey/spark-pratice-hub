import streamlit as st
import pandas as pd
from database import db

def show():
    st.title("📂 Problem Bank")
    st.write("Browse and filter problems to practice your PySpark coding.")
    
    db.init_db()
    
    # Filters in a single row
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_query = st.text_input("🔍 Search by Title or Concept", "")
    with col2:
        difficulties = ["All", "Easy", "Medium", "Hard"]
        selected_difficulty = st.selectbox("Difficulty", difficulties)
    with col3:
        # Get categories dynamically
        problems_all = db.get_problems()
        categories = sorted(list(set(p["category"] for p in problems_all)))
        categories.insert(0, "All")
        selected_category = st.selectbox("Category", categories)
        
    # Get filtered problems
    problems = db.get_problems(search=search_query, difficulty=selected_difficulty, category=selected_category)
    
    # Get user submission statuses
    submissions = db.get_submissions()
    solved_ids = set(s["problem_id"] for s in submissions if s["status"] == "PASS")
    attempted_ids = set(s["problem_id"] for s in submissions)
    
    if not problems:
        st.info("No problems found matching the filters.")
        return
        
    # Build dataframe for display
    display_data = []
    for p in problems:
        p_id = p["id"]
        status = "⚪ Unsolved"
        if p_id in solved_ids:
            status = "🟢 Solved"
        elif p_id in attempted_ids:
            status = "🟡 Attempted"
            
        display_data.append({
            "Status": status,
            "ID": p_id,
            "Title": p["title"],
            "Category": p["category"],
            "Concepts": p.get("concepts", ""),
            "Difficulty": p["difficulty"],
            "Comparison Mode": p["comparison_mode"]
        })
        
    df = pd.DataFrame(display_data)
    
    # Table rendering
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Status": st.column_config.TextColumn("Status", width="small"),
            "ID": st.column_config.TextColumn("ID", width="small"),
            "Title": st.column_config.TextColumn("Title"),
            "Category": st.column_config.TextColumn("Category"),
            "Concepts": st.column_config.TextColumn("Concepts"),
            "Difficulty": st.column_config.TextColumn("Difficulty", width="small"),
        }
    )
    
    # Quick selection to practice
    st.write("---")
    st.subheader("🚀 Select Problem to Practice")
    selected_problem_id = st.selectbox(
        "Choose a problem ID to load in the practice sandbox:",
        [p["id"] for p in problems]
    )
    
    if selected_problem_id:
        prob = db.get_problem(selected_problem_id)
        if prob:
            st.markdown(f"**Selected:** {prob['title']} ({prob['difficulty']})")
            if st.button("Go to Sandbox"):
                st.session_state["active_page"] = "💻 Practice Sandbox"
                st.session_state["selected_problem_id"] = selected_problem_id
                st.rerun()
