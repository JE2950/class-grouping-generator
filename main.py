import streamlit as st
import pandas as pd
import networkx as nx
from random import shuffle, seed
import time

st.set_page_config(page_title="Class Grouping Generator", layout="wide")

st.title("🧑‍🏫 Class Group Generator (Friendship Guaranteed)")
st.write("""
Upload a CSV of pupils with:
- `Name`, `Gender` (M/F), `SEN` (Yes/No), `Attainment` (High/Medium/Low)
- `Friend1`–`Friend5`: five chosen friends
- `Avoid1`–`Avoid3`: pupils to avoid
""")

uploaded = st.file_uploader("📤 Upload your CSV", type="csv")

if uploaded:
    df = pd.read_csv(uploaded).fillna("")
    st.success("File uploaded!")

    def assign_classes(df, class_size=20, max_attempts=1000):
        all_names = df["Name"].tolist()

        # Build student graph
        G = nx.DiGraph()
        for _, row in df.iterrows():
            friends = [row[f"Friend{i}"] for i in range(1, 6) if row[f"Friend{i}"]]
            avoids = [row[f"Avoid{i}"] for i in range(1, 4) if row[f"Avoid{i}"]]
            G.add_node(row["Name"],
                       gender=row["Gender"],
                       sen=row["SEN"],
                       attainment=row["Attainment"],
                       friends=friends,
                       avoid=avoids)

        for attempt in range(max_attempts):
            students = list(G.nodes)
            shuffle(students)
            num_classes = len(students) // class_size
            classes = [[] for _ in range(num_classes)]
            placed = set()

            def can_add(student, group):
                if len(group) >= class_size:
                    return False
                s_data = G.nodes[student]
                for peer in group:
                    if peer in s_data["avoid"] or student in G.nodes[peer]["avoid"]:
                        return False
                return True

            def place_with_friend(student):
                s_friends = G.nodes[student]["friends"]
                for friend in s_friends:
                    for group in classes:
                        if friend in group and can_add(student, group):
                            group.append(student)
                            placed.add(student)
                            return True
                return False

            def place_student(student):
                if place_with_friend(student):
                    return True
                # Try building a new group starting from this student
                for group in classes:
                    if not group and can_add(student, group):
                        group.append(student)
                        placed.add(student)
                        # Now try to bring one of their friends
                        for friend in G.nodes[student]["friends"]:
                            if friend not in placed and can_add(friend, group):
                                group.append(friend)
                                placed.add(friend)
                                return True
                        # If no friend can join, undo
                        group.pop()
                        placed.remove(student)
                return False

            for student in students:
                if student not in placed:
                    if not place_student(student):
                        break  # this attempt fails
            if len(placed) == len(students):
                return classes  # success

        return None  # failed after max_attempts

    with st.spinner("Generating class groups... this may take a few seconds"):
        result = assign_classes(df)

    if result:
        st.header("📋 Class Lists")
        output_rows = []
        for i, group in enumerate(result, start=1):
            st.subheader(f"Class {i} ({len(group)} pupils)")
            st.write(group)
            for name in group:
                output_rows.append({"Name": name, "Class": f"Class {i}"})
        export_df = pd.DataFrame(output_rows)
        st.download_button("📥 Download CSV", export_df.to_csv(index=False).encode("utf-8"), "assignments.csv")
    else:
        st.error("❌ Could not generate valid groupings after many attempts. Try loosening avoid constraints or rechecking data.")
