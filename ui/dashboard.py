import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import datetime
import plotly.express as px
from database import db
from ui import roadmap

def render_heatmap(activity_data):
    # Prepare date range for the last 12 months
    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=365)
    
    date_range = [start_date + datetime.timedelta(days=x) for x in range(366)]
    
    # Structure data into weekly grid: 7 rows (Mon-Sun), 53 columns
    # We will map dates to weekdays (0-6) and week numbers of the year
    # Plotly Heatmap: x = week number/dates, y = weekday, z = activity level
    
    z_values = []
    text_values = []
    
    # We want a grid of 7 rows (Monday to Sunday)
    for weekday in range(7):
        row_z = []
        row_text = []
        for date in date_range:
            if date.weekday() == weekday:
                date_str = date.strftime("%Y-%m-%d")
                act = activity_data.get(date_str, {"attempts": 0, "solved": 0})
                
                # Activity levels
                # 0 = No activity
                # 1 = Attempted
                # 2 = Solved
                # 3 = Multiple solved
                if act["solved"] > 1:
                    level = 3
                elif act["solved"] == 1:
                    level = 2
                elif act["attempts"] > 0:
                    level = 1
                else:
                    level = 0
                    
                row_z.append(level)
                row_text.append(f"{date_str}<br>Attempts: {act['attempts']}<br>Solved: {act['solved']}")
        z_values.append(row_z)
        text_values.append(row_text)
        
    # Standardize column sizes (each week should have 7 days, padding if needed)
    max_len = max(len(row) for row in z_values)
    for i in range(7):
        while len(z_values[i]) < max_len:
            z_values[i].insert(0, 0)
            text_values[i].insert(0, "")
            
    # Weekday labels
    weekdays_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    
    # Weeks labels (representing month starts)
    x_labels = []
    current_month = None
    for idx, date in enumerate(date_range):
        if date.weekday() == 0:  # Only label on Mondays
            month_name = date.strftime("%b")
            if month_name != current_month:
                x_labels.append(month_name)
                current_month = month_name
            else:
                x_labels.append("")
                
    while len(x_labels) < max_len:
        x_labels.insert(0, "")
        
    fig = go.Figure(data=go.Heatmap(
        z=z_values,
        y=weekdays_labels,
        text=text_values,
        hoverinfo="text",
        colorscale=[
            [0.0, "#1e1e1e"],      # No activity (Dark grey for dark mode theme)
            [0.33, "#107c41"],     # Green: Attempted
            [0.66, "#ffc107"],     # Yellow: Solved
            [1.0, "#0078d4"]       # Blue: Multiple solved
        ],
        showscale=False,
        xgap=3,
        ygap=3
    ))
    
    fig.update_layout(
        height=180,
        margin=dict(t=5, b=5, l=5, r=5),
        yaxis=dict(autorange="reversed", showgrid=False, zeroline=False, tickmode="array", tickvals=list(range(7)), ticktext=weekdays_labels),
        xaxis=dict(showgrid=False, zeroline=False, tickmode="array", tickvals=list(range(max_len)), ticktext=x_labels),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    return fig

def generate_progress_report(streak_info, solved_problems, total_problems, success_rate, coding_hours, total_jobs, all_submissions, topic_stats):
    report = f"""# Spark Practice Hub - Progress Report
Generated on: {datetime.date.today().strftime("%Y-%m-%d")}

## 📊 Summary Statistics
*   🔥 Current Streak: {streak_info['current_streak']} Days
*   🏆 Longest Streak: {streak_info['longest_streak']} Days
*   ✅ Problems Solved: {solved_problems} / {total_problems}
*   📈 Success Rate: {success_rate}%
*   ⌛ Coding Time: {coding_hours} Hours
*   ⚙️ Spark Jobs Run: {total_jobs}
*   🎯 Total Attempts: {len(all_submissions)}

## 🔍 Spark Topic Diagnostics
"""
    if topic_stats:
        for t, s_val in topic_stats.items():
            solved = s_val["solved"]
            attempts = s_val["attempts"]
            total = s_val["total"]
            rate = 0.0
            classification = "Neutral/Untouched"
            if attempts > 0:
                rate = (solved / attempts) * 100
                if rate < 50 or (attempts > 1 and solved == 0):
                    classification = "Weak (Needs Focus)"
                elif rate >= 80:
                    classification = "Strong"
            
            report += f"*   **{t}**:\n"
            report += f"    - Total problems in system: {total}\n"
            report += f"    - Solved: {solved}\n"
            report += f"    - Attempts: {attempts}\n"
            report += f"    - Success Rate: {round(rate, 1)}%\n"
            report += f"    - Classification: {classification}\n"
    else:
        report += "\nNo topic diagnostic data available yet.\n"

    report += "\n## 📂 Recent Submissions (Last 50 Runs)\n"
    for s in all_submissions[:50]:
        report += f"*   {s['timestamp']} | Problem: {s['problem_id']} | Status: {s['status']} | Runtime: {s['execution_time_ms']}ms | Jobs: {s['metrics'].get('jobs', 0) if s['metrics'] else 0}\n"
        
    return report

def show():
    db.init_db()
    
    # Fetch data
    streak_info = db.get_streak_stats()
    all_submissions = db.get_submissions()
    activity_data = db.get_daily_activity()
    problems = db.get_problems()
    
    # Calculate stats
    total_problems = len(problems)
    solved_problems = len(set(s["problem_id"] for s in all_submissions if s["status"] == "PASS"))
    attempted_problems = len(set(s["problem_id"] for s in all_submissions))
    
    success_rate = 0
    if attempted_problems > 0:
        success_rate = int((solved_problems / attempted_problems) * 100)
        
    total_jobs = sum(s["metrics"].get("jobs", 0) for s in all_submissions if s["metrics"])
    total_time_s = sum(s.get("execution_time_ms", 0) for s in all_submissions) / 1000.0
    coding_hours = round(total_time_s / 3600.0, 2)
    
    # Process problem difficulty & topic statistics early
    solved_ids = set(s["problem_id"] for s in all_submissions if s["status"] == "PASS")
    diff_stats = {"Easy": {"total": 0, "solved": 0}, "Medium": {"total": 0, "solved": 0}, "Hard": {"total": 0, "solved": 0}}
    topic_stats = {}
    
    if problems:
        for p in problems:
            d = p["difficulty"]
            cat = p["category"]
            p_id = p["id"]
            
            # Difficulty
            if d in diff_stats:
                diff_stats[d]["total"] += 1
                if p_id in solved_ids:
                    diff_stats[d]["solved"] += 1
                    
            # Topic
            if cat not in topic_stats:
                topic_stats[cat] = {"total": 0, "solved": 0, "attempts": 0, "failed_attempts": 0}
            topic_stats[cat]["total"] += 1
            if p_id in solved_ids:
                topic_stats[cat]["solved"] += 1
                
        # Count attempts per category
        for s in all_submissions:
            p_id = s["problem_id"]
            prob_obj = next((p for p in problems if p["id"] == p_id), None)
            if prob_obj:
                cat = prob_obj["category"]
                if cat in topic_stats:
                    topic_stats[cat]["attempts"] += 1
                    if s["status"] != "PASS":
                        topic_stats[cat]["failed_attempts"] += 1

    # Header with download report button
    col_t1, col_t2 = st.columns([4, 1.2])
    with col_t1:
        st.markdown("<h1 style='color: #ff4b4b;'>⚡ Spark Practice Hub</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color: #888;'>Master PySpark, track execution internals, and crack your interviews!</p>", unsafe_allow_html=True)
    with col_t2:
        st.write("")  # Padding
        st.write("")
        report_md = generate_progress_report(
            streak_info, solved_problems, total_problems, success_rate, 
            coding_hours, total_jobs, all_submissions, topic_stats
        )
        st.download_button(
            label="📥 Download Progress Report",
            data=report_md,
            file_name="spark_practice_report.md",
            mime="text/markdown",
            use_container_width=True
        )
        
    # Display Stats Cards
    st.write("---")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🔥 Current Streak", f"{streak_info['current_streak']} Days")
    with col2:
        st.metric("🏆 Longest Streak", f"{streak_info['longest_streak']} Days")
    with col3:
        st.metric("✅ Problems Solved", f"{solved_problems} / {total_problems}")
    with col4:
        st.metric("📈 Success Rate", f"{success_rate}%")
        
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.metric("⌛ Coding Time", f"{coding_hours} Hrs")
    with col6:
        st.metric("⚙️ Spark Jobs Run", f"{total_jobs}")
    with col7:
        st.metric("🎯 Total Attempts", len(all_submissions))
    with col8:
        st.metric("📂 Total Problems", total_problems)
        
    st.write("---")
    st.subheader("📆 Contribution Graph")
    heatmap_fig = render_heatmap(activity_data)
    st.plotly_chart(heatmap_fig, use_container_width=True)
    
    # Legend
    col_l1, col_l2, col_l3, col_l4 = st.columns(4)
    with col_l1:
        st.markdown("<span style='color: #888;'>■</span> No Activity", unsafe_allow_html=True)
    with col_l2:
        st.markdown("<span style='color: #107c41;'>■</span> Attempted (Incorrect)", unsafe_allow_html=True)
    with col_l3:
        st.markdown("<span style='color: #ffc107;'>■</span> Solved (Correct)", unsafe_allow_html=True)
    with col_l4:
        st.markdown("<span style='color: #0078d4;'>■</span> Multiple Solved", unsafe_allow_html=True)
        
    st.write("---")
    st.subheader("📊 Topic & Difficulty Analytics")
    
    if not problems:
        st.info("No problems imported yet. Navigate to 'Import Problems' in the sidebar to upload your practice problems workbook.")
        st.write("---")
    else:
        # Render UIs
        col_an1, col_an2 = st.columns(2)
        
        with col_an1:
            # Plotly Difficulty Chart
            diff_data = []
            for d, s_val in diff_stats.items():
                diff_data.append({"Difficulty": d, "Type": "Solved", "Count": s_val["solved"]})
                diff_data.append({"Difficulty": d, "Type": "Remaining", "Count": max(0, s_val["total"] - s_val["solved"])})
            df_diff = pd.DataFrame(diff_data)
            fig_diff = px.bar(df_diff, x="Difficulty", y="Count", color="Type", title="Solved vs. Remaining by Difficulty",
                              color_discrete_map={"Solved": "#107c41", "Remaining": "#333333"})
            fig_diff.update_layout(height=280, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", legend_title="")
            st.plotly_chart(fig_diff, use_container_width=True)
            
        with col_an2:
            # Plotly Topic Chart
            topic_data = []
            for t, s_val in topic_stats.items():
                topic_data.append({"Topic": t, "Type": "Solved", "Count": s_val["solved"]})
                topic_data.append({"Topic": t, "Type": "Remaining", "Count": max(0, s_val["total"] - s_val["solved"])})
            df_topic = pd.DataFrame(topic_data)
            fig_topic = px.bar(df_topic, y="Topic", x="Count", color="Type", orientation="h", title="Solved vs. Remaining by Spark Topic",
                               color_discrete_map={"Solved": "#0078d4", "Remaining": "#333333"})
            fig_topic.update_layout(height=280, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", legend_title="")
            st.plotly_chart(fig_topic, use_container_width=True)
            
        # Weak topics analysis
        st.write("###### 🔍 Topic Diagnostics & Weak Areas")
        col_w1, col_w2 = st.columns(2)
        
        weak_topics = []
        strong_topics = []
        
        for t, s_val in topic_stats.items():
            solved = s_val["solved"]
            attempts = s_val["attempts"]
            failed = s_val["failed_attempts"]
            
            if attempts > 0:
                pass_rate = (solved / attempts) * 100
                # Weak criteria: Fail rate >= 50% or attempts > 0 with 0 solved
                if pass_rate < 50 or (attempts > 1 and solved == 0):
                    weak_topics.append((t, round(pass_rate, 1), attempts))
                elif pass_rate >= 80:
                    strong_topics.append((t, round(pass_rate, 1)))
            elif s_val["total"] > 0:
                # Not yet attempted
                pass
                
        with col_w1:
            st.markdown("<h5 style='color: #ff4b4b;'>⚠️ Weak Spark Topics (Needs Focus)</h5>", unsafe_allow_html=True)
            if weak_topics:
                for wt, rate, atts in sorted(weak_topics, key=lambda x: x[1]):
                    st.warning(f"**{wt}** — Success Rate: {rate}% ({atts} attempts)")
            else:
                st.info("No weak topics identified yet. Keep practicing!")
                
        with col_w2:
            st.markdown("<h5 style='color: #107c41;'>💪 Strong Spark Topics</h5>", unsafe_allow_html=True)
            if strong_topics:
                for st_name, rate in sorted(strong_topics, key=lambda x: x[1], reverse=True):
                    st.success(f"**{st_name}** — Success Rate: {rate}%")
            else:
                st.info("No strong topics identified yet. Solve more problems to build strength.")
                
        st.write("---")
        
    # Active Roadmaps Progress
    st.subheader("🗺️ Active Roadmaps Progress")
    opted_roadmaps = db.get_opted_roadmaps()
    has_active_roadmap = False
    for level, opted in opted_roadmaps.items():
        if opted:
            has_active_roadmap = True
            # Filter problems for this level
            level_probs = roadmap.get_roadmap_problems(level, problems)
            total = len(level_probs)
            solved_count = sum(1 for p in level_probs if p["id"] in solved_ids)
            pct = int((solved_count / total * 100)) if total > 0 else 0
            
            col_rm1, col_rm2 = st.columns([4, 1])
            with col_rm1:
                st.write(f"**{level} Roadmap** ({solved_count}/{total} solved)")
                st.progress(pct / 100.0)
            with col_rm2:
                st.write("")
                if st.button("Resume Path", key=f"resume_rm_{level}"):
                    st.session_state["selected_roadmap_level"] = level
                    st.session_state["active_page"] = "🗺️ Learning Roadmaps"
                    st.rerun()
    if not has_active_roadmap:
        st.info("You haven't opted into any roadmaps yet. Go to 'Learning Roadmaps' in the sidebar to start a structured learning path!")
        
    st.write("---")
    
    # Goals and Progress
    st.subheader("🎯 Goals & Progress")
    goals = db.get_goals()
    if not goals:
        # Save a default monthly goal if none exists
        today = datetime.date.today()
        month_end = (today.replace(day=28) + datetime.timedelta(days=4)).replace(day=1) - datetime.timedelta(days=1)
        db.save_goal("Monthly", 15, 0, today.strftime("%Y-%m-%d"), month_end.strftime("%Y-%m-%d"))
        goals = db.get_goals()
        
    for g in goals:
        goal_type = g["type"]
        target = g["target"]
        
        # Recalculate progress based on current actuals and goal criteria
        g_start = g["start_date"]
        g_end = g["end_date"]
        if goal_type == "Streak":
            active_dates = sorted([
                datetime.datetime.strptime(d, "%Y-%m-%d").date()
                for d in activity_data
                if activity_data[d]["solved"] > 0 and g_start <= d <= g_end
            ])
            if active_dates:
                longest_streak = 1
                temp_streak = 1
                for idx in range(1, len(active_dates)):
                    if (active_dates[idx] - active_dates[idx-1]).days == 1:
                        temp_streak += 1
                        if temp_streak > longest_streak:
                            longest_streak = temp_streak
                    elif (active_dates[idx] - active_dates[idx-1]).days == 0:
                        continue
                    else:
                        temp_streak = 1
                progress = longest_streak
            else:
                progress = 0
        else:
            solved_in_period = set(
                s["problem_id"]
                for s in all_submissions
                if s["status"] == "PASS" and g_start <= s["timestamp"][:10] <= g_end
            )
            progress = len(solved_in_period)

        percent = min(int((progress / target) * 100), 100)
        
        st.write(f"**{goal_type} Goal:** Solve {target} problems by {g['end_date']}.")
        st.progress(percent / 100.0)
        st.write(f"{progress} / {target} completed ({percent}%)")

        
    # Goal Customization Expander
    with st.expander("⚙️ Manage & Add Customized Goals"):
        st.markdown("##### Current active goals")
        for g in goals:
            col_g1, col_g2 = st.columns([4, 1])
            with col_g1:
                st.write(f"**{g['type']}** — Target: {g['target']} (Start: {g['start_date']} | End: {g['end_date']})")
            with col_g2:
                if st.button("Delete", key=f"del_goal_{g['id']}"):
                    db.delete_goal(g['id'])
                    st.success("Goal deleted successfully!")
                    st.rerun()
                    
        st.write("---")
        st.markdown("##### Set a new goal")
        with st.form("add_goal_form", clear_on_submit=True):
            g_type = st.selectbox("Goal Type", ["Daily", "Weekly", "Monthly", "Streak"])
            g_target = st.number_input("Target Problems", min_value=1, value=5)
            
            # Default dates
            today_dt = datetime.date.today()
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                g_start = st.date_input("Start Date", today_dt)
            with col_d2:
                g_end = st.date_input("End Date", today_dt + datetime.timedelta(days=30))
                
            submit_goal = st.form_submit_button("Set Goal")
            if submit_goal:
                db.save_goal(
                    goal_type=g_type,
                    target=g_target,
                    progress=0,
                    start_date=g_start.strftime("%Y-%m-%d"),
                    end_date=g_end.strftime("%Y-%m-%d")
                )
                st.success("New goal added successfully!")
                st.rerun()
        
    # Today's Mission Recommendation
    st.write("---")
    st.subheader("🚀 Today's Mission")
    solved_ids = set(s["problem_id"] for s in all_submissions if s["status"] == "PASS")
    unsolved = [p for p in problems if p["id"] not in solved_ids]
    
    if unsolved:
        mission_prob = unsolved[0] # Pick the first unsolved
        st.info(f"**Today's Mission:** [{mission_prob['id']}] **{mission_prob['title']}** ({mission_prob['difficulty']})")
        st.write(mission_prob["description"])
    else:
        st.success("🎉 You've solved all problems in the system! Good job!")
