import streamlit as st
import pandas as pd
import networkx as nx
from random import shuffle

st.set_page_config(page_title="Class Grouping Generator", layout="wide")

st.title("🧑‍🏫 Class Group Generator")
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

    students = list(G.nodes)
    shuffle(students)
    class_size = 20
    num_classes = len(students) // class_size
    classes = [[] for _ in range(num_classes)]

    def can_add(student, group):
        if len(group) >= class_size: return False
        s = G.nodes[student]
        for peer in group:
            if peer in s["avoid"] or student in G.nodes[peer]["avoid"]:
                return False
        return True

    def best_group(student):
        for friend in G.nodes[student]["friends"]:
            for group in classes:
                if friend in group and can_add(student, group):
                    return group
        shuffle(classes)
        for group in classes:
            if can_add(student, group):
                return group
        return None

    results = []
    for student in students:
        group = best_group(student)
        if group:
            group.append(student)
        else:
            st.warning(f"Could not place {student} with constraints.")

    st.header("📋 Class Lists")
    for i, group in enumerate(classes, start=1):
        st.subheader(f"Class {i} ({len(group)} pupils)")
        st.write(group)
        for name in group:
            results.append({"Name": name, "Class": f"Class {i}"})

    export_df = pd.DataFrame(results)
    st.download_button("📥 Download CSV", export_df.to_csv(index=False).encode("utf-8"), "assignments.csv")
