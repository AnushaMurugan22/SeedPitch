
# SeedPitch – Tamil Nadu Startup Grant Assistant

## Problem

First-time startup founders in Tamil Nadu struggle to identify the government grants and funding schemes they are eligible for. They often cannot distinguish between state startup funding, TANSEED, and central government schemes, or understand the eligibility criteria, funding amount, and equity requirements. Government policy documents and scheme details change frequently, making it difficult to find accurate and updated information. SeedPitch helps founders discover relevant funding opportunities by matching their startup profile with verified government schemes and explaining the eligibility rules with policy references.

## Who it is for

- Final-year student founders and first-time entrepreneurs looking for government startup funding.
- Startup founders at incubators in Tamil Nadu, especially founders in agriculture, technology, and agri-drone startups who are preparing to apply for TANSEED or other government schemes.

## Signature feature

### AI-powered Startup Grant Matcher

Founders enter their startup profile, including sector, startup stage, and funding requirements.

SeedPitch matches their profile with relevant Tamil Nadu state and central government funding schemes.

For each matching scheme, it provides:

- Scheme name and funding amount.
- Eligibility criteria and startup stage.
- Equity or ownership requirements.
- Relevant government policy clauses.
- Source references to verify the information.

The feature helps founders identify suitable funding opportunities without manually searching multiple government websites and policy documents.

## Hardest problem (my interview story)

My biggest technical challenge was keeping the grant information accurate and updated because Tamil Nadu startup policies, funding schemes, and eligibility requirements change frequently.

Instead of re-indexing every document whenever the application runs, I designed a freshness system that checks government webpages regularly using a nightly job. It compares page hashes and re-indexes only the pages that have changed. Older versions are marked as expired so that outdated information is not presented as current.

I also track re-indexing time and the stale-answer rate to measure whether the system is keeping its information fresh.

This was challenging because the system needed to balance accurate information, efficient document processing, and reliable answers with policy references.

## Signature feature – AI Agent (Weeks 7–12)

### Mock Interviewer Agent

The AI agent conducts a voice-based mock interview for startup founders preparing to apply for TANSEED.

The agent asks questions about the founder's startup, problem statement, market, team, and planned use of funds.

It uses SeedPitch to verify the founder's claims against the relevant scheme rules and funding requirements.

After the interview, it provides:

- A scored interview feedback report.
- Suggestions to improve the founder's answers.
- Policy references supporting the feedback.
- Identification of incorrect or unsupported funding claims.

The goal is to help founders prepare for startup funding interviews and understand whether their answers align with the scheme requirements.

## Dataset

| Source | Link | Documents | Pages | Licence / terms |
|---|---|---|---|---|
| Tamil Nadu Startup and Innovation Policy 2023 | https://startuptn.in/ | Policy document | Included in 600+ page corpus | Verify reuse terms |
| StartupTN / TANSEED scheme pages | https://startuptn.in/ | Scheme pages and announcements | Included in 600+ page corpus | Verify website terms |
| Earlier Tamil Nadu Startup Policy 2018–23 | https://startuptn.in/ | Previous policy document | Included in 600+ page corpus | Verify reuse terms |
| Tamil Nadu Finance Department | https://www.tn.gov.in/ | Economic Survey and budget documents | Minimum 5 budget years | Verify reuse terms |
| Startup India | https://www.startupindia.gov.in/ | Central government startup scheme pages | Included in 600+ page corpus | Verify website terms |

**Dataset summary:** More than 600 pages of Tamil Nadu startup policies, TANSEED scheme information, earlier startup policies, central government schemes, and state budget documents. The corpus includes a minimum of five budget years.

## 10 real questions

1. How much TANSEED funding can a woman-led rural impact startup receive, and how much equity is taken?
2. What is the age limit for a startup to be recognised under the Tamil Nadu policy?
3. Is there a special fund for SC/ST founders?
4. What is the difference between TANSEED funding, Tamil Nadu startup recognition, and central government startup schemes?
5. What are the eligibility criteria for a first-time startup founder to apply for TANSEED?
6. Does an agri-drone startup qualify for Tamil Nadu startup funding, and what conditions must it satisfy?
7. What documents are required to apply for government startup funding in Tamil Nadu?
8. How much funding was allocated for startup development or entrepreneurship in the Tamil Nadu budget?
9. How much was allotted for the welfare of fishermen in the interim budget?
10. Which government funding schemes are suitable for a final-year student founder, and what are their eligibility requirements?

## Run it

### 1. Create and activate the virtual environment

**Windows – PowerShell**

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install dependencies

```powershell
pip install -r requirements-dev.txt
```

### 3. Configure environment variables

```powershell
copy .env.example .env
```

Add the required API keys and configuration values to `.env`.

### 4. Start the application

```powershell
uvicorn app.main:app --reload
```

### 5. Check the health endpoint

```powershell
curl http://localhost:8000/health
```

Application URL:

```text
http://localhost:8000
```

## Live link

Added in Week 2.
