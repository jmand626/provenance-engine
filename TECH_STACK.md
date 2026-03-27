Philosophy: A decoupled microservice architecture running locally. Heavy data processing isolated from the core API.

1. Data Storage & Search (Dockerized)

* Relational Database: PostgreSQL. (Stores bill metadata, sponsor info, dates, and the final alignment scores).

* Search/Text Engine: Elasticsearch. (Crucial for the LSH pre-filtering mentioned in the report. It is optimized for rapidly searching massive text corpora before running the heavier algorithms).

2. Data Pipeline & NLP (The "Worker")

* Language: Python 3.11+

* Scraping: BeautifulSoup and Requests (for scraping ALEC's HTML).

* Algorithms: text_reuse or similar libraries to implement LSH and sequence alignment.

* Role: This acts as a background worker. It scrapes data, runs the heavy NLP math, and saves the matching results into the PostgreSQL database.

3. Backend API (The "Orchestrator")

* Language/Framework: Java (Spring Boot).

* Role: The command center. It serves the REST API, queries PostgreSQL for matched bills, formats the data, and serves it to the frontend. Spring Boot provides an incredibly solid, enterprise-grade foundation for this logic.

4. Frontend (The "Viewer")

* Framework: React or Next.js. Next.js is an enchanced version, and we do not need to go into React's architectural weeds to create something particularly unique there. We will probably use Next.js.

* UI Library: Tailwind CSS.

* Role: A clean, minimal dashboard to view the data. The primary component will be a text-diff viewer that highlights the matched rhetoric.
