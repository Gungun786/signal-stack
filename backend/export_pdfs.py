import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from app.database import SessionLocal
from app.models import Brief, Company

def generate_pdf_for_company(company_name: str, output_filename: str):
    db = SessionLocal()
    comp = db.query(Company).filter(Company.name == company_name).first()
    if not comp:
        print(f"Company {company_name} not found")
        db.close()
        return

    brief = db.query(Brief).filter(Brief.company_id == comp.id).order_by(Brief.id.desc()).first()
    if not brief:
        print(f"No brief for {company_name}")
        db.close()
        return

    reports_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "reports"))
    pdf_path = os.path.join(reports_dir, output_filename)

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=10
    )
    h2_style = ParagraphStyle(
        'DocH2',
        parent=styles['Heading2'],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#1e3a8a'),
        spaceBefore=14,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['BodyText'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#334155')
    )
    bold_style = ParagraphStyle(
        'DocBold',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#0f172a')
    )

    story = []
    # Title
    story.append(Paragraph(f"{brief.title}", title_style))
    story.append(Paragraph(f"<b>Company:</b> {comp.name} ({comp.website}) &bull; <b>Period:</b> Last 7 Days &bull; <b>Classification:</b> Executive Brief", body_style))
    story.append(Spacer(1, 12))

    # 1. Executive Summary
    story.append(Paragraph("1. Executive Summary (Top Developments)", h2_style))
    for idx, item in enumerate(brief.executive_summary[:5], 1):
        headline = item.get("headline", "")
        cat = item.get("category", "Intel").upper()
        urgency = item.get("urgency", "monitor")
        story.append(Paragraph(f"<b>{idx}. [{cat}]</b> {headline} <i>(Urgency: {urgency})</i>", body_style))
        story.append(Spacer(1, 4))
    story.append(Spacer(1, 8))

    # 2. Recommended Actions
    story.append(Paragraph("2. Prioritized Recommended Actions", h2_style))
    action_data = [["Priority", "Action", "Designated Owner"]]
    for a in brief.recommended_actions[:4]:
        action_data.append([
            Paragraph(f"<b>{a.get('priority')}</b>", bold_style),
            Paragraph(a.get("action", "")[:120], body_style),
            Paragraph(f"<b>{a.get('owner')}</b>", bold_style)
        ])
    t = Table(action_data, colWidths=[60, 360, 110])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#0f172a')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    # 3. Opportunities
    story.append(Paragraph("3. Strategic Opportunities (Tied to Verified Signals)", h2_style))
    for opp in brief.opportunities[:3]:
        story.append(Paragraph(f"<b>&bull; {opp.get('title')}</b> [{opp.get('priority')} Priority]", bold_style))
        story.append(Paragraph(f"<i>Evidence:</i> {opp.get('evidence')[:140]}...", body_style))
        story.append(Paragraph(f"<i>Next Step:</i> {opp.get('next_step')}", body_style))
        story.append(Spacer(1, 6))

    # 4. Source Appendix Sample
    story.append(Paragraph("4. Evidence & Source Audit Trail (Sample)", h2_style))
    source_table_data = [["Source", "Pub Date", "Verification", "Snippet Excerpt"]]
    for app in brief.source_appendix[:6]:
        source_table_data.append([
            Paragraph(app.get("source", "")[:25], bold_style),
            Paragraph(app.get("publication_date", ""), body_style),
            Paragraph(app.get("verification_status", ""), body_style),
            Paragraph(app.get("snippet", "")[:100], body_style)
        ])
    st = Table(source_table_data, colWidths=[110, 65, 85, 270])
    st.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f8fafc')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(st)

    doc.build(story)
    print(f"Generated PDF: {pdf_path}")
    db.close()

if __name__ == "__main__":
    generate_pdf_for_company("MeetUniversity", "meetuniversity_monday_brief.pdf")
    generate_pdf_for_company("Supabase", "supabase_monday_brief.pdf")
    generate_pdf_for_company("Razorpay", "razorpay_monday_brief.pdf")
