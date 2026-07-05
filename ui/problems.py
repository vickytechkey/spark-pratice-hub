import streamlit as st
import pandas as pd
from database import db

def show():
    st.title("📂 Problem Bank")
    st.write("Browse and filter problems to practice your PySpark coding.")
    
    db.init_db()
    
    # Filters in a single row
    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
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
    with col4:
        status_filter = st.selectbox("Status", ["All", "Completed", "Pending"])
    with col5:
        page_size = st.selectbox("Display Limit", [5, 10, 20, 50, 100], index=1)
        
    # Get filtered problems
    problems = db.get_problems(search=search_query, difficulty=selected_difficulty, category=selected_category)
    
    # Get user submission statuses
    submissions = db.get_submissions()
    solved_ids = set(s["problem_id"] for s in submissions if s["status"] == "PASS")
    attempted_ids = set(s["problem_id"] for s in submissions)
    
    # Filter by completion status (completed vs pending)
    filtered_problems = []
    for p in problems:
        is_solved = p["id"] in solved_ids
        if status_filter == "Completed" and not is_solved:
            continue
        if status_filter == "Pending" and is_solved:
            continue
        filtered_problems.append(p)
        
    if not filtered_problems:
        st.info("No problems found matching the filters.")
        return
        
    # Pagination
    total_items = len(filtered_problems)
    total_pages = max(1, (total_items + page_size - 1) // page_size)
    
    col_page, col_info = st.columns([1, 4])
    with col_page:
        page_num = st.number_input("Page", min_value=1, max_value=total_pages, value=1, key="problems_page")
    with col_info:
        st.write("")
        st.write(f"Showing {(page_num-1)*page_size + 1} - {min(page_num*page_size, total_items)} of {total_items} problems")
        
    start_idx = (page_num - 1) * page_size
    end_idx = start_idx + page_size
    page_probs = filtered_problems[start_idx:end_idx]
    
    # Build dataframe for display
    display_data = []
    for p in page_probs:
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
    
    # Table rendering with selection support
    event = st.dataframe(
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
        },
        selection_mode="single-row",
        on_select="rerun"
    )
    
    # Quick selection to practice
    st.write("---")
    st.subheader("🚀 Select Problem to Practice")
    
    selected_problem_id = None
    if event and hasattr(event, "selection") and event.selection.rows:
        selected_row_idx = event.selection.rows[0]
        selected_problem_id = df.iloc[selected_row_idx]["ID"]
        
    if selected_problem_id:
        prob = db.get_problem(selected_problem_id)
        if prob:
            st.markdown(f"**Selected:** {prob['title']} ({prob['difficulty']})")
            if st.button("Go to Sandbox"):
                st.session_state["active_page"] = "💻 Practice Sandbox"
                st.session_state["selected_problem_id"] = selected_problem_id
                st.rerun()
    else:
        st.info("👆 Click on a row in the table above to select a problem, then click 'Go to Sandbox' to practice.")
