import os
import numpy as np
from github import Github
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# --- CONSTANTES ---
SIMILARITY_THRESHOLD = float(os.environ.get('INPUT_THRESHOLD', '0.95'))
TOKEN = os.environ.get('INPUT_GITHUB_TOKEN')
LABEL_NAME = os.environ.get('INPUT_DUPLICATE_LABEL', 'potential-duplicate')
REPO_NAME = os.environ.get('GITHUB_REPOSITORY')
EVENT_PATH = os.environ.get('GITHUB_EVENT_PATH')
MODEL_NAME = 'all-MiniLM-L6-v2' # Modèle NLP

if not TOKEN:
    print("Erreur: INPUT_GITHUB_TOKEN est manquant.")
    exit(1)
if not REPO_NAME:
    print("Erreur: Variable GITHUB_REPOSITORY manquante.")
    exit(1)
if not EVENT_PATH:
    print("Erreur: Variable GITHUB_EVENT_PATH manquante.")
    exit(1)

# Récupérer le numéro de l'issue depuis le fichier d'événement
try:
    with open(EVENT_PATH, 'r') as f:
        import json
        event_payload = json.load(f)
        ISSUE_NUMBER = event_payload['issue']['number']
except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
    print(f"Erreur lors de la lecture du numéro de l'issue depuis GITHUB_EVENT_PATH : {e}")
    exit(1)

print(f"Analyse de l'issue #{ISSUE_NUMBER} dans {REPO_NAME}...")

# --- 1. CONNEXION ET RÉCUPÉRATION DES ISSUES ---
g = Github(TOKEN)
try:
    repo = g.get_repo(REPO_NAME)
    new_issue = repo.get_issue(number=ISSUE_NUMBER)
    new_issue_text = f"{new_issue.title} {new_issue.body or ''}" # S'assurer que le body n'est pas None
except Exception as e:
    print(f"Impossible de récupérer l'issue ou le dépôt : {e}")
    exit(1)

corpus = [] # Liste pour stocker le texte des anciennes issues
corpus_issues = [] # Liste pour stocker les objets Issue correspondants
print("Récupération des autres issues ouvertes...")
for issue in repo.get_issues(state='open'):
    if issue.number != ISSUE_NUMBER and not issue.pull_request: # Ignorer la nouvelle issue et les PRs
        corpus.append(f"{issue.title} {issue.body or ''}")
        corpus_issues.append(issue)

if not corpus:
    print("Aucune autre issue ouverte à comparer. Fin.")
    exit(0)

print(f"Comparaison avec {len(corpus)} autres issues...")

# --- 2. LE CERVEAU NLP : VECTORISATION ---
print(f"Chargement du modèle NLP ({MODEL_NAME})...")
try:
    model = SentenceTransformer(MODEL_NAME)
except Exception as e:
    print(f"Erreur lors du chargement du modèle SentenceTransformer : {e}")
    exit(1)

print("Vectorisation des issues (cela peut prendre un moment)...")
# Convertir le texte des anciennes issues en vecteurs numériques
corpus_embeddings = model.encode(corpus, show_progress_bar=False)
# Convertir le texte de la nouvelle issue en vecteur
query_embedding = model.encode([new_issue_text], show_progress_bar=False)

# --- 3. COMPARAISON MATHÉMATIQUE ---
print("Calcul de la similarité cosinus...")
# Calculer la similarité entre la nouvelle issue et TOUTES les anciennes
cosine_scores = cosine_similarity(query_embedding, corpus_embeddings)[0] # On prend le premier (et seul) élément

# Trouver le score le plus élevé et l'index correspondant
best_match_index = np.argmax(cosine_scores)
best_match_score = cosine_scores[best_match_index]

print(f"Meilleur score de similarité : {best_match_score * 100:.2f}%")

# --- 4. DÉCISION ET ACTION ---
if best_match_score >= SIMILARITY_THRESHOLD:
    duplicate_issue = corpus_issues[best_match_index] # Récupérer l'objet Issue correspondant

    print(f"DUPLICATA POTENTIEL TROUVÉ ! Similaire à l'issue #{duplicate_issue.number}")

    # Préparer le commentaire
    comment_body = f"""🤖 Bonjour @{new_issue.user.login} ! Merci pour votre rapport.

Mon analyse suggère que cette issue ressemble beaucoup à une issue existante.

🎯 **Issue similaire trouvée :** [{duplicate_issue.title} (#{duplicate_issue.number})]({duplicate_issue.html_url}) (Score de similarité : {best_match_score * 100:.2f}%)

Je laisse un mainteneur humain vérifier et confirmer.
"""

    # Poster le commentaire
    try:
        new_issue.create_comment(comment_body)
        print("Commentaire posté.")
    except Exception as e:
        print(f"Erreur lors de la publication du commentaire : {e}")

    # Ajouter un label (le label doit exister dans le dépôt)
    try:
        new_issue.add_to_labels(LABEL_NAME)
        print(f"Label '{LABEL_NAME}' ajouté.")
    except Exception as e:
        print(f"Avertissement : Impossible d'ajouter le label '{LABEL_NAME}'. Existe-t-il bien dans le dépôt ? Détails: {e}")
else:
    print("Aucun duplicata clair trouvé (score sous le seuil). Fin.")