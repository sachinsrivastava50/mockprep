import json
import random
import re
import requests
from typing import Dict, Any, List
from .config import settings

# Curated high-fidelity knowledge banks for offline / zero-API-key execution
CURATED_QUESTIONS = {
    ("Software Engineer", "Technical", "Easy"): [
        {
            "question": "What is the difference between a process and a thread in an operating system? How does memory sharing differ between them?",
            "category": "Operating Systems & Concurrency",
            "hint": "Think about independent address spaces versus shared heap/data segments within the same process.",
            "expected_key_points": [
                "Process has its own dedicated virtual address space and resources",
                "Threads within a process share code, data, and heap, but have independent stacks and registers",
                "Context switching between processes is more expensive than between threads",
                "Communication: IPC (pipes, sockets) for processes vs shared memory for threads"
            ],
            "model_answer": "A process is an executing program instance with its own private address space, page tables, and file descriptors. Threads are lightweight execution units within a single process that share the process's heap, global variables, and code segment, while each maintaining its own stack and registers. Context switching between threads is faster because memory mappings do not need to be flushed, whereas inter-process context switches require flushing translation lookaside buffers (TLB)."
        },
        {
            "question": "Explain how HashMap works internally in languages like Java or Python (dictionaries). What happens when a hash collision occurs?",
            "category": "Data Structures",
            "hint": "Discuss hashing, bucket array indexing, hash collisions, and collision resolution techniques.",
            "expected_key_points": [
                "Hash function maps keys to array bucket indexes",
                "Collisions resolved via chaining (linked list / balanced tree) or open addressing",
                "Time complexity is O(1) average, degrading to O(n) or O(log n) on heavy collisions",
                "Load factor triggers rehashing / array resizing"
            ],
            "model_answer": "A HashMap uses an internal bucket array. When inserting a key-value pair, it applies a hash function to the key and computes an index via modulo with array capacity. If two distinct keys map to the exact same index (hash collision), resolution is handled either by separate chaining (chaining nodes into a linked list or red-black tree) or open addressing (linear/quadratic probing). When the ratio of entries to bucket size exceeds the load factor (commonly 0.75), the map doubles in capacity and rehashes existing entries."
        }
    ],
    ("Software Engineer", "Technical", "Medium"): [
        {
            "question": "Design a URL shortening service like Bitly. How would you generate unique 7-character aliases and guarantee low-latency redirects under heavy load?",
            "category": "System Design & Architecture",
            "hint": "Address Base62 encoding, unique ID generation (Snowflake or auto-increment), database choices, and caching.",
            "expected_key_points": [
                "Base62 encoding (a-z, A-Z, 0-9) yielding 62^7 (~3.5 trillion) combinations",
                "Distributed ID generator or counter to eliminate collision overhead",
                "Caching layer (Redis/Memcached) for hot URL redirects (sub-5ms response)",
                "Read-heavy optimization (80-20 rule) and HTTP 301 vs 302 redirects"
            ],
            "model_answer": "A URL shortener is a read-heavy system. For the alias, Base62 encoding (62 characters: [a-zA-Z0-9]) of a 64-bit distributed auto-incrementing ID (such as Twitter Snowflake) produces compact 7-character slugs capable of representing over 3.5 trillion URLs without hashing collisions. For storage, a NoSQL key-value store or relational DB with indexed alias keys stores mapping. We place a distributed Redis caching layer in front of the database to cache the top 20% most-requested URLs in memory. When a user navigates to a short link, the API returns an HTTP 302 redirect so click metrics can be accurately tracked."
        },
        {
            "question": "Explain the difference between optimistic and pessimistic locking in databases. In what real-world scenario would you choose one over the other?",
            "category": "Databases & Concurrency",
            "hint": "Compare version/timestamp checks with explicit SELECT FOR UPDATE locks, and analyze conflict frequency.",
            "expected_key_points": [
                "Pessimistic locking locks rows upon read (SELECT FOR UPDATE) preventing any concurrent modification",
                "Optimistic locking allows concurrent reads and checks version column at commit time",
                "Optimistic is best for low contention / read-heavy scenarios (e-commerce catalog, profile edits)",
                "Pessimistic is suited for high-contention financial / inventory checkout transactions"
            ],
            "model_answer": "Pessimistic locking assumes conflicts are frequent and explicitly locks database rows upon access using constructs like 'SELECT ... FOR UPDATE', blocking other transactions until the lock is released. Optimistic locking assumes conflicts are rare; it allows concurrent reads and writes without locks, but verifies at commit time that a version number or timestamp has not changed. If it has, the transaction rolls back or retries. Optimistic locking is ideal for read-heavy applications like CMS article edits, whereas pessimistic locking is preferable in high-contention financial balances or flash-sale inventory where rollbacks would be prohibitively costly."
        }
    ],
    ("Software Engineer", "Technical", "Hard"): [
        {
            "question": "Walk me through how distributed consensus works in the Raft algorithm. How are leader election and log replication handled during a network partition?",
            "category": "Distributed Systems",
            "hint": "Explain candidate states, randomized election timeouts, quorum majorities, and split-brain resolution.",
            "expected_key_points": [
                "Three node states: Follower, Candidate, Leader",
                "Heartbeats and randomized election timeouts to initiate term elections",
                "Log replication requires an acknowledgment from a quorum (majority: N/2 + 1)",
                "Network partitions: minority partition cannot commit entries; higher term wins upon reconnection"
            ],
            "model_answer": "Raft achieves distributed consensus by electing a single leader responsible for log replication. Nodes begin as Followers; if they do not receive heartbeats before a randomized election timeout expires, they increment the term counter and transition to Candidate, requesting votes. A leader is elected when it receives votes from a quorum majority of nodes (N/2 + 1). During log replication, the leader appends entries to its log and sends AppendEntries RPCs. Once a quorum acknowledges, the entry is committed. If a network partition occurs, the partition with a quorum majority continues committing entries, while the minority partition rejects commits. When the partition heals, nodes detect the higher term and uncommitted minority logs are overwritten by the authoritative leader log."
        }
    ],
    ("Software Engineer", "Behavioral", "Medium"): [
        {
            "question": "Tell me about a time when you had to make a critical technical decision with incomplete information and tight deadlines. How did you proceed?",
            "category": "Decision Making & Ambiguity",
            "hint": "Frame using STAR (Situation, Task, Action, Result). Highlight risk mitigation and communication.",
            "expected_key_points": [
                "Described high-stakes situation and constraints clearly",
                "Gathered available metrics and consulted domain experts",
                "Formulated a two-way door decision with fallback strategies",
                "Delivered successful outcome with measurable impact"
            ],
            "model_answer": "At my prior role, we had 48 hours to choose a message queue for our payments ingestion service during a surge. Full load testing wasn't possible within the window. I listed our non-negotiables—at-least-once delivery, horizontal partition scaling, and team familiarity. I chose Apache Kafka because our engineers already maintained Kafka clusters for analytics, avoiding operational risk. I decoupled the ingestion layer behind an abstraction interface so we could swap implementations if needed. The launch processed 2.4 million transactions with zero message loss."
        }
    ],
    ("Data Analyst", "Technical", "Easy"): [
        {
            "question": "What is the difference between WHERE and HAVING clauses in SQL? Give an example where using WHERE instead of HAVING would result in a syntax error.",
            "category": "SQL & Data Querying",
            "hint": "Consider aggregate functions like COUNT, SUM, AVG and the SQL execution order.",
            "expected_key_points": [
                "WHERE filters raw individual rows before aggregation occurs",
                "HAVING filters grouped records after GROUP BY aggregation",
                "Aggregate functions (COUNT, SUM) cannot be used in WHERE clause",
                "Order of execution: FROM -> WHERE -> GROUP BY -> HAVING -> SELECT"
            ],
            "model_answer": "The WHERE clause filters individual rows before any grouping or aggregation takes place, whereas the HAVING clause filters summary rows after GROUP BY has performed aggregation. For instance, 'SELECT department, COUNT(*) FROM employees WHERE COUNT(*) > 5 GROUP BY department' results in a syntax error because COUNT(*) cannot be evaluated in the row-filtering WHERE stage; it must be written as 'HAVING COUNT(*) > 5'."
        }
    ],
    ("Data Analyst", "Technical", "Medium"): [
        {
            "question": "Explain how you handle missing or skewed data in a dataset before feeding it into an analytics dashboard or predictive model. Compare imputation vs deletion.",
            "category": "Data Wrangling & Statistics",
            "hint": "Discuss MCAR/MAR/MNAR missingness, mean/median vs forward-fill, log transforms, and outlier detection.",
            "expected_key_points": [
                "Diagnosed missing mechanism (Missing Completely at Random vs Systematic)",
                "Deletion (listwise/pairwise) is acceptable only when missing fraction is tiny (<2%)",
                "Imputation strategies: median for skewed numerical data, mode for categorical, KNN/regression for complex patterns",
                "Transformations (Log, Box-Cox) and capping (IQR/Winsorization) for extreme skewness"
            ],
            "model_answer": "First, I identify whether missingness is completely random (MCAR) or systematic (MNAR). If fewer than 2% of rows are missing randomly, listwise deletion is safe. For numerical data with high skew, mean imputation distorts distributions, so I impute using the median or a KNN imputer. For time-series metrics, forward-fill or linear interpolation is used. To address severe skewness in metrics like revenue or session duration, I apply a log1p or Box-Cox transformation to normalize variance, and use IQR thresholds (1.5 * IQR) to detect and winsorize anomalies without losing valid customer records."
        }
    ]
}

def generate_interview_question(role: str, interview_type: str, difficulty: str, previous_questions: List[str] = None) -> Dict[str, Any]:
    """Generates an interview question using an LLM or intelligent curated bank."""
    previous_questions = previous_questions or []
    
    # 1. Try Claude API / Anthropic if configured
    if settings.ANTHROPIC_API_KEY:
        try:
            headers = {
                "x-api-key": settings.ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            prompt = f"""You are an expert interviewer for MockPrep.
Generate one {difficulty} level {interview_type} interview question for a {role}.
Do NOT repeat any of these previously asked questions: {previous_questions}

Return ONLY a valid JSON object matching this schema:
{{
  "question": "string",
  "category": "string",
  "hint": "string",
  "expected_key_points": ["point1", "point2", "point3", "point4"]
}}"""
            payload = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 500,
                "messages": [{"role": "user", "content": prompt}]
            }
            res = requests.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers, timeout=8)
            if res.status_code == 200:
                content = res.json()["content"][0]["text"]
                clean_json = re.search(r'\{.*\}', content, re.DOTALL)
                if clean_json:
                    return json.loads(clean_json.group(0))
        except Exception as e:
            print("Claude API error in question generation, falling back to curated bank:", e)

    # 2. Try Gemini API if configured
    if settings.GEMINI_API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
            prompt = f"""Generate a {difficulty} level {interview_type} interview question for a {role}.
Return valid JSON: {{"question": "...", "category": "...", "hint": "...", "expected_key_points": ["..."]}}"""
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=8)
            if res.status_code == 200:
                txt = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                clean_json = re.search(r'\{.*\}', txt, re.DOTALL)
                if clean_json:
                    return json.loads(clean_json.group(0))
        except Exception as e:
            print("Gemini API error in question generation:", e)

    # 3. Intelligent Curated Bank Fallback
    key = (role, interview_type, difficulty)
    candidates = CURATED_QUESTIONS.get(key)
    
    if not candidates:
        # Fallback to closest match
        matching_keys = [k for k in CURATED_QUESTIONS.keys() if k[0] == role or k[1] == interview_type]
        if matching_keys:
            candidates = CURATED_QUESTIONS[random.choice(matching_keys)]
        else:
            candidates = CURATED_QUESTIONS[("Software Engineer", "Technical", "Medium")]

    # Filter out already asked questions
    fresh_candidates = [q for q in candidates if q["question"] not in previous_questions]
    if not fresh_candidates:
        fresh_candidates = candidates

    chosen = random.choice(fresh_candidates)
    return {
        "question": chosen["question"],
        "category": chosen.get("category", "Core Domain"),
        "hint": chosen.get("hint", "Structure your answer with clear points, trade-offs, and examples."),
        "expected_key_points": chosen.get("expected_key_points", [
            "Demonstrated core domain accuracy",
            "Explained technical trade-offs",
            "Structured response clearly",
            "Highlighted real-world application"
        ])
    }

def evaluate_interview_answer(
    question_text: str,
    category: str,
    user_answer: str,
    role: str = "Software Engineer",
    interview_type: str = "Technical",
    difficulty: str = "Medium",
    time_taken_seconds: int = 0
) -> Dict[str, Any]:
    """
    Evaluates a candidate's answer using weighted scoring out of 10.
    Weighted scoring model:
      - Correctness: weight 2.5 (25%)
      - Clarity: weight 2.0 (20%)
      - Depth: weight 2.0 (20%)
      - Relevance: weight 2.0 (20%)
      - Communication: weight 1.5 (15%)
    Total = 10.0
    """
    # 1. Check if LLM API is available for live evaluation
    if settings.ANTHROPIC_API_KEY:
        try:
            headers = {
                "x-api-key": settings.ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            prompt = f"""You are the MockPrep AI Evaluation Engine evaluating a candidate for: {role} ({difficulty} {interview_type}).
Question: "{question_text}"
Candidate's typed answer: "{user_answer}"

Evaluate the answer using this exact weighted scoring model:
- correctness: score 0.0 - 10.0
- clarity: score 0.0 - 10.0
- depth: score 0.0 - 10.0
- relevance: score 0.0 - 10.0
- communication: score 0.0 - 10.0

Return ONLY a valid JSON object matching this schema:
{{
  "overall_score": <calculated weighted total: (correctness*0.25 + clarity*0.20 + depth*0.20 + relevance*0.20 + communication*0.15) rounded to 1 decimal place>,
  "correctness": <float 0-10>,
  "clarity": <float 0-10>,
  "depth": <float 0-10>,
  "relevance": <float 0-10>,
  "communication": <float 0-10>,
  "strengths": ["<strength 1>", "<strength 2>"],
  "improvements": ["<actionable improvement 1>", "<actionable improvement 2>"],
  "feedback_summary": "<2-3 sentence constructive feedback>",
  "model_answer": "<high scoring benchmark answer>"
}}"""
            payload = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 800,
                "messages": [{"role": "user", "content": prompt}]
            }
            res = requests.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers, timeout=10)
            if res.status_code == 200:
                content = res.json()["content"][0]["text"]
                clean_json = re.search(r'\{.*\}', content, re.DOTALL)
                if clean_json:
                    return json.loads(clean_json.group(0))
        except Exception as e:
            print("Claude API evaluation error, falling back to weighted rubric:", e)

    # 2. Intelligent Built-in Weighted Rubric Engine
    words = user_answer.strip().split()
    word_count = len(words)
    answer_lower = user_answer.lower()
    
    # Base scores out of 10
    correctness = 6.5
    clarity = 7.0
    depth = 6.0
    relevance = 7.0
    communication = 7.0

    # Word count heuristic
    if word_count < 25:
        correctness = max(3.0, correctness - 2.5)
        depth = max(2.5, depth - 3.0)
        clarity = max(4.0, clarity - 2.0)
        communication = max(4.0, communication - 2.0)
    elif word_count >= 60 and word_count <= 250:
        correctness = min(9.5, correctness + 1.8)
        depth = min(9.2, depth + 2.2)
        clarity = min(9.0, clarity + 1.5)
        communication = min(9.0, communication + 1.5)
    elif word_count > 250:
        depth = min(9.6, depth + 2.5)
        clarity = max(6.5, clarity - 0.5)  # slight penalty for wordiness

    # Detect technical and structured markers
    structured_markers = ["first", "second", "specifically", "because", "trade-off", "example", "result", "however", "therefore", "in contrast"]
    matched_markers = [m for m in structured_markers if m in answer_lower]
    if len(matched_markers) >= 3:
        clarity = min(9.8, clarity + 1.5)
        communication = min(9.8, communication + 1.5)

    # Detect STAR components if behavioral
    if interview_type == "Behavioral":
        star_situation = bool(re.search(r'(when i was|at company|during|in a project|we were)', answer_lower))
        star_action = bool(re.search(r'(i decided|i implemented|i built|i scheduled|i analyzed)', answer_lower))
        star_result = bool(re.search(r'(result|outcome|improved|reduced|increased|launched|saved)', answer_lower))
        star_count = sum([star_situation, star_action, star_result])
        if star_count >= 2:
            relevance = min(9.5, relevance + 1.8)
            correctness = min(9.5, correctness + 1.5)

    # Calculate overall weighted score:
    # 25% correctness, 20% clarity, 20% depth, 20% relevance, 15% communication
    overall_score = round(
        (correctness * 0.25) +
        (clarity * 0.20) +
        (depth * 0.20) +
        (relevance * 0.20) +
        (communication * 0.15),
        1
    )
    overall_score = max(3.5, min(9.8, overall_score))

    # Formulate strengths & improvements
    strengths = []
    improvements = []

    if depth >= 7.5:
        strengths.append("Thorough technical explanation with good architectural depth.")
    else:
        improvements.append("Elaborate more deeply on underlying mechanics and trade-offs.")

    if clarity >= 7.5:
        strengths.append("Clear and logical structure that is easy for interviewers to follow.")
    else:
        improvements.append("Organize your response with bulleted points or step-by-step sequencing.")

    if word_count >= 50:
        strengths.append("Good elaboration without being overly brief.")
    else:
        improvements.append("Provide a concrete real-world example or metric to substantiate your claims.")

    # Model answer generation
    model_answer = (
        f"A top-performing answer to this {role} question should clearly state the core definition, "
        f"compare alternative approaches or trade-offs (e.g. latency vs consistency, or memory vs CPU), "
        f"and conclude with a measurable production impact or concrete code pattern."
    )

    feedback_summary = (
        f"Solid response demonstrating clear competency. "
        f"Your explanation scored {overall_score}/10. Adding quantifiable metrics and discussing edge-case handling "
        f"will push your answers into the highest scoring band."
    )

    return {
        "overall_score": overall_score,
        "correctness": round(correctness, 1),
        "clarity": round(clarity, 1),
        "depth": round(depth, 1),
        "relevance": round(relevance, 1),
        "communication": round(communication, 1),
        "strengths": strengths[:3],
        "improvements": improvements[:3],
        "feedback_summary": feedback_summary,
        "model_answer": model_answer
    }
