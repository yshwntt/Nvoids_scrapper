"""Configuration for Nvoid Bot."""

# Search keywords and job matching
KEYWORDS = ["python", "django", "flask", "fastapi", "ai", "ml", "machine learning", "genai", "generative ai", "llm", "data science"]
EXCLUDE_KEYWORDS = [
    # Interview type
    "face to face",
    "f2f",
    "in person interview",
    "in-person interview",
    "face-to-face",
    # Visa restrictions
    "no h1b",
    "no h-1b",
    "usc only",
    "gc only",
    "green card only",
    "citizens only",
    "no visa",
    "us citizen",
    "no sponsorship",
    "no cpt",
    "no opt",
    "no cpt/opt",
    # Wrong roles
    "product manager",
    "java",
    ".net",
    "jira",
    "architect",
    "full stack",
    "security engineer",
    "security architect",
    "product owner",
    "15+ years",
    "14+ years",
]

SEARCH_QUERIES = ["AI", "ML", "genai", "agentic ai"]

# Email settings
MAX_EMAILS_PER_RUN = 25
DELAY_BETWEEN_EMAILS = 10
EMPLOYER_EMAIL = "nanditha@stemsolllc.com"

# Email extraction settings
EXCLUDE_DOMAINS = ["nvoids.com", "me@nvoids.com"]  # Exclude these from email picks
VALID_EMAIL_PATTERN = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]{2,}"

# Job age filter (hours) — jobs older than this are skipped at scrape time
MAX_JOB_AGE_HOURS = 50

# Browser settings
BROWSER_TIMEOUT = 20
JOB_PAGE_LOAD_TIME = 4
SEARCH_DELAY = 1

# Tracking
TRACKER_FILE = "applied_jobs.xlsx"
