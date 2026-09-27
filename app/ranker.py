import os

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def compute_similarity(jd_text: str, resume_text: str) -> float:
    """Compute similarity score (0-100) between a job description and a resume using TF-IDF."""
    if not jd_text.strip() or not resume_text.strip():
        return 0.0

    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform([jd_text, resume_text])

    sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    score = max(0.0, min(100.0, float(sim) * 100))
    return score


def extract_matched_keywords(jd_text: str, resume_text: str, top_k: int = 6) -> list[str]:
    import re

    # Common stop words to ignore
    STOP_WORDS = {
        'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 'aren',
        'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by',
        'can', 'could', 'did', 'do', 'does', 'doing', 'down', 'during', 'each', 'few', 'for', 'from',
        'further', 'had', 'has', 'have', 'having', 'he', 'her', 'here', 'hers', 'herself', 'him', 'himself',
        'his', 'how', 'i', 'if', 'in', 'into', 'is', 'it', 'its', 'itself', 'just', 'me', 'more', 'most',
        'my', 'myself', 'no', 'nor', 'not', 'now', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'our',
        'ours', 'ourselves', 'out', 'over', 'own', 'same', 'should', 'so', 'some', 'such', 'than', 'that',
        'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', 'these', 'they', 'this', 'those',
        'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', 'we', 'were', 'what', 'when', 'where',
        'which', 'while', 'who', 'whom', 'why', 'with', 'would', 'you', 'your', 'yours', 'yourself', 'yourselves',
        'experience', 'work', 'working', 'skills', 'knowledge', 'years', 'role', 'team', 'ability', 'proficient',
        'including', 'strong', 'good', 'using', 'used', 'tools', 'technologies', 'project', 'projects'
    }

    jd_tokens = set(re.findall(r'\b[a-zA-Z0-9+#.\-]{2,}\b', jd_text.lower()))
    res_tokens = set(re.findall(r'\b[a-zA-Z0-9+#.\-]{2,}\b', resume_text.lower()))

    matched = [w for w in (jd_tokens & res_tokens) if w not in STOP_WORDS and len(w) > 2]
    matched.sort(key=lambda x: (-len(x), x))
    return matched[:top_k]


def rank_resumes(jd_text: str, resume_texts: dict[str, str]) -> list[dict]:
    results = []
    for filename, text in resume_texts.items():
        if not text.strip():
            continue
        score = compute_similarity(jd_text, text)
        matched_kw = extract_matched_keywords(jd_text, text)
        results.append({
            "filename": filename,
            "score": round(score, 1),
            "matched_keywords": matched_kw
        })

    results.sort(key=lambda x: x['score'], reverse=True)
    for idx, res in enumerate(results):
        res['rank'] = idx + 1

    return results


def process_job_background(job_id: str, file_paths: dict[str, str]):
    import time
    t_start = time.time()
    from app.database import SessionLocal
    from app.models import ScreeningJob, Candidate
    from app.extractor import extract_text

    db = SessionLocal()
    job = db.query(ScreeningJob).filter(ScreeningJob.id == job_id).first()
    if not job:
        db.close()
        return

    job.status = "processing"
    db.commit()

    print(f"[{job_id}] Started processing job. Setup took {time.time()-t_start:.2f}s")

    jd_text = job.job_description

    for filename, file_path in file_paths.items():
        t_file = time.time()
        try:
            with open(file_path, 'rb') as f:
                file_bytes = f.read()

            t_ext = time.time()
            text = extract_text(filename, file_bytes)
            ext_time = time.time() - t_ext

            if not text.strip():
                cand = Candidate(job_id=job_id, filename=filename, status="failed", error_message="No extractable text found")
            else:
                t_score = time.time()
                score = compute_similarity(jd_text, text)
                score_time = time.time() - t_score
                matched_kw = extract_matched_keywords(jd_text, text)

                cand = Candidate(
                    job_id=job_id,
                    filename=filename,
                    score=round(score, 1),
                    matched_keywords=",".join(matched_kw)
                )
                print(f"[{job_id}] Processed {filename} in {time.time()-t_file:.2f}s (Ext: {ext_time:.2f}s, Score: {score_time:.2f}s)")

            db.add(cand)
        except Exception as e:
            cand = Candidate(job_id=job_id, filename=filename, status="failed", error_message=str(e))
            db.add(cand)
            print(f"[{job_id}] Failed {filename}: {e}")

        job.processed_files += 1
        db.commit()

        try:
            os.remove(file_path)
        except:
            pass

    job.status = "completed"
    db.commit()
    db.close()
    print(f"[{job_id}] Job finished in {time.time()-t_start:.2f}s total")
sqlalchemy
psycopg2-binary
