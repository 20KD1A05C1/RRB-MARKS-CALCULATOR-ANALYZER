import streamlit as st
from bs4 import BeautifulSoup
import requests
import matplotlib.pyplot as plt
import numpy as np
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import pandas as pd

st.set_page_config(page_title="RRB Score Dashboard", layout="centered")

st.title("📊 RRB Score Dashboard")

link = st.text_input("🔗 Enter Response Sheet URL")

if st.button("Calculate and Analyze Score"):

    if not link:
        st.warning("Enter valid link")
        st.stop()

    with st.spinner("Analyzing..."):
        
        headers = {
            "Accept": "text/html,application/xhtml+xml"
        }
        response = requests.get(link, headers=headers,timeout=60)
        st.write("Status Code:", response.status_code)
        st.write(response.text[:1000])
        st.write("-----------------...")
        soup = BeautifulSoup(response.text, "html.parser")

        # -------------------------
        # 👤 Student Details
        # -------------------------
        details = {}
        for row in soup.select(".main-info-pnl table tr"):
            cols = row.find_all("td")
            if len(cols) == 2:
                details[cols[0].text.strip()] = cols[1].text.strip()

        st.subheader("👤 Student Details")
        st.write(details)

        # -------------------------
        # 📊 Section-wise + Overall
        # -------------------------
        sections = {}
        current_section = "General"

        total_questions = 0
        total_attempted = 0
        total_correct = 0
        total_wrong = 0

        elements = soup.select(".section-lbl, .question-pnl")

        for el in elements:

            if "section-lbl" in el.get("class", []):
                current_section = el.text.strip()
                sections[current_section] = {
                    "correct": 0,
                    "wrong": 0,
                    "attempted": 0,
                    "total": 0
                }

            if "question-pnl" in el.get("class", []):

                total_questions += 1
                sections[current_section]["total"] += 1

                chosen = None
                tds = el.select(".menu-tbl td")

                for i, td in enumerate(tds):
                    if "Chosen Option" in td.text:
                        chosen = tds[i+1].text.strip()

                if not chosen or chosen == "--":
                    continue

                total_attempted += 1
                sections[current_section]["attempted"] += 1

                correct_ans = el.select_one(".rightAns")
                correct_option = correct_ans.text.strip()[0]

                if chosen == correct_option:
                    total_correct += 1
                    sections[current_section]["correct"] += 1
                else:
                    total_wrong += 1
                    sections[current_section]["wrong"] += 1

        final_score = total_correct - total_wrong / 3

        # -------------------------
        # 📊 Overall Summary
        # -------------------------
        st.subheader("📊 Overall Summary")

        col1, col2 = st.columns(2)
        col1.metric("Total Questions", total_questions)
        col1.metric("Attempted", total_attempted)

        col2.metric("Correct", total_correct)
        col2.metric("Wrong", total_wrong)

        st.metric("🏆 Final Score", round(final_score, 2))

        # -------------------------
        # 📋 Section Table
        # -------------------------
        st.subheader("📋 Section-wise Report")

        table_data = [["Section", "Attempted", "Correct", "Wrong", "Score"]]

        for sec, data in sections.items():
            score = data["correct"] - data["wrong"] / 3
            table_data.append([
                sec,
                data["attempted"],
                data["correct"],
                data["wrong"],
                round(score, 2)
            ])
        table_data.append([
            "Total",
            total_attempted,
            total_correct,
            total_wrong,
            round(final_score, 2)
        ])

        

        df = pd.DataFrame(table_data[1:], columns=table_data[0])
        df = df.astype(str)
        st.dataframe(df, width="stretch")

        # -------------------------
        # 📊 Performance Radar Chart
        # -------------------------
        if not sections:
            st.error("⚠️ No sections found. Unable to generate chart.")
            st.stop()
        st.subheader("📈 Performance Radar (Correct / Total) %")

        labels = list(sections.keys())
        # values = [v["correct"] for v in sections.values()]
        values = [(v["correct"] / v["total"]) * 100 if v["total"] > 0 else 0 for v in sections.values()]

        angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False)
        # values += values[:1]
        values_plot = values + values[:1]
        angles_plot  = np.concatenate((angles, [angles[0]]))

        fig = plt.figure()
        ax = plt.subplot(111, polar=True)

        ax.plot(angles_plot, values_plot)
        ax.fill(angles_plot, values_plot, alpha=0.1)

        ax.set_xticks(angles)
        ax.set_xticklabels(labels)
        ax.set_ylim(0, 100)
        ax.set_yticks([20, 40, 60, 80, 100]) 
        ax.set_yticklabels(["20%", "40%", "60%", "80%", "100%"])
        ax.set_title("Section-wise Performance (%)")
        ax.set_facecolor("#f5f5f5")
        ax.grid(True)
        st.pyplot(fig)

        from reportlab.platypus import Image

        chart_buffer = BytesIO()
        plt.savefig(chart_buffer, format='png')
        chart_buffer.seek(0)

        # -------------------------
        # 🎯 Accuracy Radar Chart
        # -------------------------
        st.subheader("🎯 Accuracy Radar (Correct / Attempted) %")

        labels = list(sections.keys())

        accuracy_values = [
            (v["correct"] / v["attempted"]) * 100 if v["attempted"] > 0 else 0
            for v in sections.values()
        ]

        angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False)

        # Close shape
        accuracy_plot = accuracy_values + accuracy_values[:1]
        angles_plot = np.concatenate((angles, [angles[0]]))

        fig2 = plt.figure()
        ax2 = plt.subplot(111, polar=True)

        ax2.plot(angles_plot, accuracy_plot)
        ax2.fill(angles_plot, accuracy_plot, alpha=0.1)

        ax2.set_xticks(angles)
        ax2.set_xticklabels(labels)

        # ✅ Fix scale to 100
        ax2.set_ylim(0, 100)
        ax2.set_yticks([20, 40, 60, 80, 100])
        ax2.set_yticklabels(["20%", "40%", "60%", "80%", "100%"])

        ax2.set_title("Section-wise Accuracy (%)")
        ax2.set_facecolor("#f5f5f5")
        ax2.grid(True)

        st.pyplot(fig2)
        acc_buffer = BytesIO()
        plt.figure(fig2.number)
        plt.savefig(acc_buffer, format='png')
        acc_buffer.seek(0)

        # -------------------------
        # 📄 PDF Report
        # -------------------------
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer)
        styles = getSampleStyleSheet()

        content = []

        content.append(Paragraph("RRB Score Report", styles['Title']))
        content.append(Spacer(1, 10))

        content.append(Paragraph(f"Name: {details.get('Candidate Name')}", styles['Normal']))
        content.append(Paragraph(f"Roll: {details.get('Roll Number')}", styles['Normal']))
        content.append(Paragraph(f"Subject: {details.get('Subject')}", styles['Normal']))
        content.append(Paragraph(f"Test Date: {details.get('Test Date')}", styles['Normal']))
        content.append(Spacer(1, 10))

        content.append(Paragraph(f"Total Questions: {total_questions}", styles['Normal']))
        content.append(Paragraph(f"Attempted: {total_attempted}", styles['Normal']))
        content.append(Paragraph(f"Correct: {total_correct}", styles['Normal']))
        content.append(Paragraph(f"Wrong: {total_wrong}", styles['Normal']))
        content.append(Paragraph(f"Final Score: {round(final_score,2)}", styles['Heading2']))

        content.append(Spacer(1, 10))

        pdf_table = Table(table_data)
        content.append(pdf_table)

        content.append(Spacer(1, 20))

        # ✅ Add radar chart image
        content.append(Paragraph("Performance Radar", styles['Heading2']))
        content.append(Spacer(1, 10))
        img = Image(chart_buffer, width=400, height=300)
        content.append(img)
        content.append(Spacer(1, 20))
        content.append(Paragraph("Accuracy Radar", styles['Heading2']))
        content.append(Spacer(1, 10))

        img2 = Image(acc_buffer, width=400, height=300)
        content.append(img2)

        doc.build(content)

        st.download_button(
            "📄 Download PDF Report",
            buffer.getvalue(),
            file_name=f"report_{details.get('Candidate Name')}_{details.get('Subject')}.pdf",
            mime="application/pdf"
        )