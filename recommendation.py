"""
AI-Based Book Recommendation System
Content-Based Recommendation Engine for E-Library

This module implements a content-based filtering algorithm that calculates
relevance scores for books based on:
1. Student's registered areas of interest (profile matching)
2. Student's previous book requests and transaction history (behavior matching)
3. Domain ontology / semantic category relationships (cross-domain discovery)
4. Lexical keyword similarity between book metadata
"""

import re

# Cross-domain related category map for CSE disciplines
RELATED_DOMAINS = {
    'Programming': ['Computer Science', 'Web Development', 'Data Structures', 'Artificial Intelligence'],
    'Artificial Intelligence': ['Machine Learning', 'Data Science', 'Programming', 'Python'],
    'Data Science': ['Artificial Intelligence', 'Database', 'Programming', 'Cloud Computing'],
    'Cybersecurity': ['Networking', 'Computer Networks', 'Operating Systems', 'Cloud Computing'],
    'Networking': ['Cybersecurity', 'Cloud Computing', 'Computer Science'],
    'Web Development': ['Programming', 'Database', 'Cloud Computing'],
    'Database': ['Web Development', 'Data Science', 'Cloud Computing', 'Programming'],
    'Cloud Computing': ['Networking', 'Database', 'Cybersecurity', 'Web Development'],
    'Computer Science': ['Programming', 'Database', 'Networking', 'Cybersecurity']
}


def extract_keywords(text):
    """Normalize and tokenize text into significant keywords."""
    if not text:
        return set()
    words = re.findall(r'[a-zA-Z0-9]+', text.lower())
    stop_words = {
        'the', 'and', 'for', 'with', 'using', 'basics', 'introduction',
        'guide', 'edition', 'fundamentals', 'concepts', 'systems', 'management',
        'a', 'an', 'in', 'on', 'of', 'to', 'from', 'by', 'at'
    }
    return {w for w in words if len(w) > 2 and w not in stop_words}


def get_recommendations(user, user_requests, all_books, limit=8, exclude_requested=True):
    """
    Generate personalized book recommendations for a student.

    Parameters:
        user: dict or sqlite3.Row containing user details (interests)
        user_requests: list of dicts/Rows representing user's past book requests
        all_books: list of dicts/Rows of all books in library
        limit: max number of recommendations to return
        exclude_requested: boolean, whether to exclude books user already requested

    Returns:
        list of book dicts enriched with:
            - relevance_score
            - match_percentage
            - reason (human-readable AI explanation)
    """
    # 1. Normalize user object to dictionary
    user_dict = dict(user) if user is not None else {}

    # 1. Parse user's registered interests
    user_interests = []
    if user_dict.get('interests'):
        raw_interests = user_dict['interests']
        if isinstance(raw_interests, str):
            user_interests = [i.strip() for i in raw_interests.split(',') if i.strip()]
        elif isinstance(raw_interests, list):
            user_interests = [i.strip() for i in raw_interests if i.strip()]

    user_interests_lower = {i.lower() for i in user_interests}

    # 2. Normalize user requests to list of dictionaries
    normalized_requests = [dict(r) for r in user_requests] if user_requests else []

    requested_book_ids = set()
    requested_categories = []
    requested_book_titles = []
    requested_keywords = set()

    for req in normalized_requests:
        b_id = req.get('book_id') or req.get('id')
        if b_id:
            requested_book_ids.add(b_id)
        cat = req.get('category')
        if cat:
            requested_categories.append(cat)
        title = req.get('title')
        if title:
            requested_book_titles.append(title)
            requested_keywords.update(extract_keywords(title))

    has_interests = len(user_interests) > 0
    has_history = len(normalized_requests) > 0

    scored_books = []

    for book in all_books:
        book_dict = dict(book)
        b_id = book_dict.get('id')

        # Optionally skip books already requested by user
        if exclude_requested and b_id in requested_book_ids:
            continue

        category = book_dict.get('category', '')
        title = book_dict.get('title', '')
        description = book_dict.get('description', '')
        cat_lower = category.lower()

        book_keywords = extract_keywords(title) | extract_keywords(description)

        score = 0
        reasons = []

        # --- Criterion 1: Direct Interest Match (+12 points) ---
        direct_interest_matches = [
            i for i in user_interests if i.lower() in cat_lower or cat_lower in i.lower()
        ]
        if direct_interest_matches:
            score += 12
            reasons.append(f"matches your registered interest in '{direct_interest_matches[0]}'")
        else:
            # Check if any interest word is in title/description (+6 points)
            keyword_interest_matches = [
                i for i in user_interests if i.lower() in title.lower() or i.lower() in description.lower()
            ]
            if keyword_interest_matches:
                score += 6
                reasons.append(f"aligns with your interest in '{keyword_interest_matches[0]}'")

        # --- Criterion 2: Past Request History Category Match (+10 points) ---
        matching_past_cats = [c for c in requested_categories if c.lower() == cat_lower]
        if matching_past_cats:
            score += 10 + min(len(matching_past_cats) * 2, 6)
            # Find the title that matched
            matched_title = next((r.get('title') for r in normalized_requests if (r.get('category') or '').lower() == cat_lower), None)
            if matched_title:
                reasons.append(f"you previously explored '{matched_title}' in {category}")
            else:
                reasons.append(f"similar to books you previously requested in {category}")

        # --- Criterion 3: Cross-Domain Semantic Association (+5 points) ---
        for user_int in user_interests:
            related_list = RELATED_DOMAINS.get(user_int, [])
            if any(rel.lower() in cat_lower for rel in related_list):
                score += 5
                reasons.append(f"complements your study in {user_int}")
                break

        for past_cat in requested_categories:
            related_list = RELATED_DOMAINS.get(past_cat, [])
            if any(rel.lower() in cat_lower for rel in related_list):
                score += 4
                break

        # --- Criterion 4: Lexical Content Similarity with Past Books (+3 points per keyword) ---
        common_tokens = book_keywords.intersection(requested_keywords)
        if common_tokens:
            token_score = min(len(common_tokens) * 3, 9)
            score += token_score

        # --- Cold Start / Default Fallback for new users ---
        if not has_interests and not has_history:
            # Baseline popular score
            score = 5
            reasons.append("popular core reading in Computer Science Engineering")
        elif score == 0:
            # If no direct match found but book is available
            score = 2
            reasons.append("recommended general reference for CSE students")

        # Availability bonus: available books slightly prioritized (+2 points)
        if book_dict.get('available', 1) == 1:
            score += 2

        # Format explanation
        if reasons:
            primary_reason = f"Recommended because {reasons[0]}."
            if len(reasons) > 1 and "matches" in reasons[0] and "explored" in reasons[1]:
                primary_reason = f"Recommended because {reasons[0]}, and {reasons[1]}."
        else:
            primary_reason = "Recommended based on your curriculum profile."

        # Compute match percentage between 65% and 99%
        calculated_pct = min(99, max(65, 60 + int(score * 1.5)))

        book_dict['relevance_score'] = score
        book_dict['match_percentage'] = calculated_pct
        book_dict['recommendation_reason'] = primary_reason

        scored_books.append(book_dict)

    # Sort descending by relevance score, then by match_percentage, then by availability
    scored_books.sort(key=lambda b: (b['relevance_score'], b.get('available', 0)), reverse=True)

    return scored_books[:limit]
