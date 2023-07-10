import time
import numpy as np
from numpy.linalg import norm
from extensions.openai.embeddings import get_embeddings_model


moderations_disabled = False # return 0/false
category_embeddings = None
antonym_embeddings = None
categories = [ "hate", "hate/threatening", "self-harm", "sexual", "sexual/minors", "violence", "violence/graphic" ]
flag_threshold = 0.5


def get_category_embeddings():
    global category_embeddings, categories
    if category_embeddings is None:
        embeddings = get_embeddings_model().encode(categories).tolist()
        category_embeddings = dict(zip(categories, embeddings))

    return category_embeddings


def cosine_similarity(a, b):
    return np.dot(a, b) / (norm(a) * norm(b))


# seems most openai like with all-mpnet-base-v2
def mod_score(a, b):
    return 2.0 * np.dot(a, b)


def moderations(input):
    global category_embeddings, categories, flag_threshold, moderations_disabled
    results = {
        "id": f"modr-{int(time.time()*1e9)}",
        "model": "text-moderation-001",
        "results": [],
    }

    embeddings_model = get_embeddings_model()
    if not embeddings_model or moderations_disabled:
        results['results'] = [{
            'categories': dict([ (C, False) for C in categories]),
            'category_scores': dict([ (C, 0.0) for C in categories]),
            'flagged': False,
        }]
        return results

    category_embeddings = get_category_embeddings()


    # input, string or array
    if isinstance(input, str):
        input = [input]

    for in_str in input:
        for ine in embeddings_model.encode([in_str]).tolist():
            category_scores = dict([ (C, mod_score(category_embeddings[C], ine)) for C in categories ])
            category_flags = dict([ (C, bool(category_scores[C] > flag_threshold)) for C in categories ])
            flagged = any(category_flags)

            results['results'].extend([{
                'categories': category_flags,
                'category_scores': category_scores,
                'flagged': flagged,
            }])

    print(results)

    return results