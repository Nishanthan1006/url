with open("generate_phishing_report.py", "r", encoding="utf-8") as f:
    content = f.read()

parts = content.split("# ================== CHAPTERS ==================")
intro = parts[0]
chapters = parts[1]

# Replace page breaks in chapters with some spacing
chapters_no_breaks = chapters.replace("doc.add_page_break()", "add_smart_text(doc, \"\\n\")")

new_content = intro + "# ================== CHAPTERS ==================" + chapters_no_breaks

# Save it to V4
new_content = new_content.replace('doc.save("PHISHING_DETECTION_INTERNSHIP_REPORT_V3.docx")', 'doc.save("PHISHING_DETECTION_INTERNSHIP_REPORT_V5.docx")')
new_content = new_content.replace('print("Final Master Document successfully generated at PHISHING_DETECTION_INTERNSHIP_REPORT_V3.docx")', 'print("Final Master Document successfully generated at PHISHING_DETECTION_INTERNSHIP_REPORT_V5.docx")')
new_content = new_content.replace('doc.save("PHISHING_DETECTION_INTERNSHIP_REPORT_V4.docx")', 'doc.save("PHISHING_DETECTION_INTERNSHIP_REPORT_V6.docx")')
new_content = new_content.replace('print("Document generated at PHISHING_DETECTION_INTERNSHIP_REPORT_V4.docx (bypassed permission error).")', 'print("Document generated at PHISHING_DETECTION_INTERNSHIP_REPORT_V6.docx (bypassed permission error).")')

with open("generate_phishing_report.py", "w", encoding="utf-8") as f:
    f.write(new_content)

print("Page breaks removed from chapters.")
