import os
import numpy as np
from github import Github, Auth
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import json # Moved import to top

# --- CONSTANTES ---
# Lire les inputs en utilisant les NOMS EXACTS passés par l'action Docker (avec traits d'union)
TOKEN = os.environ.get('INPUT_GITHUB-TOKEN') 
SIMILARITY_THRESHOLD = float(os.environ.get('INPUT_THRESHOLD', '0.70')) # INPUT_THRESHOLD (pas de trait d'union) est correct
LABEL_NAME_INPUT = os.environ.get('INPUT_DUPLICATE-LABEL') # Lire avec trait d'union

# Variables d'environnement GitHub standard
REPO_NAME = os.environ.get('GITHUB_REPOSITORY')
EVENT_PATH = os.environ.get('GITHUB_EVENT_PATH')
MODEL_NAME = 'all-MiniLM-L6-v2' # Modèle NLP

# Gérer la valeur par défaut pour le label si l'input n'est pas fourni
LABEL_NAME = LABEL_NAME_INPUT if LABEL_NAME_INPUT else 'potential-duplicate'

# --- Vérifications initiales ---
if not TOKEN:
    print("Erreur: INPUT_GITHUB-TOKEN est manquant.")
    exit(1)
if not REPO_NAME:
    print("Erreur: Variable GITHUB_REPOSITORY manquante.")
    exit(1)
if not EVENT_PATH:
    print("Erreur: Variable GITHUB_EVENT_PATH manquante.")
    exit(1)

# --- Récupérer le numéro de l'issue ---
try:
    with open(EVENT_PATH, 'r') as f:
        event_payload = json.load(f)
        # Vérifier que la clé 'issue' et 'number' existent
        if 'issue' in event_payload and 'number' in event_payload['issue']:
             ISSUE_NUMBER = event_payload['issue']['number']
        else:
             print(f"Erreur: Structure inattendue dans GITHUB_EVENT_PATH. 'issue' ou 'number' manquant.")
             exit(1)
except (FileNotFoundError, KeyError, json.JSONDecodeError, TypeError) as e:
    print(f"Erreur lors de la lecture du numéro de l'issue depuis GITHUB_EVENT_PATH : {e}")
    exit(1)

print(f"Analyse de l'issue #{ISSUE_NUMBER} dans {REPO_NAME}...")

# --- 1. CONNEXION ET RÉCUPÉRATION DES ISSUES ---
try:
    auth = Auth.Token(TOKEN)
    g = Github(auth=auth)
    repo = g.get_repo(REPO_NAME)
    new_issue = repo.get_issue(number=ISSUE_NUMBER)
    # S'assurer que title et body sont des chaînes, même si None
    new_issue_text = f"{new_issue.title or ''} {new_issue.body or ''}" 
except Exception as e:
    print(f"Impossible de récupérer l'issue ou le dépôt : {e}")
    exit(1)

corpus = [] # Liste pour stocker le texte des anciennes issues
corpus_issues = [] # Liste pour stocker les objets Issue correspondants
print("Récupération des autres issues ouvertes...")
try:
    # Utiliser paginated list pour gérer potentiellement beaucoup d'issues
    issues_paginated_list = repo.get_issues(state='open')
    for issue in issues_paginated_list:
        # Ignorer la nouvelle issue et les Pull Requests (qui apparaissent comme des issues)
        if issue.number != ISSUE_NUMBER and not issue.pull_request: 
            corpus.append(f"{issue.title or ''} {issue.body or ''}")
            corpus_issues.append(issue)
except Exception as e:
    print(f"Erreur lors de la récupération des issues existantes : {e}")
    # On peut choisir de continuer ou d'arrêter, ici on arrête
    exit(1)


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
try:
    # Convertir le texte des anciennes issues en vecteurs numériques
    corpus_embeddings = model.encode(corpus, show_progress_bar=False)
    # Convertir le texte de la nouvelle issue en vecteur
    query_embedding = model.encode([new_issue_text], show_progress_bar=False)
except Exception as e:
    print(f"Erreur lors de la vectorisation du texte : {e}")
    exit(1)


# --- 3. COMPARAISON MATHÉMATIQUE ---
print("Calcul de la similarité cosinus...")
try:
    # Calculer la similarité entre la nouvelle issue et TOUTES les anciennes
    # S'assurer que les embeddings ne sont pas vides
    if query_embedding.shape[0] > 0 and corpus_embeddings.shape[0] > 0:
        cosine_scores = cosine_similarity(query_embedding, corpus_embeddings)[0] # On prend le premier (et seul) élément

        # Trouver le score le plus élevé et l'index correspondant
        best_match_index = np.argmax(cosine_scores)
        best_match_score = cosine_scores[best_match_index]
        
        print(f"Meilleur score de similarité : {best_match_score * 100:.2f}%")
    else:
        print("Erreur: Impossible de calculer la similarité, embeddings vides.")
        best_match_score = 0 # Pas de correspondance trouvée

except Exception as e:
     print(f"Erreur lors du calcul de la similarité : {e}")
     best_match_score = 0 # Considérer comme échec

# --- 4. DÉCISION ET ACTION ---
if best_match_score >= SIMILARITY_THRESHOLD:
    # S'assurer que l'index est valide
    if best_match_index < len(corpus_issues):
        duplicate_issue = corpus_issues[best_match_index] # Récupérer l'objet Issue correspondant

        print(f"DUPLICATA POTENTIEL TROUVÉ ! Similaire à l'issue #{duplicate_issue.number}")

        # Préparer le commentaire
        comment_body = f"""🤖 Bonjour @{new_issue.user.login} ! Merci pour votre rapport.

Mon analyse suggère que cette issue ressemble beaucoup à une issue existante.

🎯 **Issue similaire trouvée :** [{duplicate_issue.title or 'Sans titre'} (#{duplicate_issue.number})]({duplicate_issue.html_url}) (Score de similarité : {best_match_score * 100:.2f}%)

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
        print("Erreur interne : Index de correspondance invalide.")
else:
    print("Aucun duplicata clair trouvé (score sous le seuil). Fin.")
