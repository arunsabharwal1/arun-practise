"""
Seed script — populates database with 10 realistic projects.

Run:
    python seed_data.py
"""

import asyncio
from datetime import date, datetime
from app.database import AsyncSessionLocal, init_db
from app.models import Project, FinancialLog, TeamMember, RiskEntry, ProjectStatus, RiskLevel, RiskStatus


PROJECTS_DATA = [
    {
        "project": {
            "name": "ERP System Migration",
            "description": "Full migration of legacy ERP to SAP S/4HANA cloud platform",
            "client": "Apex Manufacturing Ltd",
            "status": ProjectStatus.ACTIVE,
            "start_date": date(2024, 1, 15),
            "end_date": date(2024, 12, 31),
        },
        "financials": {
            "budget": 850000, "actual_cost": 410000, "revenue": 950000, "currency": "USD",
            "notes": "Phase 1 complete. Phase 2 in progress."
        },
        "team": [
            {"name": "Sarah Chen", "role": "Project Manager", "email": "s.chen@apex.com", "is_lead": True, "allocation_percentage": 100},
            {"name": "James Patel", "role": "SAP Architect", "email": "j.patel@apex.com", "allocation_percentage": 100},
            {"name": "Emily Torres", "role": "Business Analyst", "email": "e.torres@apex.com", "allocation_percentage": 80},
            {"name": "Ravi Kumar", "role": "Backend Developer", "email": "r.kumar@apex.com", "allocation_percentage": 100},
        ],
        "risks": [
            {"title": "Data migration data loss", "probability": RiskLevel.MEDIUM, "impact": RiskLevel.HIGH,
             "mitigation_plan": "Full backup before each migration phase. Parallel run for 2 weeks.", "owner": "James Patel"},
            {"title": "User adoption resistance", "probability": RiskLevel.HIGH, "impact": RiskLevel.MEDIUM,
             "mitigation_plan": "Conduct 4-week training program before go-live.", "owner": "Sarah Chen"},
        ]
    },
    {
        "project": {
            "name": "Mobile Banking App",
            "description": "Consumer mobile banking app for iOS and Android with biometric authentication",
            "client": "NorthStar Bank",
            "status": ProjectStatus.ACTIVE,
            "start_date": date(2024, 3, 1),
            "end_date": date(2025, 2, 28),
        },
        "financials": {
            "budget": 1200000, "actual_cost": 320000, "revenue": 1400000, "currency": "USD",
            "notes": "Design phase complete. Development sprint 3 of 8 in progress."
        },
        "team": [
            {"name": "Michael Wong", "role": "Product Lead", "email": "m.wong@northstar.com", "is_lead": True, "allocation_percentage": 100},
            {"name": "Aisha Nkosi", "role": "iOS Developer", "email": "a.nkosi@northstar.com", "allocation_percentage": 100},
            {"name": "Lars Eriksson", "role": "Android Developer", "email": "l.eriksson@northstar.com", "allocation_percentage": 100},
            {"name": "Priya Sharma", "role": "UX Designer", "email": "p.sharma@northstar.com", "allocation_percentage": 60},
            {"name": "Daniel Kim", "role": "Security Engineer", "email": "d.kim@northstar.com", "allocation_percentage": 80},
        ],
        "risks": [
            {"title": "PCI DSS compliance gap", "probability": RiskLevel.MEDIUM, "impact": RiskLevel.HIGH,
             "mitigation_plan": "Engage external auditor in sprint 5 for early gap analysis.", "owner": "Daniel Kim"},
            {"title": "App store rejection", "probability": RiskLevel.LOW, "impact": RiskLevel.MEDIUM,
             "mitigation_plan": "Follow Apple/Google guidelines strictly. Internal review before submission.", "owner": "Michael Wong"},
        ]
    },
    {
        "project": {
            "name": "AI Customer Support Bot",
            "description": "Conversational AI chatbot using LLMs to automate tier-1 customer support",
            "client": "ShopEase Retail",
            "status": ProjectStatus.PLANNING,
            "start_date": date(2024, 6, 1),
            "end_date": date(2024, 11, 30),
        },
        "financials": {
            "budget": 320000, "actual_cost": 15000, "revenue": 400000, "currency": "USD",
            "notes": "Planning phase. Vendor evaluation in progress."
        },
        "team": [
            {"name": "Fatima Al-Hassan", "role": "AI/ML Lead", "email": "f.alhassan@shopease.com", "is_lead": True, "allocation_percentage": 100},
            {"name": "Tom Bradley", "role": "NLP Engineer", "email": "t.bradley@shopease.com", "allocation_percentage": 100},
        ],
        "risks": [
            {"title": "LLM hallucination in customer responses", "probability": RiskLevel.HIGH, "impact": RiskLevel.HIGH,
             "mitigation_plan": "Implement retrieval-augmented generation (RAG) with strict content filters.", "owner": "Fatima Al-Hassan"},
        ]
    },
    {
        "project": {
            "name": "Data Warehouse Modernization",
            "description": "Migrate on-premise data warehouse to Snowflake with real-time pipelines",
            "client": "GlobalLogistics Corp",
            "status": ProjectStatus.ACTIVE,
            "start_date": date(2024, 2, 15),
            "end_date": date(2024, 9, 30),
        },
        "financials": {
            "budget": 550000, "actual_cost": 380000, "revenue": 620000, "currency": "USD",
            "notes": "75% complete. Final integration testing phase."
        },
        "team": [
            {"name": "Yuki Tanaka", "role": "Data Architect", "email": "y.tanaka@globallog.com", "is_lead": True, "allocation_percentage": 100},
            {"name": "Carlos Rivera", "role": "Data Engineer", "email": "c.rivera@globallog.com", "allocation_percentage": 100},
            {"name": "Adaeze Obi", "role": "BI Developer", "email": "a.obi@globallog.com", "allocation_percentage": 80},
        ],
        "risks": [
            {"title": "Data pipeline latency exceeds SLA", "probability": RiskLevel.MEDIUM, "impact": RiskLevel.MEDIUM,
             "mitigation_plan": "Optimize Kafka consumer groups. Add auto-scaling rules.", "owner": "Carlos Rivera", "status": RiskStatus.MITIGATED},
        ]
    },
    {
        "project": {
            "name": "E-Commerce Platform Rebuild",
            "description": "Full headless commerce rebuild with Next.js frontend and microservices backend",
            "client": "FreshMart Online",
            "status": ProjectStatus.ACTIVE,
            "start_date": date(2023, 11, 1),
            "end_date": date(2024, 8, 31),
        },
        "financials": {
            "budget": 780000, "actual_cost": 690000, "revenue": 850000, "currency": "USD",
            "notes": "Near completion. Performance optimization phase."
        },
        "team": [
            {"name": "Hannah Schmidt", "role": "Tech Lead", "email": "h.schmidt@freshmart.com", "is_lead": True, "allocation_percentage": 100},
            {"name": "Mohammed Alami", "role": "Frontend Developer", "email": "m.alami@freshmart.com", "allocation_percentage": 100},
            {"name": "Jessica Park", "role": "Backend Developer", "email": "j.park@freshmart.com", "allocation_percentage": 100},
            {"name": "Ivan Petrov", "role": "DevOps Engineer", "email": "i.petrov@freshmart.com", "allocation_percentage": 80},
        ],
        "risks": [
            {"title": "Payment gateway downtime during migration", "probability": RiskLevel.LOW, "impact": RiskLevel.HIGH,
             "mitigation_plan": "Schedule cutover at 2AM. Keep old system live for 48h rollback window.", "owner": "Hannah Schmidt"},
        ]
    },
    {
        "project": {
            "name": "Cybersecurity Audit & Remediation",
            "description": "ISO 27001 gap analysis, penetration testing, and full remediation implementation",
            "client": "MediCare Solutions",
            "status": ProjectStatus.ON_HOLD,
            "start_date": date(2024, 4, 1),
            "end_date": date(2024, 10, 31),
        },
        "financials": {
            "budget": 290000, "actual_cost": 95000, "revenue": 310000, "currency": "USD",
            "notes": "On hold pending client budget approval for remediation phase."
        },
        "team": [
            {"name": "Damian Cross", "role": "Security Lead", "email": "d.cross@medicare.com", "is_lead": True, "allocation_percentage": 100},
            {"name": "Zara Ahmed", "role": "Penetration Tester", "email": "z.ahmed@medicare.com", "allocation_percentage": 100},
        ],
        "risks": [
            {"title": "HIPAA violation exposure during pen test", "probability": RiskLevel.LOW, "impact": RiskLevel.HIGH,
             "mitigation_plan": "All pen testing in isolated staging environment only.", "owner": "Zara Ahmed"},
            {"title": "Client budget freeze extending timeline", "probability": RiskLevel.HIGH, "impact": RiskLevel.MEDIUM,
             "mitigation_plan": "Monthly stakeholder reviews. Document financial impact of delays.", "owner": "Damian Cross"},
        ]
    },
    {
        "project": {
            "name": "IoT Fleet Management System",
            "description": "Real-time GPS tracking and predictive maintenance for 500-vehicle fleet",
            "client": "FastFreight Transport",
            "status": ProjectStatus.ACTIVE,
            "start_date": date(2024, 1, 8),
            "end_date": date(2024, 12, 15),
        },
        "financials": {
            "budget": 960000, "actual_cost": 480000, "revenue": 1100000, "currency": "USD",
            "notes": "Sensor integration phase complete. Dashboard development ongoing."
        },
        "team": [
            {"name": "Roberto Diaz", "role": "IoT Architect", "email": "r.diaz@fastfreight.com", "is_lead": True, "allocation_percentage": 100},
            {"name": "Mei Lin", "role": "Embedded Systems Engineer", "email": "m.lin@fastfreight.com", "allocation_percentage": 100},
            {"name": "Tobias Müller", "role": "Data Scientist", "email": "t.muller@fastfreight.com", "allocation_percentage": 100},
            {"name": "Alice Johnson", "role": "Dashboard Developer", "email": "a.johnson@fastfreight.com", "allocation_percentage": 100},
            {"name": "Samuel Osei", "role": "QA Engineer", "email": "s.osei@fastfreight.com", "allocation_percentage": 80},
        ],
        "risks": [
            {"title": "Cellular connectivity gaps in rural areas", "probability": RiskLevel.HIGH, "impact": RiskLevel.MEDIUM,
             "mitigation_plan": "Implement store-and-forward mode for offline operation.", "owner": "Mei Lin"},
            {"title": "Battery life below spec on cold weather units", "probability": RiskLevel.MEDIUM, "impact": RiskLevel.MEDIUM,
             "mitigation_plan": "Thermal enclosures for harsh environment units. Increase polling interval.", "owner": "Roberto Diaz"},
        ]
    },
    {
        "project": {
            "name": "HR Self-Service Portal",
            "description": "Employee self-service portal for leave, payroll, performance reviews, and onboarding",
            "client": "InnovateCorp (Internal)",
            "status": ProjectStatus.COMPLETED,
            "start_date": date(2023, 8, 1),
            "end_date": date(2024, 2, 29),
        },
        "financials": {
            "budget": 220000, "actual_cost": 198000, "revenue": 220000, "currency": "USD",
            "notes": "Delivered on time and 10% under budget."
        },
        "team": [
            {"name": "Linda Okafor", "role": "Project Manager", "email": "l.okafor@innovatecorp.com", "is_lead": True, "allocation_percentage": 100},
            {"name": "Alex Turner", "role": "Full Stack Developer", "email": "a.turner@innovatecorp.com", "allocation_percentage": 100},
        ],
        "risks": [
            {"title": "GDPR compliance for EU employees", "probability": RiskLevel.MEDIUM, "impact": RiskLevel.HIGH,
             "mitigation_plan": "Legal review completed. Data residency controls implemented.", "status": RiskStatus.CLOSED, "owner": "Linda Okafor"},
        ]
    },
    {
        "project": {
            "name": "Cloud Infrastructure Migration",
            "description": "Lift-and-shift of 40 on-premise servers to AWS with IaC using Terraform",
            "client": "PrimeInsurance Group",
            "status": ProjectStatus.ACTIVE,
            "start_date": date(2024, 5, 1),
            "end_date": date(2024, 11, 30),
        },
        "financials": {
            "budget": 430000, "actual_cost": 160000, "revenue": 490000, "currency": "USD",
            "notes": "Wave 1 (dev/test environments) complete. Wave 2 (production) starting."
        },
        "team": [
            {"name": "Nadia Volkov", "role": "Cloud Architect", "email": "n.volkov@primeins.com", "is_lead": True, "allocation_percentage": 100},
            {"name": "Ben Harper", "role": "DevOps Engineer", "email": "b.harper@primeins.com", "allocation_percentage": 100},
            {"name": "Grace Liu", "role": "Security Engineer", "email": "g.liu@primeins.com", "allocation_percentage": 60},
        ],
        "risks": [
            {"title": "Production cutover outage window exceeded", "probability": RiskLevel.MEDIUM, "impact": RiskLevel.HIGH,
             "mitigation_plan": "Blue-green deployment. DNS failback tested. 4h max outage SLA.", "owner": "Nadia Volkov"},
            {"title": "Cost overrun due to unoptimized cloud resources", "probability": RiskLevel.MEDIUM, "impact": RiskLevel.MEDIUM,
             "mitigation_plan": "AWS Cost Explorer dashboards. Rightsizing analysis after Wave 1.", "owner": "Ben Harper"},
        ]
    },
    {
        "project": {
            "name": "Blockchain Supply Chain Tracker",
            "description": "Ethereum-based smart contract system for end-to-end supply chain provenance tracking",
            "client": "PureSource Foods",
            "status": ProjectStatus.PLANNING,
            "start_date": date(2024, 7, 1),
            "end_date": date(2025, 6, 30),
        },
        "financials": {
            "budget": 680000, "actual_cost": 8000, "revenue": 800000, "currency": "USD",
            "notes": "Kickoff complete. Technical design phase starting."
        },
        "team": [
            {"name": "David Reeves", "role": "Blockchain Lead", "email": "d.reeves@puresource.com", "is_lead": True, "allocation_percentage": 100},
            {"name": "Amara Diallo", "role": "Smart Contract Developer", "email": "a.diallo@puresource.com", "allocation_percentage": 100},
            {"name": "Paul Nguyen", "role": "Integration Architect", "email": "p.nguyen@puresource.com", "allocation_percentage": 80},
        ],
        "risks": [
            {"title": "Gas fees making micro-transactions uneconomical", "probability": RiskLevel.HIGH, "impact": RiskLevel.HIGH,
             "mitigation_plan": "Evaluate Layer 2 solutions (Polygon/Optimism) as fallback.", "owner": "David Reeves"},
            {"title": "Smart contract vulnerability", "probability": RiskLevel.MEDIUM, "impact": RiskLevel.HIGH,
             "mitigation_plan": "Formal verification + third-party audit before mainnet deployment.", "owner": "Amara Diallo"},
        ]
    },
]


async def seed():
    await init_db()
    async with AsyncSessionLocal() as session:
        for item in PROJECTS_DATA:
            # Create project
            p = Project(**item["project"])
            session.add(p)
            await session.flush()

            # Add financials
            fin = item["financials"]
            risk_status = fin.pop("status", None)
            fl = FinancialLog(project_id=p.id, **fin)
            session.add(fl)

            # Add team members
            for member_data in item["team"]:
                m = TeamMember(project_id=p.id, joined_at=item["project"]["start_date"], **member_data)
                session.add(m)

            # Add risks
            for risk_data in item["risks"]:
                risk_data_copy = dict(risk_data)
                r = RiskEntry(project_id=p.id, **risk_data_copy)
                session.add(r)

        await session.commit()
        print(f"✅ Seeded {len(PROJECTS_DATA)} projects successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
